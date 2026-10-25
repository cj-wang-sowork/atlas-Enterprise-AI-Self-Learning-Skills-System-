"""Launch-entry contracts; not evidence of native model quality."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class LaunchEntryTests(unittest.TestCase):
    def test_marketer_first_entry_has_a_single_honest_trial_route(self):
        text = (ROOT / 'README.md').read_text(encoding='utf-8')
        self.assertTrue(text.startswith('# ATLAS Marketing Team\n'))
        self.assertIn('docs/TRY_IN_CHATGPT.md', text)
        self.assertIn('python3 -m native_demo', text)
        self.assertIn('localhost-only', text)
        self.assertIn('not a production service', text)
        self.assertIn('one week of social content', text)
        primary = text.split('## Adaptive Marketing Team', 1)[0]
        self.assertNotIn('1000+', primary)
        self.assertNotIn('five-layer security', primary)

    def test_chat_trial_has_unpack_failure_and_no_installation_claim(self):
        path = ROOT / 'docs/TRY_IN_CHATGPT.md'
        self.assertTrue(path.is_file(), 'One-task trial guide is missing')
        text = ' '.join(path.read_text(encoding='utf-8').split())
        for term in ('PLAYBOOK.md', 'PROJECT_INSTRUCTIONS.md', 'cannot unpack',
                     'not permanent installation', 'DRAFT', '7 complete posts',
                     'Do not invent', 'consent'):
            self.assertIn(term, text)
        setup = (ROOT / 'team_core/SETUP.md').read_text(encoding='utf-8')
        self.assertIn('Ordinary-chat trial', setup)

    def test_new_preview_uses_a_distinct_plugin_version(self):
        import importlib.util
        import json
        spec = importlib.util.spec_from_file_location('launch_builder', ROOT / 'scripts/build-marketing-team.py')
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        manifest = json.loads(module.archive_entries('chatgpt-plugin', module.read_sources(ROOT))['plugin.json'])
        self.assertEqual(manifest['version'], '0.2.0')


if __name__ == '__main__':
    unittest.main()
