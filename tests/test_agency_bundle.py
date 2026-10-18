"""Test the actual generated upload package, not just its source references."""
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class AgencyBundleTests(unittest.TestCase):
    def test_ready_upload_and_demo_are_reproducibly_built(self):
        result = subprocess.run([sys.executable, str(ROOT / 'scripts/build-agency-bundle.py'), '--check'],
                                cwd=ROOT, capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        kit = ROOT / 'starter/chatgpt/agency'
        self.assertTrue((kit / 'AGENCY_PLAYBOOK.md').is_file())
        self.assertTrue((kit / 'SAMPLE_WORK.md').is_file())

    def test_upload_playbook_excludes_other_clients_and_retains_all_six_methods_and_license(self):
        kit = ROOT / 'starter/chatgpt/agency'
        playbook = (kit / 'AGENCY_PLAYBOOK.md').read_text()
        self.assertNotIn('SKIN-DEMO', playbook)
        self.assertNotIn('DEMO-SKIN-001', playbook)
        self.assertNotIn('### Copy SK-01', playbook)
        for name in ('AGENT_ROLES.md', 'WORKFLOW.md'):
            self.assertIn((kit / name).read_text().rstrip(), playbook)
        for skill in ('01-brand-positioning', '02-product-positioning', '03-social-operating-system',
                      '04-content-pillar-design', '05-performance-review', '06-linkedin-operator-pack'):
            self.assertIn('## Skill: ' + skill, playbook)
        self.assertIn((kit / 'UPSTREAM_LICENSE.txt').read_text().strip(), playbook)
        sample = (kit / 'SAMPLE_WORK.md').read_text()
        self.assertIn('DEMO-SKIN-001', sample)
        self.assertIn('不要與真實客戶檔案一起上傳', sample)

    def test_all_upload_methods_use_the_same_task_index_and_human_approval_states(self):
        kit = ROOT / 'starter/chatgpt/agency'
        for name in ('SKILL_PACK.md', 'AGENCY_PLAYBOOK.md'):
            text = (kit / name).read_text()
            self.assertNotIn('CurrentVersions', text, name)
            self.assertNotIn('IN_REVIEW', text, name)
            self.assertIn('TASK_BOARD', text, name)
            self.assertIn('READY_FOR_REVIEW', text, name)
            self.assertIn('HUMAN_APPROVED', text, name)
        self.assertIn('CURRENT_RULES', (kit / 'SKILL_PACK.md').read_text())

    def isolated_repository(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        root = Path(directory.name).resolve() / 'source'
        shutil.copytree(ROOT, root, ignore=shutil.ignore_patterns('.git', '.venv', '__pycache__'))
        return root

    def compile(self, root, flag):
        return subprocess.run([sys.executable, str(root / 'scripts/build-agency-bundle.py'), flag],
                              cwd=root, capture_output=True, text=True, timeout=30)

    def test_stale_check_is_read_only_and_explicit_rebuild_restores_exact_bytes(self):
        root = self.isolated_repository()
        target = root / 'starter/chatgpt/agency/AGENCY_PLAYBOOK.md'
        target.write_text('STALE synthetic fixture\n')
        result = self.compile(root, '--check')
        self.assertEqual(result.returncode, 1)
        self.assertEqual(target.read_text(), 'STALE synthetic fixture\n')
        self.assertEqual(self.compile(root, '--write').returncode, 0)
        self.assertEqual(target.read_bytes(), (ROOT / 'starter/chatgpt/agency/AGENCY_PLAYBOOK.md').read_bytes())
        self.assertEqual(self.compile(root, '--check').returncode, 0)

    def test_source_and_output_symlinks_reject_before_any_generated_write(self):
        root = self.isolated_repository()
        kit = root / 'starter/chatgpt/agency'
        playbook = kit / 'AGENCY_PLAYBOOK.md'
        playbook.write_text('preserve existing generated fixture\n')
        outside = root.parent / 'outside.md'
        outside.write_text('synthetic outside fixture\n')
        sample = kit / 'SAMPLE_WORK.md'
        sample.unlink()
        sample.symlink_to(outside)
        self.assertEqual(self.compile(root, '--write').returncode, 1)
        self.assertEqual(playbook.read_text(), 'preserve existing generated fixture\n')
        self.assertEqual(outside.read_text(), 'synthetic outside fixture\n')
        sample.unlink()
        source = kit / 'AGENT_ROLES.md'
        source.unlink()
        source.symlink_to(outside)
        self.assertEqual(self.compile(root, '--write').returncode, 1)
        self.assertEqual(playbook.read_text(), 'preserve existing generated fixture\n')
        self.assertFalse(sample.exists())


if __name__ == '__main__':
    unittest.main()
