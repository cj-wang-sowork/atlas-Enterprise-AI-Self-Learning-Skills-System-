"""Exercise the real shell entry point; never write to a real runtime home."""
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


REPO = Path(__file__).resolve().parents[1]
MODULES = (
    "learn_system", "market_router", "security_checker", "hermes_adapter",
    "market_intelligence",
)
SLUG = "atlas-enterprise-ai-self-learning"


class InstallerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="atlas-installer-", dir=os.environ.get("TMPDIR"))
        self.addCleanup(self.temp.cleanup)
        # macOS often exposes the temporary root via /var -> /private/var.
        # Use its canonical spelling; the installer intentionally rejects symlinks.
        self.root = Path(self.temp.name).resolve()
        self.source = self.root / "source"
        shutil.copytree(REPO, self.source, ignore=shutil.ignore_patterns(
            ".git", "__pycache__", ".pytest_cache", "*.pyc"))
        self.home = self.root / "home"
        self.home.mkdir()
        self.env = dict(os.environ, HOME=str(self.home), HERMES_HOME=str(self.home / ".hermes"),
                        PYTHONPATH="", PYTHONDONTWRITEBYTECODE="1")
        self.project = self.root / "project with spaces"

    def run_installer(self, *args):
        return subprocess.run(["sh", str(self.source / "scripts/install-workspace.sh"), *args],
                              env=self.env, cwd=self.root, capture_output=True, text=True)

    def assert_installs(self, *args):
        result = self.run_installer(*args)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return result

    def assert_modules(self, bundle):
        self.assertTrue((bundle / "SECURITY.md").is_file())
        self.assertTrue((bundle / "starter/chatgpt/README.md").is_file())
        modules: list[str] = list(MODULES)
        if (self.source / "skill_registry.py").exists():
            modules.append("skill_registry")
        for name in modules:
            self.assertTrue((bundle / (name + ".py")).is_file(), str(bundle / name))
        result = subprocess.run([sys.executable, "-c", "; ".join("import " + name for name in modules)],
                                cwd=bundle, env=self.env, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_shell_targets_install_complete_importable_bundles(self):
        for target in ("openclaw", "claude", "codex", "qwen", "hermes", "all"):
            with self.subTest(target=target):
                dest = self.root / (target + " destination")
                self.assert_installs("--target", target, "--dest", str(dest))
                if target in ("claude", "codex", "all"):
                    self.assert_modules(dest / ".atlas-workspace")
                    if target in ("claude", "all"):
                        self.assert_modules(dest / ".claude/skills" / SLUG / "templates/workspace")
                    launcher = "CLAUDE.md" if target == "claude" else "AGENTS.md"
                    self.assertIn(".atlas-workspace/", (dest / launcher).read_text())
                    if target == "all":
                        self.assertTrue((dest / "CLAUDE.md").is_file())
                        self.assert_modules(self.home / ".openclaw/workspace")
                        self.assert_modules(self.home / ".qwen/skills" / SLUG / "templates/workspace")
                        self.assert_modules(self.home / ".hermes/skills/openclaw-imports/openclaw-workspace-sowork/templates/workspace")
                elif target in ("qwen", "hermes"):
                    self.assertTrue((dest / "SKILL.md").is_file())
                    self.assert_modules(dest / "templates/workspace")
                else:
                    self.assert_modules(dest)

    def test_repeated_installs_preserve_distinct_backups_without_launcher_refusal(self):
        # Fixed date reproduces same-second backup collisions in the old shell code.
        fakebin = self.root / "bin"
        fakebin.mkdir()
        date = fakebin / "date"
        date.write_text("#!/bin/sh\nprintf '20261017-120000\\n'\n")
        date.chmod(0o755)
        self.env["PATH"] = str(fakebin) + os.pathsep + self.env["PATH"]
        for target, filename in (("openclaw", "MEMORY.md"), ("claude", "CLAUDE.md"),
                                 ("codex", "AGENTS.md"), ("qwen", "SKILL.md"),
                                 ("hermes", "SKILL.md"), ("all", "AGENTS.md")):
            with self.subTest(target=target):
                dest = self.root / target
                self.assert_installs("--target", target, "--dest", str(dest))
                for index in range(3):
                    (dest / filename).write_text("custom " + str(index))
                    self.assert_installs("--target", target, "--dest", str(dest))
                backups = list(dest.glob(filename + ".bak.*"))
                self.assertEqual(len(backups), 3)
                self.assertEqual({p.read_text() for p in backups}, {"custom 0", "custom 1", "custom 2"})

    def test_all_preflights_every_destination_before_any_write(self):
        # The last runtime is blocked; earlier OpenClaw/project/Qwen must be untouched.
        blocked = self.home / ".hermes"
        blocked.write_text("not a directory")
        result = self.run_installer("--target", "all", "--dest", str(self.project))
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((self.home / ".openclaw").exists(), result.stdout)
        self.assertFalse(self.project.exists(), result.stdout)
        self.assertFalse((self.home / ".qwen").exists(), result.stdout)
        self.assertEqual(blocked.read_text(), "not a directory")

    def test_symlinks_are_rejected_without_touching_their_targets(self):
        outside = self.root / "outside"
        outside.mkdir()
        marker = outside / "MEMORY.md"
        marker.write_text("keep private")
        for kind in ("root", "parent", "file", "dangling", "nested"):
            for force in (False, True):
                with self.subTest(kind=kind, force=force):
                    case = self.root / (kind + str(force))
                    case.mkdir()
                    dest = case / "install"
                    if kind == "root":
                        dest.symlink_to(outside, target_is_directory=True)
                    elif kind == "parent":
                        (case / "alias").symlink_to(outside, target_is_directory=True)
                        dest = case / "alias/install"
                    else:
                        dest.mkdir()
                        if kind == "nested":
                            (dest / "docs").mkdir()
                            (dest / "docs/shortcut").symlink_to(outside)
                        else:
                            (dest / "MEMORY.md").symlink_to(marker if kind == "file" else outside / "missing")
                    args = ["--target", "openclaw", "--dest", str(dest)] + (["--force"] if force else [])
                    result = self.run_installer(*args)
                    self.assertNotEqual(result.returncode, 0, result.stdout)
                    self.assertFalse((dest / "AGENTS.md").exists())
                    self.assertEqual(marker.read_text(), "keep private")
                    self.assertFalse((outside / "install").exists())

    def test_source_symlink_fails_before_writing(self):
        (self.source / "docs/shortcut").symlink_to(self.home)
        result = self.run_installer("--target", "all", "--dest", str(self.project))
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((self.home / ".openclaw").exists())
        self.assertFalse(self.project.exists())

    def test_malformed_arguments_do_not_write(self):
        cases = [(), ("--target",), ("--target", "unknown"),
                 ("--target", "openclaw", "--dest"),
                 ("--target", "openclaw", "--dest", ""),
                 ("--target", "openclaw", "--target", "qwen"),
                 ("--target", "openclaw", "--dest", str(self.project), "--dest", str(self.project)),
                 ("--target", "openclaw", "--force", "--force"),
                 ("--target", "openclaw", "--dest", "--force"),
                 ("--target", "claude"), ("--target", "codex"), ("--target", "all"),
                 ("--target", "openclaw", "--typo")]
        for args in cases:
            with self.subTest(args=args):
                result = self.run_installer(*args)
                self.assertNotEqual(result.returncode, 0)
                self.assertFalse(self.project.exists())
                self.assertEqual(list(self.home.iterdir()), [])

    def test_source_overlap_and_all_destination_overlap_are_rejected(self):
        for destination in (self.source, self.source / "nested", self.root):
            with self.subTest(destination=destination):
                result = self.run_installer("--target", "openclaw", "--dest", str(destination))
                self.assertNotEqual(result.returncode, 0)
        result = self.run_installer("--target", "all", "--dest", str(self.home / ".openclaw/workspace"))
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((self.home / ".openclaw").exists())

    def test_chatgpt_export_is_manual_text_only_and_repeatable(self):
        dest = self.root / "manual kit"
        self.assert_installs("--target", "chatgpt", "--dest", str(dest))
        core = {"README.md", "PROJECT_INSTRUCTIONS.md", "SAMPLE_BRIEF.md", "OUTCOME_REVIEW_LOG.md"}
        required = {p.name for p in (self.source / "starter/chatgpt").iterdir()
                    if p.suffix in (".md", ".json") and not p.name.startswith(".")}
        self.assertTrue(core <= required)
        self.assertEqual({p.name for p in dest.iterdir()}, required)
        self.assertTrue(all(p.suffix in (".md", ".json") for p in dest.iterdir()))
        for name in required:
            self.assertEqual((dest / name).read_bytes(),
                             (self.source / "starter/chatgpt" / name).read_bytes())
        self.assertFalse(list(dest.rglob("*.py")))
        instructions = (dest / "PROJECT_INSTRUCTIONS.md").read_text()
        self.assertIn("not access control", instructions)
        self.assertIn("manual", instructions.lower())
        self.assertIn("fictional", (dest / "SAMPLE_BRIEF.md").read_text().lower())
        self.assertIn("Reject", (dest / "OUTCOME_REVIEW_LOG.md").read_text())
        self.assertIn("manual", (dest / "README.md").read_text().lower())
        (dest / "SAMPLE_BRIEF.md").write_text("reviewed local brief")
        self.assert_installs("--target", "chatgpt", "--dest", str(dest))
        self.assertEqual(next(dest.glob("SAMPLE_BRIEF.md.bak.*")).read_text(), "reviewed local brief")
        self.assertEqual(list(self.home.iterdir()), [])
        result = self.run_installer("--target", "chatgpt")
        self.assertNotEqual(result.returncode, 0)

    def test_hermes_honors_explicit_profile_home(self):
        profile = self.home / "chosen-profile"
        self.env["HERMES_HOME"] = str(profile)
        self.assert_installs("--target", "hermes")
        self.assert_modules(profile / "skills/openclaw-imports/openclaw-workspace-sowork/templates/workspace")
        self.assertFalse((self.home / ".hermes").exists())

    def test_default_destinations_stay_in_sandbox(self):
        for target, destination in (
            ("openclaw", self.home / ".openclaw/workspace"),
            ("qwen", self.home / ".qwen/skills" / SLUG),
            ("hermes", self.home / ".hermes/skills/openclaw-imports/openclaw-workspace-sowork"),
        ):
            with self.subTest(target=target):
                self.assert_installs("--target", target)
                self.assertTrue((destination / "SKILL.md").is_file())

    def test_force_replaces_managed_items_without_new_backups(self):
        for target, filename in (("openclaw", "MEMORY.md"), ("claude", "CLAUDE.md"),
                                 ("codex", "AGENTS.md"), ("qwen", "SKILL.md"),
                                 ("hermes", "SKILL.md"), ("all", "AGENTS.md"),
                                 ("chatgpt", "SAMPLE_BRIEF.md")):
            with self.subTest(target=target):
                dest = self.root / ("force-" + target)
                dest.mkdir()
                marker = dest / "unmanaged.txt"
                marker.write_text("keep this")
                (dest / filename).write_text("custom instruction")
                existing_backup = dest / (filename + ".bak.preexisting")
                existing_backup.write_text("keep older backup")
                other_launcher = dest / ("AGENTS.md" if target == "claude" else "CLAUDE.md")
                if target in ("claude", "codex"):
                    other_launcher.write_text("another runtime owns this")
                self.assert_installs("--target", target, "--dest", str(dest), "--force")
                self.assertNotEqual((dest / filename).read_text(), "custom instruction")
                self.assertEqual(list(dest.glob(filename + ".bak.*")), [existing_backup])
                self.assertEqual(existing_backup.read_text(), "keep older backup")
                if target in ("claude", "codex"):
                    self.assertEqual(other_launcher.read_text(), "another runtime owns this")
                self.assertEqual(marker.read_text(), "keep this")

    def test_missing_runtime_source_fails_all_without_writing(self):
        for name in ('learn_system.py', 'skill_registry.py'):
            with self.subTest(module=name):
                module = self.source / name
                saved = module.with_suffix('.py.saved')
                module.rename(saved)
                try:
                    result = self.run_installer("--target", "all", "--dest", str(self.project))
                    self.assertNotEqual(result.returncode, 0)
                    self.assertFalse(self.project.exists())
                    self.assertEqual(list(self.home.iterdir()), [])
                finally:
                    saved.rename(module)

    def test_new_registry_module_is_copied_when_present(self):
        # A test-only module proves future top-level modules are not omitted.
        registry = self.source / "skill_registry.py"
        if not registry.exists():
            registry.write_text('"""Installer fixture module, not a backend implementation."""\n')
        self.assert_installs("--target", "hermes", "--dest", str(self.project))
        self.assertEqual((self.project / "templates/workspace/skill_registry.py").read_bytes(), registry.read_bytes())
        self.assert_modules(self.project / "templates/workspace")

    def test_chatgpt_rejects_symlinked_source_parent(self):
        external = self.root / "external-starter"
        shutil.move(str(self.source / "starter"), external)
        (self.source / "starter").symlink_to(external, target_is_directory=True)
        result = self.run_installer("--target", "chatgpt", "--dest", str(self.project))
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(self.project.exists())

    def test_all_preflights_launcher_symlink_before_openclaw_write(self):
        self.project.mkdir()
        (self.project / "CLAUDE.md").symlink_to(self.home / "missing")
        result = self.run_installer("--target", "all", "--dest", str(self.project))
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(list(self.home.iterdir()), [])
        self.assertTrue((self.project / "CLAUDE.md").is_symlink())

    def test_all_preflights_bundle_and_pack_directory_conflicts(self):
        conflicts = [self.project / ".atlas-workspace",
                     self.project / ".claude/skills" / SLUG / "references",
                     self.home / ".qwen/skills" / SLUG / "templates/workspace",
                     self.home / ".hermes/skills/openclaw-imports/openclaw-workspace-sowork/assets"]
        for conflict in conflicts:
            with self.subTest(conflict=conflict):
                conflict.parent.mkdir(parents=True, exist_ok=True)
                conflict.write_text("not a directory")
                result = self.run_installer("--target", "all", "--dest", str(self.project))
                self.assertNotEqual(result.returncode, 0)
                self.assertFalse((self.home / ".openclaw").exists(), result.stdout)
                self.assertFalse((self.project / "CLAUDE.md").exists(), result.stdout)
                self.assertFalse((self.project / "AGENTS.md").exists(), result.stdout)
                self.assertEqual(conflict.read_text(), "not a directory")
                conflict.unlink()

    def test_wrong_source_shapes_fail_before_any_install(self):
        for relative in ("SKILL.md", "docs", "learn_system.py", "starter/chatgpt/SAMPLE_BRIEF.md"):
            with self.subTest(relative=relative):
                source = self.source / relative
                saved = source.with_name(source.name + ".saved")
                source.rename(saved)
                try:
                    if saved.is_dir():
                        source.write_text("not a directory")
                    else:
                        source.mkdir()
                    target = "chatgpt" if relative.startswith("starter/") else "all"
                    result = self.run_installer("--target", target, "--dest", str(self.project))
                    self.assertNotEqual(result.returncode, 0)
                    self.assertFalse(self.project.exists())
                    self.assertEqual(list(self.home.iterdir()), [])
                finally:
                    if source.is_dir():
                        source.rmdir()
                    else:
                        source.unlink()
                    saved.rename(source)


if __name__ == "__main__":
    unittest.main()
