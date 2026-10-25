"""Offline contracts for the canonical adaptive team and portable exports."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
import zipfile

ROOT = Path(__file__).resolve().parents[1]
CORE = ROOT / 'team_core'
SCRIPT = ROOT / 'scripts/build-marketing-team.py'


def load_builder():
    spec = importlib.util.spec_from_file_location('marketing_builder', SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class CoreContracts(unittest.TestCase):
    def test_canonical_director_and_complete_bundled_methods(self):
        self.assertTrue((CORE / 'SKILL.md').is_file(), 'Canonical director is missing')
        skill = (CORE / 'SKILL.md').read_text()
        self.assertTrue(skill.startswith('---\nname: atlas-marketing-team\n'))
        for term in ('adaptive', 'workstream', 'Traditional Chinese', 'LIVE_SEARCH_UNAVAILABLE',
                     'DRAFT', 'unpublished', 'capability', 'discovery'):
            self.assertIn(term, skill)
        methods = (CORE / 'resources/bundled-methods.md').read_text()
        original = (ROOT / 'starter/chatgpt/agency/SKILL_PACK.md').read_text()
        start = original.index('## Skill: 01-brand-positioning\n')
        end = original.index('\n# 一句需求的首輪實作\n')
        self.assertIn(original[start:end].rstrip(), methods)
        self.assertEqual(methods.count('## Skill: '), 6)
        for forbidden in ('SKIN-DEMO', 'CB-SK', 'Copy SK-01', '## 五角色 → 六技能矩陣'):
            self.assertNotIn(forbidden, methods)
        self.assertEqual((CORE / 'licenses/UPSTREAM_LICENSE.txt').read_bytes(),
                         (ROOT / 'starter/chatgpt/agency/UPSTREAM_LICENSE.txt').read_bytes())
        self.assertEqual((CORE / 'licenses/UPSTREAM_PROVENANCE.json').read_bytes(),
                         (ROOT / 'starter/chatgpt/agency/UPSTREAM_PROVENANCE.json').read_bytes())

    def test_referenced_resources_enforce_discovery_safety_and_handoff(self):
        expected = {
            'resources/orchestration.md': ('skip', 'workstream', 'not a fixed'),
            'resources/discovery.md': ('README', 'commit', 'license', 'environment',
                                        'generic', 'untrusted', 'stars', 'LIVE_SEARCH_UNAVAILABLE'),
            'resources/capabilities.md': ('news-sowork', 'election-pwa', 'unresolved', 'not connected'),
            'resources/safety.md': ('credential', 'ad spend', 'human', 'untrusted', 'privacy'),
            'resources/output-reference.md': ('outcome', 'methods', 'sources', 'DRAFT', 'QA'),
            'templates/CLIENT_CONTEXT.md': ('Unknown', 'Version', 'Authorized'),
            'templates/DELIVERY.md': ('Outcome', 'Method', 'Source', 'unpublished'),
            'SETUP.md': ('Customize > Skills', 'Create skill', 'Upload a skill',
                         'Code execution', 'plugin.json', 'permissions', 'not permanent', 'PENDING'),
            'PROVENANCE.md': ('a230b7f6f5ed987fefbb8f4933c411681701c8ed', 'MIT', 'manual'),
        }
        for path, terms in expected.items():
            with self.subTest(path=path):
                self.assertTrue((CORE / path).is_file(), 'Missing resource: ' + path)
                text = (CORE / path).read_text()
                for term in terms:
                    self.assertIn(term, text)
        self.assertTrue((CORE / 'catalog.json').is_file(), 'Missing catalog')
        catalog = json.loads((CORE / 'catalog.json').read_text())
        self.assertEqual(catalog['status'], 'discovery-hints-only')
        self.assertEqual({s['repository'] for s in catalog['seeds']},
                         {'coreyhaines31/marketingskills', 'msitarzewski/agency-agents'})
        self.assertTrue(all(s['requires_live_revalidation'] for s in catalog['seeds']))

    def test_operator_documentation_explains_all_exports_and_limits(self):
        path = ROOT / 'docs/MARKETING_TEAM.md'
        self.assertTrue(path.is_file(), 'Operator documentation is missing')
        text = path.read_text()
        for target in ('claude', 'chatgpt-plugin', 'chatgpt-project'):
            self.assertIn('scripts/build-marketing-team.py --target ' + target, text)
        for term in ('--check', 'Python 3.9', 'outside', 'symlink', 'PENDING',
                     'LIVE_SEARCH_UNAVAILABLE', 'SOURCE_MANIFEST.json', 'unpublished',
                     'not a permanent', 'one model', 'manual'):
            self.assertIn(term, text)


class BundleContracts(unittest.TestCase):
    def test_check_validates_source_closure_without_writing(self):
        self.assertTrue(SCRIPT.is_file(), 'Exporter is missing')
        builder = load_builder()
        with tempfile.TemporaryDirectory(dir=ROOT.parent.resolve()) as temporary:
            root = Path(temporary) / 'source'
            shutil.copytree(CORE, root / 'team_core')
            result = subprocess.run([sys.executable, str(SCRIPT), '--check'],
                                    capture_output=True, text=True)
            # A concurrent package can still be incomplete: check must fail closed.
            missing = [p for p in builder.SOURCE_PATHS if not (ROOT / p).is_file()]
            if missing:
                self.assertNotEqual(result.returncode, 0)
                self.assertIn('Required source', result.stderr)
            else:
                self.assertEqual(result.returncode, 0, result.stderr)
                manifest = json.loads(result.stdout)
                self.assertEqual(manifest['schema_version'], 1)
                records = manifest['sources']
                self.assertEqual({r['path'] for r in records}, set(builder.SOURCE_PATHS))
                for record in records:
                    data = (ROOT / record['path']).read_bytes()
                    self.assertEqual(record['sha256'], hashlib.sha256(data).hexdigest())
                    self.assertEqual(record['bytes'], len(data))
            before = sorted(str(p.relative_to(root)) for p in root.rglob('*'))
            with self.assertRaisesRegex(ValueError, 'Required source'):
                builder.source_manifest(root)
            self.assertEqual(before, sorted(str(p.relative_to(root)) for p in root.rglob('*')))

    def test_claude_zip_is_deterministic_and_preserves_sources(self):
        builder = load_builder()
        self.assertTrue(hasattr(builder, 'build_archive'), 'ZIP build path is missing')
        missing = [p for p in builder.SOURCE_PATHS if not (ROOT / p).is_file()]
        if missing:
            self.skipTest('Sibling package pending: ' + ', '.join(missing))
        with tempfile.TemporaryDirectory(dir=ROOT.parent.resolve()) as temporary:
            dest = Path(temporary).resolve() / 'claude.zip'
            second = dest.with_name('repeat.zip')
            builder.build_archive('claude', dest, ROOT)
            builder.build_archive('claude', second, ROOT)
            self.assertEqual(dest.read_bytes(), second.read_bytes())
            with zipfile.ZipFile(dest) as archive:
                names = archive.namelist()
                self.assertEqual(names, sorted(names))
                self.assertEqual({p.split('/')[0] for p in names}, {'atlas-marketing-team'})
                for source in builder.SOURCE_PATHS:
                    target = source.removeprefix('team_core/')
                    self.assertEqual(archive.read('atlas-marketing-team/' + target),
                                     (ROOT / source).read_bytes())
                manifest = json.loads(archive.read('atlas-marketing-team/SOURCE_MANIFEST.json'))
                self.assertEqual(manifest, builder.source_manifest(ROOT))
                self.assertTrue(all(i.date_time == (1980, 1, 1, 0, 0, 0)
                                    for i in archive.infolist()))
            extracted = dest.parent / 'extracted'
            with zipfile.ZipFile(dest) as archive:
                archive.extractall(extracted)
            result = subprocess.run([sys.executable, '-m', 'marketing_team', 'plan',
                                     '--task', 'content calendar'], capture_output=True, text=True,
                                    cwd=extracted / 'atlas-marketing-team', env={'PATH': os.environ['PATH']})
            self.assertEqual(result.returncode, 0, result.stderr)
            plan = json.loads(result.stdout)
            self.assertEqual(plan['status'], 'PLANNED')
            self.assertEqual(plan['domains'], ['social'])
            self.assertEqual(plan['methods'], ['03-social-operating-system', '04-content-pillar-design'])
            self.assertEqual(plan['roles'], ['social operator'])
            self.assertEqual(plan['workflow'][0]['domain'], 'social')

    def test_plugin_zip_uses_portable_skills_only_manifest(self):
        builder = load_builder()
        with tempfile.TemporaryDirectory(dir=ROOT.parent.resolve()) as temporary:
            dest = Path(temporary).resolve() / 'plugin.zip'
            builder.build_archive('chatgpt-plugin', dest, ROOT)
            with zipfile.ZipFile(dest) as archive:
                manifest = json.loads(archive.read('plugin.json'))
                self.assertEqual(manifest['$schema'],
                                 'https://agent-plugins.org/schemas/1.0.0/plugin.schema.json')
                self.assertEqual(manifest['name'], 'atlas-marketing-team')
                self.assertLessEqual(set(manifest), {'$schema', 'name', 'version', 'description',
                                                     'author', 'homepage', 'repository', 'license',
                                                     'keywords', 'extensions'})
                self.assertNotIn('mcp', json.dumps(manifest).lower())
                for source in builder.SOURCE_PATHS:
                    target = 'skills/atlas-marketing-team/' + source.removeprefix('team_core/')
                    self.assertEqual(archive.read(target), (ROOT / source).read_bytes())
                self.assertEqual(json.loads(archive.read('skills/atlas-marketing-team/SOURCE_MANIFEST.json')),
                                 builder.source_manifest(ROOT))
                self.assertFalse(any('mcp' in n.lower() or n.endswith('.env') for n in archive.namelist()))
            second = dest.with_name('repeat.zip')
            builder.build_archive('chatgpt-plugin', second, ROOT)
            self.assertEqual(dest.read_bytes(), second.read_bytes())

    def test_project_compiles_same_director_methods_and_not_fake_plugin(self):
        builder = load_builder()
        with tempfile.TemporaryDirectory(dir=ROOT.parent.resolve()) as temporary:
            dest = Path(temporary).resolve() / 'project.zip'
            builder.build_archive('chatgpt-project', dest, ROOT)
            with zipfile.ZipFile(dest) as archive:
                names = set(archive.namelist())
                self.assertTrue({'PROJECT_INSTRUCTIONS.md', 'PLAYBOOK.md', 'CLIENT_CONTEXT.md',
                                 'SETUP.md', 'PROVENANCE.md', 'SOURCE_MANIFEST.json'} <= names)
                self.assertFalse(any(n.endswith('.py') or n.endswith('SKILL.md') or n == 'plugin.json'
                                     for n in names))
                playbook = archive.read('PLAYBOOK.md')
                for source in builder.CORE_PATHS:
                    if source.startswith(('licenses/', 'templates/')) or source in ('SETUP.md', 'PROVENANCE.md'):
                        continue
                    self.assertIn((CORE / source).read_bytes().rstrip(b'\n'), playbook)
                self.assertIn(b'not a native plugin', archive.read('PROJECT_INSTRUCTIONS.md'))
                self.assertEqual(archive.read('CLIENT_CONTEXT.md'),
                                 (CORE / 'templates/CLIENT_CONTEXT.md').read_bytes())
                self.assertEqual(archive.read('licenses/UPSTREAM_LICENSE.txt'),
                                 (CORE / 'licenses/UPSTREAM_LICENSE.txt').read_bytes())
                self.assertEqual(json.loads(archive.read('SOURCE_MANIFEST.json')),
                                 builder.source_manifest(ROOT))
                self.assertNotIn(b'SKIN-DEMO', playbook)
                self.assertEqual(playbook.count(b'## Skill: '), 6)
            repeat = dest.with_name('repeat.zip')
            builder.build_archive('chatgpt-project', repeat, ROOT)
            self.assertEqual(dest.read_bytes(), repeat.read_bytes())

    def test_unsafe_destinations_refused_before_any_output_write(self):
        builder = load_builder()
        with tempfile.TemporaryDirectory(dir=ROOT.parent.resolve()) as temporary:
            directory = Path(temporary).resolve()
            root = directory / 'repository'
            shutil.copytree(CORE, root / 'team_core')
            shutil.copytree(ROOT / 'marketing_team', root / 'marketing_team',
                            ignore=shutil.ignore_patterns('__pycache__'))
            existing = directory / 'existing.zip'
            existing.write_bytes(b'keep original')
            linked = directory / 'linked'
            linked.symlink_to(directory, target_is_directory=True)
            dangling = directory / 'dangling.zip'
            dangling.symlink_to(directory / 'absent')
            (directory / 'safe').mkdir()
            cases = [root / 'inside.zip', existing, linked / 'out.zip', dangling,
                     directory / 'missing-parent/out.zip', directory / 'safe/../traversal.zip',
                     directory / 'not-a-zip.txt']
            for destination in cases:
                with self.subTest(destination=destination):
                    with mock.patch.object(builder.tempfile, 'NamedTemporaryFile',
                                           wraps=tempfile.NamedTemporaryFile) as writer:
                        with self.assertRaises((ValueError, OSError)):
                            builder.build_archive('claude', destination, root)
                        writer.assert_not_called()
            self.assertEqual(existing.read_bytes(), b'keep original')
            self.assertFalse((root / 'inside.zip').exists())
            self.assertFalse((directory / 'out.zip').exists())

    def test_source_symlink_ancestors_and_unbundled_imports_fail_closed(self):
        builder = load_builder()
        with tempfile.TemporaryDirectory(dir=ROOT.parent.resolve()) as temporary:
            directory = Path(temporary).resolve()
            root = directory / 'repository'
            shutil.copytree(CORE, root / 'team_core')
            shutil.copytree(ROOT / 'marketing_team', root / 'marketing_team',
                            ignore=shutil.ignore_patterns('__pycache__'))
            alias = directory / 'alias'
            alias.symlink_to(directory, target_is_directory=True)
            destination = directory / 'must-not-exist.zip'
            with mock.patch.object(builder.tempfile, 'NamedTemporaryFile', wraps=tempfile.NamedTemporaryFile) as writer:
                with self.assertRaisesRegex(ValueError, 'symlink'):
                    builder.build_archive('claude', destination, alias / 'repository')
                writer.assert_not_called()
            module = root / 'marketing_team/__main__.py'
            module.write_text(module.read_text() + '\nfrom marketing_team.private import secret\n')
            with mock.patch.object(builder.tempfile, 'NamedTemporaryFile', wraps=tempfile.NamedTemporaryFile) as writer:
                with self.assertRaisesRegex(ValueError, 'import outside source allowlist'):
                    builder.build_archive('claude', destination, root)
                writer.assert_not_called()
            self.assertFalse(destination.exists())

    def test_invalid_canonical_catalog_rejected_before_write(self):
        builder = load_builder()
        with tempfile.TemporaryDirectory(dir=ROOT.parent.resolve()) as temporary:
            directory = Path(temporary).resolve()
            root = directory / 'repository'
            shutil.copytree(CORE, root / 'team_core')
            shutil.copytree(ROOT / 'marketing_team', root / 'marketing_team',
                            ignore=shutil.ignore_patterns('__pycache__'))
            (root / 'team_core/catalog.json').write_text('{broken')
            destination = directory / 'out.zip'
            with mock.patch.object(builder.tempfile, 'NamedTemporaryFile', wraps=tempfile.NamedTemporaryFile) as writer:
                with self.assertRaises(ValueError):
                    builder.build_archive('claude', destination, root)
                writer.assert_not_called()
            self.assertFalse(destination.exists())

    def test_fixed_allowlist_excludes_extra_client_files_and_cache(self):
        builder = load_builder()
        with tempfile.TemporaryDirectory(dir=ROOT.parent.resolve()) as temporary:
            directory = Path(temporary).resolve()
            root = directory / 'repository'
            shutil.copytree(CORE, root / 'team_core')
            shutil.copytree(ROOT / 'marketing_team', root / 'marketing_team',
                            ignore=shutil.ignore_patterns('__pycache__'))
            for name in ('team_core/.env', 'team_core/client-notes.md',
                         'marketing_team/session.log', 'marketing_team/private.py'):
                (root / name).write_text('PRIVATE_SENTINEL_DO_NOT_PACKAGE')
            destination = directory / 'safe.zip'
            builder.build_archive('claude', destination, root)
            with zipfile.ZipFile(destination) as archive:
                expected = {'atlas-marketing-team/' + p.removeprefix('team_core/')
                            for p in builder.SOURCE_PATHS}
                expected.add('atlas-marketing-team/SOURCE_MANIFEST.json')
                self.assertEqual(set(archive.namelist()), expected)
                self.assertTrue(all(b'PRIVATE_SENTINEL_DO_NOT_PACKAGE' not in archive.read(n)
                                    for n in archive.namelist()))

    def test_missing_or_symlinked_required_source_prevents_output(self):
        builder = load_builder()
        with tempfile.TemporaryDirectory(dir=ROOT.parent.resolve()) as temporary:
            directory = Path(temporary).resolve()
            root = directory / 'repository'
            shutil.copytree(CORE, root / 'team_core')
            shutil.copytree(ROOT / 'marketing_team', root / 'marketing_team',
                            ignore=shutil.ignore_patterns('__pycache__'))
            source = root / 'team_core/SKILL.md'
            source.unlink()
            destination = directory / 'safe.zip'
            for state in ('missing', 'symlink'):
                with self.subTest(state=state):
                    if state == 'symlink':
                        source.symlink_to(CORE / 'SKILL.md')
                    with mock.patch.object(builder.tempfile, 'NamedTemporaryFile', wraps=tempfile.NamedTemporaryFile) as writer:
                        with self.assertRaises(ValueError):
                            builder.build_archive('claude', destination, root)
                        writer.assert_not_called()
                    self.assertFalse(destination.exists())

    def test_atomic_commit_race_preserves_existing_file_and_cleans_temp(self):
        builder = load_builder()
        with tempfile.TemporaryDirectory(dir=ROOT.parent.resolve()) as temporary:
            directory = Path(temporary).resolve()
            destination = directory / 'raced.zip'
            def concurrent_create(source, target):
                Path(target).write_bytes(b'concurrent writer owns this')
                raise FileExistsError('race')
            with mock.patch.object(builder.os, 'link', side_effect=concurrent_create):
                with self.assertRaises(FileExistsError):
                    builder.build_archive('claude', destination, ROOT)
            self.assertEqual(destination.read_bytes(), b'concurrent writer owns this')
            self.assertEqual(set(directory.iterdir()), {destination})


if __name__ == '__main__':
    unittest.main()
