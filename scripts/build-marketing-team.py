#!/usr/bin/env python3
"""Export one canonical marketing team; stdlib-only, offline and read-only by default."""
import argparse
import ast
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import sys
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
CORE_PATHS = (
    'SKILL.md', 'SETUP.md', 'PROVENANCE.md', 'catalog.json',
    'resources/orchestration.md', 'resources/discovery.md',
    'resources/capabilities.md', 'resources/safety.md',
    'resources/output-reference.md', 'resources/bundled-methods.md',
    'templates/CLIENT_CONTEXT.md', 'templates/DELIVERY.md',
    'licenses/ATLAS_LICENSE.txt', 'licenses/UPSTREAM_LICENSE.txt',
    'licenses/UPSTREAM_PROVENANCE.json',
)
PACKAGE_PATHS = (
    'marketing_team/__init__.py', 'marketing_team/__main__.py',
    'marketing_team/planner.py', 'marketing_team/discovery.py', 'marketing_team/github.py',
    'marketing_team/metadata.py', 'marketing_team/inspection.py',
)
SOURCE_PATHS = tuple('team_core/' + path for path in CORE_PATHS) + PACKAGE_PATHS


def stable_json(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode('utf-8')


def read_sources(root):
    root = Path(root).absolute()
    for ancestor in (root,) + tuple(root.parents):
        if ancestor.is_symlink():
            raise ValueError('Source symlink ancestor: ' + str(ancestor))
    sources = {}
    for relative in SOURCE_PATHS:
        name = PurePosixPath(relative)
        if name.is_absolute() or '..' in name.parts:
            raise ValueError('Unsafe source path: ' + relative)
        current = root
        if current.is_symlink():
            raise ValueError('Source symlink: ' + str(current))
        for component in name.parts:
            current = current / component
            if current.is_symlink():
                raise ValueError('Source symlink: ' + relative)
        if not current.is_file():
            raise ValueError('Required source is missing or not a file: ' + relative)
        sources[relative] = current.read_bytes()
    for relative, data in sources.items():
        if relative.endswith('.json'):
            json.loads(data.decode('utf-8'))
    # Validate package import closure without importing or executing its code.
    for relative in PACKAGE_PATHS:
        tree = ast.parse(sources[relative].decode('utf-8'), filename=relative)
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.level:
                if node.level != 1 or not node.module:
                    raise ValueError('Unsupported package import: ' + relative)
                target = 'marketing_team/' + node.module.replace('.', '/') + '.py'
                if target not in sources:
                    raise ValueError('Package import outside source allowlist: ' + target)
            if (isinstance(node, ast.ImportFrom) and not node.level
                    and node.module and node.module.startswith('marketing_team.')):
                target = node.module.replace('.', '/') + '.py'
                if target not in sources:
                    raise ValueError('Package import outside source allowlist: ' + target)
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.startswith('marketing_team.'):
                        target = alias.name.replace('.', '/') + '.py'
                        if target not in sources:
                            raise ValueError('Package import outside source allowlist: ' + target)
    return sources


def manifest_for(sources):
    records = [{'path': path, 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}
               for path, data in sorted(sources.items())]
    return {'schema_version': 1,
            'source_digest': hashlib.sha256(stable_json(records)).hexdigest(),
            'sources': records}


def source_manifest(root=ROOT):
    return manifest_for(read_sources(root))


def archive_entries(target, sources):
    if target == 'chatgpt-project':
        instructions = (
            '# Project instructions\n\n'
            'Use PLAYBOOK.md as the canonical adaptive marketing director and method guide.\n'
            'This is a manual text workflow, not a native plugin or an automatic installer.\n'
            'Use only visible authorized CLIENT_CONTEXT.md inputs; keep versions manual.\n'
            'Capability-check each new need; reuse bundled methods for supported small edits.\n'
            'Discover safe public methods for gaps, fresh evidence or explicit research, using\n'
            'generic category searches or mark LIVE_SEARCH_UNAVAILABLE, then deliver the real\n'
            'requested output before optional onboarding. Select relevant workstreams,\n'
            'apply reviewed methods, cite sources/versions and QA. Bundled methods are\n'
            'available offline. Outputs remain DRAFT — unpublished. No account access,\n'
            'automatic self-learning, code execution or publishing is provided here.\n'
            'Reply in the user language including Traditional Chinese.\n'
        )
        sections = [b'# Canonical marketing playbook\n\n'
                    b'Resource paths below identify compiled source sections, not extra uploads.\n'
                    b'The local Python helper is not included in this text-only fallback.\n']
        for path in CORE_PATHS:
            if path.startswith('licenses/') or path in ('SETUP.md', 'PROVENANCE.md',
                                                       'templates/CLIENT_CONTEXT.md'):
                continue
            sections.append(('\n\n---\n\n# Source: team_core/' + path + '\n\n').encode('utf-8')
                            + sources['team_core/' + path])
        entries = {'PROJECT_INSTRUCTIONS.md': instructions.encode('utf-8'),
                   'PLAYBOOK.md': b''.join(sections),
                   'CLIENT_CONTEXT.md': sources['team_core/templates/CLIENT_CONTEXT.md'],
                   'SETUP.md': sources['team_core/SETUP.md'],
                   'PROVENANCE.md': sources['team_core/PROVENANCE.md'],
                   'SOURCE_MANIFEST.json': stable_json(manifest_for(sources))}
        entries.update({path: sources['team_core/' + path]
                        for path in CORE_PATHS if path.startswith('licenses/')})
        return entries
    if target not in ('claude', 'chatgpt-plugin'):
        raise ValueError('Unknown target: ' + target)
    prefix = ('atlas-marketing-team/' if target == 'claude' else 'skills/atlas-marketing-team/')
    entries = {prefix + path.removeprefix('team_core/'): data
               for path, data in sources.items()}
    entries[prefix + 'SOURCE_MANIFEST.json'] = stable_json(manifest_for(sources))
    if target == 'chatgpt-plugin':
        entries['plugin.json'] = stable_json({
            '$schema': 'https://agent-plugins.org/schemas/1.0.0/plugin.schema.json',
            'name': 'atlas-marketing-team',
            'version': '0.2.0',
            'description': 'Adaptive marketing workstreams with reviewed public methods.',
            'license': 'MIT',
            'keywords': ['marketing', 'research', 'content', 'skills'],
        })
    return entries


def validate_destination(destination, root):
    destination = Path(destination)
    if not destination.is_absolute() or '..' in destination.parts or destination.suffix != '.zip':
        raise ValueError('Destination must be an absolute .zip path without traversal')
    for ancestor in (destination,) + tuple(destination.parents):
        if ancestor.is_symlink():
            raise ValueError('Destination symlink/ancestor is not allowed: ' + str(ancestor))
    if destination.is_relative_to(Path(root).resolve()):
        raise ValueError('Destination must be outside the repository')
    if destination.exists():
        raise ValueError('Destination exists; choose a separate intentional path')
    if not destination.parent.is_dir():
        raise ValueError('Destination parent must already exist')
    return destination


def build_archive(target, destination, root=ROOT):
    # Read/validate all sources before any output file or directory is touched.
    sources = read_sources(root)
    entries = archive_entries(target, sources)
    destination = validate_destination(destination, root)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(prefix='.marketing-team-', suffix='.zip',
                                         dir=destination.parent, delete=False) as stream:
            temporary = Path(stream.name)
            with zipfile.ZipFile(stream, 'w', compression=zipfile.ZIP_STORED) as archive:
                for name, data in sorted(entries.items()):
                    info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
                    info.create_system = 3
                    info.external_attr = 0o100644 << 16
                    info.compress_type = zipfile.ZIP_STORED
                    archive.writestr(info, data)
            stream.flush()
            os.fsync(stream.fileno())
        # Hard link atomically creates the exact destination, never overwriting it.
        os.link(str(temporary), str(destination))
    finally:
        if temporary is not None:
            temporary.unlink()
    return manifest_for(sources)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='Read-only source closure and manifest check.')
    parser.add_argument('--target', choices=['claude', 'chatgpt-plugin', 'chatgpt-project'])
    parser.add_argument('--dest', type=Path)
    args = parser.parse_args(argv)
    if args.check and (args.target or args.dest):
        parser.error('--check is read-only; do not combine with --target or --dest')
    if not args.check and bool(args.target) != bool(args.dest):
        parser.error('--target and --dest must be supplied together')
    try:
        manifest = (build_archive(args.target, args.dest) if args.target else source_manifest())
        print(stable_json(manifest).decode('utf-8'), end='')
        return 0
    except (ValueError, OSError, UnicodeError, SyntaxError) as error:
        print(str(error), file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
