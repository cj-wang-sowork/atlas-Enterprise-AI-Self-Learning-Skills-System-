#!/usr/bin/env sh
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
REPO_ROOT=$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)
TARGET=""
DEST=""
FORCE=0
HERMES_ROOT=${HERMES_HOME:-"$HOME/.hermes"}

usage() {
  cat <<'EOF'
Usage:
  ./scripts/install-workspace.sh --target openclaw [--dest PATH] [--force]
  ./scripts/install-workspace.sh --target claude --dest PATH [--force]
  ./scripts/install-workspace.sh --target codex --dest PATH [--force]
  ./scripts/install-workspace.sh --target qwen [--dest PATH] [--force]
  ./scripts/install-workspace.sh --target hermes [--dest PATH] [--force]
  ./scripts/install-workspace.sh --target all --dest PATH [--force]
  ./scripts/install-workspace.sh --target chatgpt --dest PATH [--force]

Targets:
  openclaw  Install the workspace files into ~/.openclaw/workspace by default
  claude    Install a CLAUDE.md launcher, .atlas-workspace/, and .claude/skills/ into a Claude Code project root (requires --dest)
  codex     Install an AGENTS.md launcher plus .atlas-workspace/ into a Codex CLI project root (requires --dest)
  qwen      Install a Qwen skill pack into ~/.qwen/skills/atlas-enterprise-ai-self-learning by default
  hermes    Install a Hermes skill pack into ~/.hermes/skills/openclaw-imports/openclaw-workspace-sowork by default (honors HERMES_HOME)
  all       Install openclaw + claude + codex + qwen + hermes (requires --dest for Claude/Codex; excludes ChatGPT)
  chatgpt   Export only manual Project starter text files (requires --dest); no ChatGPT login or execution

Options:
  --target TARGET   One of: openclaw, claude, codex, qwen, hermes, all, chatgpt
  --dest PATH       Destination path (required for claude/codex/all/chatgpt, optional otherwise)
  --force           Overwrite existing files instead of creating timestamped backups
  -h, --help        Show this help message
EOF
}

log() {
  printf '%s\n' "$*"
}

fail() {
  printf 'Error: %s\n' "$*" >&2
  exit 1
}

normalize_path() {
  python3 - "$1" <<'PY'
import os
import sys
print(os.path.realpath(os.path.expanduser(sys.argv[1])))
PY
}

ensure_safe_destination() {
  candidate=$(normalize_path "$1")
  source_root=$(normalize_path "$REPO_ROOT")

  case "$candidate" in
    "$source_root"|"$source_root"/*)
      fail "Destination $candidate overlaps the source repository $source_root. Choose a different --dest outside the cloned repo."
      ;;
  esac
}

backup_or_remove() {
  path=$1
  if [ ! -e "$path" ]; then
    return 0
  fi

  if [ "$FORCE" -eq 1 ]; then
    rm -rf "$path"
    return 0
  fi

  stamp=$(python3 -c 'from datetime import datetime; import uuid; print(datetime.now().strftime("%Y%m%d-%H%M%S-%f") + "-" + uuid.uuid4().hex)')
  [ ! -e "$path.bak.$stamp" ] && [ ! -L "$path.bak.$stamp" ] || fail "Backup already exists"
  mv "$path" "$path.bak.$stamp"
  log "Backed up existing $(basename "$path") -> $path.bak.$stamp"
}

copy_item() {
  src=$1
  dest_dir=$2
  [ -e "$src" ] || return 0
  base=$(basename "$src")
  mkdir -p "$dest_dir"
  backup_or_remove "$dest_dir/$base"
  cp -R "$src" "$dest_dir/$base"
}

copy_workspace_bundle() {
  bundle_dest=$1
  mkdir -p "$bundle_dest"

  for item in \
    AGENTS.md \
    HEARTBEAT.md \
    IDENTITY.md \
    MEMORY.md \
    README.md \
    SKILL.md \
    SOUL.md \
    TOOLS.md \
    USER.md \
    CONTRIBUTING.md \
    LICENSE \
    SECURITY.md \
    starter \
    docs \
    examples \
    memory \
    outputs \
    scripts \
    skills
  do
    copy_item "$REPO_ROOT/$item" "$bundle_dest"
  done
  for module in "$REPO_ROOT"/*.py; do
    copy_item "$module" "$bundle_dest"
  done
}

copy_skill_pack() {
  skill_dest=$1
  mkdir -p "$skill_dest/references" "$skill_dest/templates/workspace" "$skill_dest/assets"

  backup_or_remove "$skill_dest/SKILL.md"
  cp "$REPO_ROOT/SKILL.md" "$skill_dest/SKILL.md"

  for item in README.md docs/INSTALLATION.md docs/METHODOLOGY.md docs/LEARN.md docs/workspace-deep-dive.md docs/CHATGPT_STARTER.md docs/ACCESS_CONTROL.md docs/LEARNING_LIFECYCLE.md docs/VERIFICATION.md; do
    src="$REPO_ROOT/$item"
    [ -e "$src" ] || continue
    dest_name=$(basename "$item")
    backup_or_remove "$skill_dest/references/$dest_name"
    cp "$src" "$skill_dest/references/$dest_name"
  done

  copy_workspace_bundle "$skill_dest/templates/workspace"

  backup_or_remove "$skill_dest/assets/skills"
  cp -R "$REPO_ROOT/skills" "$skill_dest/assets/skills"
}

write_project_launcher() {
  launcher_root=$1
  runtime_name=$2
  launcher_path="$launcher_root/AGENTS.md"
  if [ "$runtime_name" = "Claude Code" ]; then
    launcher_path="$launcher_root/CLAUDE.md"
  fi
  backup_or_remove "$launcher_path"
  cat > "$launcher_path" <<'EOF'
# ATLAS runtime bootstrap

At the start of each session, load and follow these workspace files:

- `./.atlas-workspace/AGENTS.md`
- `./.atlas-workspace/SOUL.md`
- `./.atlas-workspace/TOOLS.md`
- `./.atlas-workspace/USER.md`
- `./.atlas-workspace/IDENTITY.md`
- `./.atlas-workspace/HEARTBEAT.md`
- `./.atlas-workspace/MEMORY.md` for direct owner sessions only

Use the reusable skill prompts from `./.atlas-workspace/skills/` when the task matches.
Read `./.atlas-workspace/docs/METHODOLOGY.md` when architecture or learning policy matters.
Treat `./.atlas-workspace/` as agent context, not application source code, unless the user explicitly asks you to edit it.
Prompt instructions are not access enforcement. Optional Python modules are not automatically run or connected by this installer.
Do not claim successful backend access, learning, or external actions without execution evidence.
EOF
  log "$runtime_name launcher written -> $launcher_path"
}

install_openclaw() {
  openclaw_dest=${1:-"$HOME/.openclaw/workspace"}
  ensure_safe_destination "$openclaw_dest"
  log "Installing OpenClaw workspace -> $openclaw_dest"
  copy_workspace_bundle "$openclaw_dest"
  log "OpenClaw install complete."
}

install_claude() {
  project_root=$1
  [ -n "$project_root" ] || fail "Claude target requires --dest /path/to/project"
  ensure_safe_destination "$project_root"
  mkdir -p "$project_root"

  claude_workspace="$project_root/.atlas-workspace"
  log "Installing Claude Code workspace context -> $claude_workspace"
  copy_workspace_bundle "$claude_workspace"
  copy_skill_pack "$project_root/.claude/skills/atlas-enterprise-ai-self-learning"
  write_project_launcher "$project_root" "Claude Code"
  log "Claude context installed: CLAUDE.md, ./.atlas-workspace/, and ./.claude/skills/. Verify discovery in Claude Code."
}

install_codex() {
  project_root=$1
  [ -n "$project_root" ] || fail "Codex target requires --dest /path/to/project"
  ensure_safe_destination "$project_root"
  mkdir -p "$project_root"

  codex_workspace="$project_root/.atlas-workspace"
  log "Installing Codex CLI workspace context -> $codex_workspace"
  copy_workspace_bundle "$codex_workspace"
  write_project_launcher "$project_root" "Codex CLI"
  log "Codex install complete. Start Codex from $project_root so it discovers AGENTS.md."
}

install_qwen() {
  qwen_dest=${1:-"$HOME/.qwen/skills/atlas-enterprise-ai-self-learning"}
  ensure_safe_destination "$qwen_dest"
  log "Installing Qwen skill pack -> $qwen_dest"
  copy_skill_pack "$qwen_dest"
  log "Qwen context installed. Check the skill list in your installed Qwen Code version."
}

install_hermes() {
  hermes_dest=${1:-"$HERMES_ROOT/skills/openclaw-imports/openclaw-workspace-sowork"}
  ensure_safe_destination "$hermes_dest"
  log "Installing Hermes skill pack -> $hermes_dest"
  copy_skill_pack "$hermes_dest"
  log "Hermes context installed. Inspect discovery with hermes skills list, then load the name shown by your runtime."
}

while [ $# -gt 0 ]; do
  case "$1" in
    --target)
      [ $# -ge 2 ] || fail "--target requires a value"
      [ -z "$TARGET" ] || fail "--target may be given only once"
      [ -n "$2" ] || fail "--target requires a nonempty value"
      case "$2" in -*) fail "--target requires a value, not an option" ;; esac
      TARGET=$2
      shift 2
      ;;
    --dest)
      [ $# -ge 2 ] || fail "--dest requires a value"
      [ -z "$DEST" ] || fail "--dest may be given only once"
      [ -n "$2" ] || fail "--dest requires a nonempty value"
      case "$2" in -*) fail "--dest requires a path, not an option" ;; esac
      DEST=$2
      shift 2
      ;;
    --force)
      [ "$FORCE" -eq 0 ] || fail "--force may be given only once"
      FORCE=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      fail "Unknown argument: $1"
      ;;
  esac
done

[ -n "$TARGET" ] || {
  usage
  fail "--target is required"
}

command -v python3 >/dev/null 2>&1 || fail "python3 is required for path normalization"

# Check every destination before any install, especially --target all.
preflight() {
  python3 - "$REPO_ROOT" "$TARGET" "$@" <<'PY'
import os
from pathlib import Path
import sys
source = Path(sys.argv[1]).resolve()
target = sys.argv[2]
roots = [Path(os.path.abspath(os.path.expanduser(value))) for value in sys.argv[3:]]
workspace = "AGENTS.md HEARTBEAT.md IDENTITY.md MEMORY.md README.md SKILL.md SOUL.md TOOLS.md USER.md CONTRIBUTING.md LICENSE SECURITY.md starter docs examples memory outputs scripts skills".split()
modules = [p.name for p in source.glob("*.py")]
required_modules = "learn_system.py market_router.py security_checker.py hermes_adapter.py skill_registry.py market_intelligence.py".split()

def fail(message):
    sys.exit("Error: " + message)

def overlaps(a, b):
    return a == b or a in b.parents or b in a.parents

def check_tree(path):
    if path.is_symlink():
        fail("Symlink is not allowed in managed paths: " + str(path))
    if not path.exists():
        return
    if not path.is_file() and not path.is_dir():
        fail("Unsupported filesystem item: " + str(path))
    if path.is_dir():
        for directory, dirs, files in os.walk(path, followlinks=False):
            for name in dirs + files:
                child = Path(directory) / name
                if child.is_symlink() or not (child.is_file() or child.is_dir()):
                    fail("Symlink or special file in managed tree: " + str(child))

# Verify source payloads before touching any runtime home.
source_items = ["starter/chatgpt/" + name for name in ("README.md", "PROJECT_INSTRUCTIONS.md", "SAMPLE_BRIEF.md", "OUTCOME_REVIEW_LOG.md")] if target == "chatgpt" else workspace + modules + required_modules
for name in set(source_items):
    path = source / name
    for parent in path.parents:
        if parent == source:
            break
        if parent.is_symlink():
            fail("Symlink source component: " + str(parent))
    check_tree(path)
    if not path.exists():
        fail("Required source is missing: " + str(path))
    expected_directory = name in {"docs", "examples", "memory", "outputs", "scripts", "skills", "starter"}
    if (expected_directory and not path.is_dir()) or (not expected_directory and not path.is_file()):
        fail("Required source has the wrong file/directory type: " + str(path))

for index, destination in enumerate(roots):
    if overlaps(destination, source):
        fail("Destination overlaps source repository: " + str(destination))
    if any(overlaps(destination, other) for other in roots[index + 1:]):
        fail("Install destinations overlap: " + str(destination))
    for ancestor in (destination, *destination.parents):
        if ancestor.is_symlink():
            fail("Symlink destination component: " + str(ancestor))
        if ancestor.exists() and not ancestor.is_dir():
            fail("Destination parent is not a directory: " + str(ancestor))
    runtime = ("openclaw", "project", "qwen", "hermes")[index] if target == "all" else target
    if runtime == "chatgpt":
        managed = [destination / Path(name).name for name in source_items]
    elif runtime == "openclaw":
        managed = [destination / name for name in workspace + modules]
    elif runtime in ("claude", "codex", "project"):
        managed = [destination / ".atlas-workspace"]
        if runtime in ("claude", "project"):
            managed += [destination / "CLAUDE.md", destination / ".claude/skills/atlas-enterprise-ai-self-learning"]
        if runtime in ("codex", "project"):
            managed += [destination / "AGENTS.md"]
    else:
        managed = [destination / name for name in ("SKILL.md", "references", "templates/workspace", "assets/skills")]
    required_dirs = []
    if runtime in ("claude", "codex", "project"):
        required_dirs.append(destination / ".atlas-workspace")
    if runtime in ("claude", "project", "qwen", "hermes"):
        pack = destination / ".claude/skills/atlas-enterprise-ai-self-learning" if runtime in ("claude", "project") else destination
        required_dirs += [pack / name for name in ("references", "templates/workspace", "assets")]
    for directory in required_dirs:
        for component in (directory, *directory.parents):
            if component.is_symlink():
                fail("Symlink destination component: " + str(component))
            if component.exists() and not component.is_dir():
                fail("Required destination directory is a file: " + str(component))
    for path in managed:
        for ancestor in path.parents:
            if ancestor.is_symlink():
                fail("Symlink destination component: " + str(ancestor))
            if ancestor.exists() and not ancestor.is_dir():
                fail("Destination parent is not a directory: " + str(ancestor))
        check_tree(path)
PY
}

case "$TARGET" in
  all)
    [ -n "$DEST" ] || fail "--target all requires --dest"
    preflight "$HOME/.openclaw/workspace" "$DEST" "$HOME/.qwen/skills/atlas-enterprise-ai-self-learning" "$HERMES_ROOT/skills/openclaw-imports/openclaw-workspace-sowork"
    ;;
  claude|codex|chatgpt)
    [ -n "$DEST" ] || fail "$TARGET requires --dest"
    preflight "$DEST"
    ;;
  openclaw) preflight "${DEST:-$HOME/.openclaw/workspace}" ;;
  qwen) preflight "${DEST:-$HOME/.qwen/skills/atlas-enterprise-ai-self-learning}" ;;
  hermes) preflight "${DEST:-$HERMES_ROOT/skills/openclaw-imports/openclaw-workspace-sowork}" ;;
esac

[ -z "$DEST" ] || DEST=$(normalize_path "$DEST")
HERMES_ROOT=$(normalize_path "$HERMES_ROOT")

case "$TARGET" in
  chatgpt)
    mkdir -p "$DEST"
    for item in README.md PROJECT_INSTRUCTIONS.md SAMPLE_BRIEF.md OUTCOME_REVIEW_LOG.md; do
      copy_item "$REPO_ROOT/starter/chatgpt/$item" "$DEST"
    done
    log "Exported manual ChatGPT Starter Kit -> $DEST"
    log "Open README.md; upload/copy manually. No ChatGPT configuration or backend code was executed."
    ;;
  openclaw)
    install_openclaw "$DEST"
    ;;
  claude)
    install_claude "$DEST"
    ;;
  codex)
    install_codex "$DEST"
    ;;
  qwen)
    install_qwen "$DEST"
    ;;
  hermes)
    install_hermes "$DEST"
    ;;
  all)
    [ -n "$DEST" ] || fail "--target all requires --dest for the Claude/Codex project"
    install_openclaw
    install_claude "$DEST"
    write_project_launcher "$DEST" "Codex CLI"
    log "Codex CLI support enabled through $DEST/AGENTS.md and $DEST/.atlas-workspace."
    install_qwen
    install_hermes
    ;;
  *)
    fail "Unsupported target: $TARGET"
    ;;
esac
