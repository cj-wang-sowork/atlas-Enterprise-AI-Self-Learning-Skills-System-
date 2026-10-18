"""Recorder tests are synthetic fixtures, not human usability-study results."""
from datetime import datetime, timezone, timedelta
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest


class UsabilityTests(unittest.TestCase):
    def recorder(self, path, **kwargs):
        try:
            from evaluation.usability import StudyLog
        except ImportError:
            self.fail('The durable usability recorder is missing')
        return StudyLog(path, **kwargs)

    def test_agent_sessions_never_count_as_human_participants(self):
        with TemporaryDirectory() as directory:
            log = self.recorder(Path(directory) / 'study.sqlite')
            log.start('agent-qa', kind='agent_qa', background='unknown', consent=True,
                      runtime='ChatGPT', starter_revision='fixture-revision')
            report = log.report()
            self.assertEqual(report['eligible_humans_started'], 0)
            self.assertIsNone(report['success_rate'])
            self.assertIsNone(report['median_success_seconds'])

    def test_human_start_requires_consent_and_observer_attestation(self):
        with TemporaryDirectory() as directory:
            log = self.recorder(Path(directory) / 'study.sqlite')
            for overrides in ({'consent': False}, {'attested': False}, {'observer': None}):
                arguments: dict = dict(kind='human', background='non_engineer', consent=True,
                                 runtime='ChatGPT', starter_revision='fixture-revision',
                                 observer='observer-1', attested=True)
                arguments.update(overrides)
                with self.subTest(overrides=overrides), self.assertRaises((ValueError, PermissionError)):
                    log.start('human-1', **arguments)
            self.assertEqual(log.report()['total_sessions'], 0)
            log.start('human-1', kind='human', background='non_engineer', consent=True,
                      runtime='ChatGPT', starter_revision='fixture-revision',
                      observer='observer-1', attested=True)
            report = log.report()
            self.assertEqual(report['eligible_humans_started'], 1)
            self.assertEqual(report['success_rate'], 0.0)
            self.assertIsNone(report['median_success_seconds'])

    def test_completed_human_fixture_is_timed_and_survives_restart(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / 'study.sqlite'
            tick = [datetime(2026, 10, 17, 8, tzinfo=timezone.utc)]
            log = self.recorder(path, clock=lambda: tick[0])
            session = log.start('fixture-human', kind='human', background='non_engineer',
                                consent=True, runtime='ChatGPT', starter_revision='fixture-revision',
                                observer='fixture-observer', attested=True)
            for name in ('download_kit', 'create_project', 'add_instructions', 'attach_brief',
                         'complete_first_task', 'save_result'):
                log.step(session, name, status='completed')
            tick[0] += timedelta(minutes=5)
            evidence = Path(directory) / 'fixture-output.txt'
            evidence.write_text('Fictional study fixture output, not a live ChatGPT response.')
            log.finish(session, outcome='success', evidence=evidence)
            report = self.recorder(path).report()
            self.assertEqual(report['eligible_humans_started'], 1)
            self.assertEqual(report['completed_successfully'], 1)
            self.assertEqual(report['completed_within_600_seconds'], 1)
            self.assertEqual(report['median_success_seconds'], 300)
            self.assertEqual(report['success_rate'], 1.0)

    def test_first_attempts_and_protocols_cannot_be_mixed(self):
        with TemporaryDirectory() as directory:
            log = self.recorder(Path(directory) / 'study.sqlite')
            arguments: dict = dict(kind='human', background='non_engineer', consent=True,
                             runtime='ChatGPT', starter_revision='fixture-revision',
                             observer='fixture-observer', attested=True)
            log.start('fixture-human', **arguments)
            for participant, overrides in [('fixture-human', {}), ('fixture-two', {'runtime': 'Claude'}),
                                           ('fixture-three', {'starter_revision': 'changed-revision'})]:
                with self.subTest(participant=participant), self.assertRaises(ValueError):
                    log.start(participant, **dict(arguments, **overrides))
            self.assertEqual(log.report()['total_sessions'], 1)

    def test_cli_start_and_report_are_real_and_exclude_agent_qa(self):
        import json
        import subprocess
        import sys
        with TemporaryDirectory() as directory:
            db = Path(directory) / 'study.sqlite'
            prefix = [sys.executable, '-m', 'evaluation.usability', '--db', str(db)]
            root = Path(__file__).resolve().parents[1]
            result = subprocess.run(prefix + ['start', 'qa-1', '--kind', 'agent_qa',
                                    '--background', 'unknown', '--runtime', 'RecorderQA',
                                    '--starter-revision', 'fixture-v1', '--consent'],
                                    cwd=root, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(result.stdout.strip(), 'CLI must return an actual saved session identifier')
            session = json.loads(result.stdout)['session']
            self.assertTrue(session)
            result = subprocess.run(prefix + ['report'], cwd=root, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads(result.stdout)
            self.assertEqual(report['total_sessions'], 1)
            self.assertEqual(report['eligible_humans_started'], 0)
            self.assertIsNone(report['success_rate'])

    def test_sensitive_pseudonyms_are_rejected_without_saving(self):
        with TemporaryDirectory() as directory:
            log = self.recorder(Path(directory) / 'study.sqlite')
            with self.assertRaises(ValueError):
                log.start('sk-proj-' + 'A' * 24, kind='agent_qa', background='unknown',
                          consent=True, runtime='RecorderQA', starter_revision='fixture-v1')
            self.assertEqual(log.report()['total_sessions'], 0)

    def test_blocked_and_unfinished_humans_remain_in_the_denominator(self):
        with TemporaryDirectory() as directory:
            log = self.recorder(Path(directory) / 'study.sqlite')
            args: dict = dict(kind='human', background='non_engineer', consent=True,
                        runtime='ChatGPT', starter_revision='fixture-revision',
                        observer='fixture-observer', attested=True)
            one = log.start('fixture-one', **args)
            log.start('fixture-two', **args)
            log.start('fixture-engineer', **dict(args, background='engineer'))
            agent = log.start('qa-only', kind='agent_qa', background='unknown', consent=True,
                              runtime='ChatGPT', starter_revision='fixture-revision')
            for session in (one, agent):
                log.step(session, 'create_project', status='blocked')
                log.step(session, 'create_project', status='blocked')
                log.finish(session, outcome='blocked')
            report = log.report()
            self.assertEqual(report['eligible_humans_started'], 2)
            self.assertEqual(report['unfinished_or_failed'], 2)
            self.assertEqual(report['success_rate'], 0.0)
            self.assertEqual(report['blocked_steps'], {'create_project': 1})

    def test_success_needs_all_steps_and_sanitized_regular_evidence(self):
        with TemporaryDirectory() as directory:
            log = self.recorder(Path(directory) / 'study.sqlite')
            session = log.start('qa-only', kind='agent_qa', background='unknown', consent=True,
                                runtime='RecorderQA', starter_revision='fixture-v1')
            evidence = Path(directory) / 'out.txt'
            evidence.write_text('Safe synthetic recorder test.')
            with self.assertRaises(ValueError):
                log.finish(session, outcome='success', evidence=evidence)
            from evaluation.usability import STEPS
            for step in STEPS:
                log.step(session, step, status='completed')
            with self.assertRaises(ValueError):
                log.finish(session, outcome='success')
            evidence.write_text('Contact alice@example.com')
            with self.assertRaises(ValueError):
                log.finish(session, outcome='success', evidence=evidence)
            alias = Path(directory) / 'alias.txt'
            alias.symlink_to(evidence)
            with self.assertRaises((OSError, ValueError)):
                log.finish(session, outcome='success', evidence=alias)
            log.finish(session, outcome='blocked')
            with self.assertRaises(ValueError):
                log.finish(session, outcome='abandoned')
            with self.assertRaises(ValueError):
                log.step(session, 'save_result', status='completed')

    def test_backwards_time_is_not_a_shorter_success(self):
        with TemporaryDirectory() as directory:
            tick = [datetime(2026, 10, 17, 8, tzinfo=timezone.utc)]
            log = self.recorder(Path(directory) / 'study.sqlite', clock=lambda: tick[0])
            session = log.start('qa-only', kind='agent_qa', background='unknown', consent=True,
                                runtime='RecorderQA', starter_revision='fixture-v1')
            tick[0] -= timedelta(seconds=1)
            with self.assertRaises(ValueError):
                log.step(session, 'download_kit', status='completed')
            with self.assertRaises(ValueError):
                log.finish(session, outcome='blocked')
            self.assertEqual(log.report()['eligible_humans_started'], 0)

    def test_public_or_symlinked_logs_are_not_accepted(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / 'study.sqlite'
            self.recorder(path)
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)
            path.chmod(0o644)
            with self.assertRaises(PermissionError):
                self.recorder(path)
            path.chmod(0o600)
            alias = Path(directory) / 'alias.sqlite'
            alias.symlink_to(path)
            with self.assertRaises((OSError, PermissionError)):
                self.recorder(alias)


if __name__ == '__main__':
    unittest.main()
