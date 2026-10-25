"""Tool-disabled Codex CLI transport; never reads or exposes auth material."""
import json
import os
from pathlib import Path
import selectors
import shutil
import signal
import subprocess
import tempfile
import time


_CAPTURE_LIMIT = 1000000


def _cleanup_group(process):
    """Give launchers a short chance to reap children, then kill the session group."""
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        pass
    try:
        process.wait(timeout=0.25)
    except subprocess.TimeoutExpired:
        pass
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    process.wait()


def _bounded_transport(args, input, text, capture_output, cwd, env, timeout):
    """POSIX-only, shared byte budget; never use communicate's unbounded capture."""
    if os.name != 'posix':
        raise GenerationError('UNSUPPORTED_PLATFORM')
    deadline = time.monotonic() + timeout
    try:
        pending = memoryview(input.encode('utf-8'))
    except UnicodeEncodeError:
        raise GenerationError('INVALID_PROMPT') from None
    buffers = {'stdout': bytearray(), 'stderr': bytearray()}
    total = 0
    process = subprocess.Popen(args, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, cwd=cwd, env=env,
                               start_new_session=True)
    try:
        with selectors.DefaultSelector() as selector:
            for stream, name in ((process.stdout, 'stdout'), (process.stderr, 'stderr')):
                os.set_blocking(stream.fileno(), False)
                selector.register(stream, selectors.EVENT_READ, name)
            os.set_blocking(process.stdin.fileno(), False)
            if pending:
                selector.register(process.stdin, selectors.EVENT_WRITE, 'stdin')
            else:
                process.stdin.close()
            while selector.get_map():
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise subprocess.TimeoutExpired(args, timeout)
                for key, _ in selector.select(remaining):
                    stream, name = key.fileobj, key.data
                    if name == 'stdin':
                        try:
                            pending = pending[os.write(stream.fileno(), pending[:65536]):]
                        except BrokenPipeError:
                            pending = pending[len(pending):]
                        except BlockingIOError:
                            continue
                        if not pending:
                            selector.unregister(stream)
                            stream.close()
                        continue
                    try:
                        chunk = os.read(stream.fileno(), min(65536, _CAPTURE_LIMIT - total + 1))
                    except BlockingIOError:
                        continue
                    if not chunk:
                        selector.unregister(stream)
                        stream.close()
                        continue
                    total += len(chunk)
                    if total > _CAPTURE_LIMIT:
                        raise GenerationError('OUTPUT_TOO_LARGE')
                    buffers[name].extend(chunk)
            process.wait(timeout=max(0, deadline - time.monotonic()))
        try:
            stdout = buffers['stdout'].decode('utf-8')
        except UnicodeDecodeError:
            raise GenerationError('INVALID_MODEL_PROTOCOL') from None
        stderr = buffers['stderr'].decode('utf-8', errors='replace')
        return subprocess.CompletedProcess(args, process.returncode, stdout, stderr)
    finally:
        _cleanup_group(process)
        for stream in (process.stdin, process.stdout, process.stderr):
            if stream is not None:
                stream.close()


class GenerationError(Exception):
    """Only fixed public codes may cross the HTTP boundary."""
    def __init__(self, code):
        self.code = code
        super().__init__(code)


class CodexRunner:
    def __init__(self, binary=None, model=None, scratch=None, transport=None):
        self.binary = binary or os.environ.get('ATLAS_CODEX_BIN') or shutil.which('codex')
        self.model = model or os.environ.get('ATLAS_CODEX_MODEL', 'gpt-6.1-sol')
        self.scratch = Path(scratch or os.environ.get('ATLAS_DEMO_SCRATCH') or
                            os.environ.get('TMPDIR') or Path.home() / '.hermes/cache/scratch')
        self.transport = transport or _bounded_transport

    def __call__(self, prompt, timeout=150):
        if not self.binary or not Path(self.binary).is_absolute():
            raise GenerationError('CODEX_UNAVAILABLE')
        args = [self.binary, 'exec', '--ignore-user-config', '--ignore-rules', '--ephemeral',
                '--skip-git-repo-check', '--sandbox', 'read-only', '--json', '-m', self.model,
                '-c', 'project_doc_max_bytes=0', '-c', 'web_search="disabled"',
                '-c', 'model_reasoning_effort="low"']
        for feature in ('shell_tool', 'browser_use', 'browser_use_external', 'computer_use',
                        'apps', 'plugins', 'hooks', 'image_generation', 'multi_agent'):
            args.extend(['--disable', feature])
        args.append('-')
        env = {key: os.environ[key] for key in ('HOME', 'PATH') if key in os.environ}
        try:
            self.scratch.mkdir(parents=True, exist_ok=True)
            with tempfile.TemporaryDirectory(prefix='atlas-generation-', dir=str(self.scratch)) as cwd:
                result = self.transport(args, input=prompt, text=True, capture_output=True,
                                        cwd=cwd, env=env, timeout=min(150, timeout))
        except subprocess.TimeoutExpired:
            raise GenerationError('MODEL_TIMEOUT') from None
        except OSError:
            raise GenerationError('CODEX_UNAVAILABLE') from None
        if result.returncode:
            # Detect common actionable failures, never expose stderr/provider payloads.
            error_text = (result.stderr + result.stdout).lower()
            if 'model' in error_text and any(word in error_text for word in ('not found', 'not supported', 'does not exist', 'unknown model', 'model_not_found')):
                raise GenerationError('MODEL_UNAVAILABLE')
            raise GenerationError('MODEL_FAILED')
        if len(result.stdout) > 1000000:
            raise GenerationError('OUTPUT_TOO_LARGE')
        try:
            events = [json.loads(line) for line in result.stdout.splitlines() if line.strip()]
            if not all(isinstance(event, dict) for event in events):
                raise ValueError()
            types = [event.get('type') for event in events]
            tool_types = {'command_execution', 'file_change', 'mcp_tool_call', 'web_search',
                          'collab_tool_call', 'image_generation', 'browser_tool_call'}
            if any(event.get('item', {}).get('type') in tool_types for event in events):
                raise GenerationError('UNEXPECTED_MODEL_TOOL')
            if ('thread.started' not in types or 'turn.started' not in types or
                    not types or types[-1] != 'turn.completed' or
                    any(t in types for t in ('turn.failed', 'error', 'thread.failed'))):
                raise GenerationError('MODEL_INCOMPLETE')
            messages = [event['item']['text'] for event in events
                        if event.get('type') == 'item.completed' and
                        event.get('item', {}).get('type') == 'agent_message']
            if not messages or not isinstance(messages[-1], str) or not messages[-1].strip():
                raise GenerationError('EMPTY_MODEL_OUTPUT')
            if len(messages[-1]) > 100000:
                raise GenerationError('OUTPUT_TOO_LARGE')
            return messages[-1]
        except (ValueError, KeyError, TypeError, AttributeError):
            raise GenerationError('INVALID_MODEL_PROTOCOL') from None
