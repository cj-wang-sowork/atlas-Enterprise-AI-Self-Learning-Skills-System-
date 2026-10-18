"""Real installer entrypoint checks; fixtures are not customer or UI evidence."""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


REQUIRED = {
    'AGENCY_SETUP.md', 'PROJECT_INSTRUCTIONS.md', 'CLIENT_BRIEF.md',
    'AGENT_ROLES.md', 'WORKFLOW.md', 'TASK_BOARD.md', 'CURRENT_RULES.md',
    'REVIEW_LOG.md', 'SKILL_PACK.md', 'UPSTREAM_LICENSE.txt',
    'UPSTREAM_PROVENANCE.json', 'AGENCY_PLAYBOOK.md', 'SAMPLE_WORK.md',
}


class AgencyExportTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.source = self.root / 'source'
        shutil.copytree(Path(__file__).resolve().parents[1], self.source,
                        ignore=shutil.ignore_patterns('.git', '.venv', '__pycache__'))
        self.assets = self.source / 'starter' / 'chatgpt' / 'agency'
        self.assets.mkdir(exist_ok=True)
        for name in REQUIRED:
            (self.assets / name).write_text('Synthetic exporter fixture: ' + name + '\n')
        self.home = self.root / 'home'
        self.home.mkdir()
        self.destination = self.root / 'agency-export'
        self.env = dict(os.environ, HOME=str(self.home),
                        HERMES_HOME=str(self.root / 'unused-hermes'))

    def run_export(self, target='chatgpt-agency', shell=None):
        command = [str(self.source / 'scripts' / 'install-workspace.sh'),
                   '--target', target, '--dest', str(self.destination)]
        if shell:
            command.insert(0, shell)
        return subprocess.run(command, cwd=self.source, env=self.env,
                              capture_output=True, text=True, timeout=30)

    def test_agency_export_is_separate_complete_and_posix(self):
        shells = [None, shutil.which('sh')]
        self.assertIsNotNone(shells[1])
        if shutil.which('dash'):
            shells.append(shutil.which('dash'))
        for index, shell in enumerate(shells):
            with self.subTest(shell=shell or 'declared executable'):
                self.destination = self.root / ('agency-' + str(index))
                result = self.run_export(shell=shell)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual({p.name for p in self.destination.iterdir()}, REQUIRED)
                for name in REQUIRED:
                    self.assertEqual((self.destination / name).read_bytes(),
                                     (self.assets / name).read_bytes())
        self.assertFalse((self.home / '.hermes').exists())
        self.assertFalse((self.home / '.openclaw').exists())
    def test_missing_license_fails_before_existing_destination_changes(self):
        (self.assets / 'UPSTREAM_LICENSE.txt').unlink()
        self.destination.mkdir()
        sentinel = self.destination / 'CURRENT_RULES.md'
        sentinel.write_text('Existing synthetic user rules; preserve.\n')
        before = {p.name: p.read_bytes() for p in self.destination.iterdir()}
        result = self.run_export()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('Required source is missing', result.stderr)
        self.assertEqual({p.name: p.read_bytes() for p in self.destination.iterdir()}, before)

    def test_source_and_destination_symlinks_fail_without_writes(self):
        outside = self.root / 'outside.md'
        outside.write_text('Synthetic outside fixture.\n')
        source = self.assets / 'CLIENT_BRIEF.md'
        source.unlink()
        source.symlink_to(outside)
        result = self.run_export()
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(self.destination.exists())
        source.unlink()
        source.write_text('Synthetic restored brief.\n')
        self.destination.mkdir()
        (self.destination / 'CURRENT_RULES.md').symlink_to(outside)
        result = self.run_export()
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(outside.read_text(), 'Synthetic outside fixture.\n')
        self.assertEqual({p.name for p in self.destination.iterdir()}, {'CURRENT_RULES.md'})

    def test_inherited_bash_preferences_do_not_leak_hidden_or_unsupported_files(self):
        for name in ('.PRIVATE.md', 'UPPER.MD', 'RUNME.py'):
            (self.assets / name).write_text('Synthetic unsupported fixture.\n')
        preferences = self.root / 'prefs.sh'
        preferences.write_text("shopt -s dotglob nullglob failglob nocaseglob\nGLOBIGNORE='*/CLIENT_BRIEF.md'\nexport GLOBIGNORE\n")
        self.env['BASH_ENV'] = str(preferences)
        result = self.run_export(shell='bash')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual({p.name for p in self.destination.iterdir()}, REQUIRED)

    def test_generic_export_remains_the_original_eight_assets(self):
        before = {p.name: p.read_bytes() for p in self.assets.parent.iterdir()
                  if p.is_file() and p.suffix in ('.md', '.json') and not p.name.startswith('.')}
        self.assertEqual(len(before), 8)
        result = self.run_export(target='chatgpt')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual({p.name for p in self.destination.iterdir()}, set(before))
        for name, content in before.items():
            self.assertEqual((self.destination / name).read_bytes(), content)
        self.assertFalse((self.destination / 'AGENCY_SETUP.md').exists())


if __name__ == '__main__':
    unittest.main()
