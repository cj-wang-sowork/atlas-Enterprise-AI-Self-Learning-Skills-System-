"""Synthetic filesystem fixtures validate the real text-only exporter, not ChatGPT UI."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


class ChatGPTAssetExportTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.source = self.root / 'source'
        shutil.copytree(Path(__file__).resolve().parents[1], self.source,
                        ignore=shutil.ignore_patterns('.git', '.venv', '__pycache__'))
        self.assets = self.source / 'starter' / 'chatgpt'
        self.home = self.root / 'home'
        self.home.mkdir()
        self.destination = self.root / 'export'
        self.env = dict(os.environ, HOME=str(self.home),
                        HERMES_HOME=str(self.root / 'unused-hermes'))

    def export(self):
        return subprocess.run(['bash', str(self.source / 'scripts' / 'install-workspace.sh'),
                               '--target', 'chatgpt', '--dest', str(self.destination)],
                              cwd=self.source, env=self.env, capture_output=True, text=True,
                              timeout=30)

    def test_new_manual_cards_and_source_json_are_exported_byte_for_byte(self):
        (self.assets / 'FIRST_VALUE_TEST.md').write_text('Synthetic first-value card fixture.\n')
        (self.assets / 'PUBLIC_SOURCE_TEST.json').write_text(json.dumps({'fixture': True}))
        result = self.export()
        self.assertEqual(result.returncode, 0, result.stderr)
        expected = {p.name for p in self.assets.iterdir()
                    if p.suffix in ('.md', '.json') and not p.name.startswith('.')}
        self.assertEqual({p.name for p in self.destination.iterdir()}, expected)
        for name in expected:
            self.assertEqual((self.destination / name).read_bytes(), (self.assets / name).read_bytes())

    def test_new_asset_symlink_is_rejected_before_existing_destination_changes(self):
        target = self.root / 'outside-fixture.json'
        target.write_text('{"fixture": true}')
        (self.assets / 'UNSAFE_NEW_SOURCE.json').symlink_to(target)
        self.destination.mkdir()
        (self.destination / 'README.md').write_text('Preserve this existing fixture.\n')
        before = {p.name: p.read_bytes() for p in self.destination.iterdir()}
        result = self.export()
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual({p.name: p.read_bytes() for p in self.destination.iterdir()}, before)
        self.assertEqual(target.read_text(), '{"fixture": true}')

    def test_hidden_notes_and_executable_assets_are_never_exported(self):
        (self.assets / '.PRIVATE_TEST.md').write_text('Synthetic private fixture.')
        (self.assets / 'EXECUTABLE_TEST.py').write_text('raise RuntimeError("fixture only")')
        result = self.export()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse((self.destination / '.PRIVATE_TEST.md').exists())
        self.assertFalse((self.destination / 'EXECUTABLE_TEST.py').exists())
        self.assertTrue(all(p.suffix in ('.md', '.json') for p in self.destination.iterdir()))

    def test_new_asset_directory_fails_preflight_without_any_output(self):
        (self.assets / 'DIRECTORY_TEST.json').mkdir()
        result = self.export()
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(self.destination.exists())


if __name__ == '__main__':
    unittest.main()
