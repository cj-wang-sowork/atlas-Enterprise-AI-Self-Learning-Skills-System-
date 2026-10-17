"""Harness regression tests; synthetic test data are NOT pilot observations."""
import copy
import importlib
import importlib.util
import json
import unittest


class LockAndScheduleTests(unittest.TestCase):
    def test_invalid_rubric_fails_before_execution(self):
        paired = importlib.import_module('evaluation.paired')
        task = {'task_id': 'test-only', 'source_kind': 'fictional', 'brief': 'Test only',
                'sources': [{'id': 'S1', 'text': 'Test fact'}],
                'rubric': {'required_facts': ['Test fact'], 'forbidden_patterns': ['[invalid']}}
        with self.assertRaises(ValueError):
            paired.validate_dataset({'schema_version': 1, 'tasks': [task]})
        task['rubric'] = {'required_facts': [], 'forbidden_patterns': []}
        with self.assertRaises(ValueError):
            paired.validate_dataset({'schema_version': 1, 'tasks': [task]})

    def test_content_lock_detects_mutation_and_schedule_is_paired(self):
        self.assertIsNotNone(importlib.util.find_spec('evaluation'),
                             'paired evaluation package must exist')
        paired = importlib.import_module('evaluation.paired')
        dataset = {'schema_version': 1, 'tasks': [
            {'task_id': name, 'source_kind': 'fictional', 'brief': 'Draft copy',
             'sources': [{'id': 'S1', 'text': 'Test fact'}],
             'rubric': {'required_facts': ['Test fact'], 'forbidden_patterns': []}}
            for name in ['a', 'b', 'c']]}
        paired.validate_dataset(dataset)
        lock = paired.digest_json(dataset)
        changed = copy.deepcopy(dataset)
        changed['tasks'][0]['brief'] = 'Different task'
        self.assertNotEqual(lock, paired.digest_json(changed))
        schedule = paired.make_schedule(dataset, seed=17)
        self.assertEqual(len(schedule), 6)
        for task_id in ['a', 'b', 'c']:
            self.assertEqual({x['arm'] for x in schedule if x['task_id'] == task_id},
                             {'baseline', 'atlas_reference'})
        self.assertEqual([x['arm'] for x in schedule[::2]],
                         ['baseline', 'atlas_reference', 'baseline'])
        self.assertEqual(schedule, paired.make_schedule(dataset, seed=17))
        with self.assertRaises(ValueError):
            paired.validate_dataset({'schema_version': 1, 'tasks': [dataset['tasks'][0]] * 3})


class GateTests(unittest.TestCase):
    def test_optimized_python_keeps_format_validation_active(self):
        import subprocess
        import sys
        from pathlib import Path
        root = Path(__file__).resolve().parents[1]
        result = subprocess.run([sys.executable, '-O', '-c',
            'import json; from evaluation.paired import score_output; '
            'task={"task_id":"test-only","sources":[{"id":"S1","text":"Fact"}],'
            '"rubric":{"required_facts":["Fact"],"forbidden_patterns":[]}}; '
            'obj={"task_id":"WRONG","status":"approved","positioning":"Test",'
            '"headlines":["a","b","c"],"cta":"Test","claims":[{"text":"Fact",'
            '"source_ids":["S1"]}],"gaps":["Test only"]}; '
            'print(score_output(task,json.dumps(obj))["format"])'],
            cwd=root, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), 'False')

    def test_narrow_gates_reject_missing_sources_invented_facts_and_malformed_output(self):
        paired = importlib.import_module('evaluation.paired')
        task = {'task_id': 'test-only', 'sources': [{'id': 'S1', 'text': 'Costs $20 per month.'}],
                'rubric': {'required_facts': ['$20'], 'forbidden_patterns': ['guaranteed sales']}}
        output = {'task_id': 'test-only', 'status': 'draft', 'positioning': 'A clear draft.',
                  'headlines': ['One', 'Two', 'Three'], 'cta': 'Learn more',
                  'claims': [{'text': 'Costs $20 per month.', 'source_ids': ['S1']}],
                  'gaps': ['No approved guideline supplied.']}
        self.assertTrue(paired.score_output(task, json.dumps(output))['all_passed'])
        bad = copy.deepcopy(output)
        bad['claims'][0]['source_ids'] = ['invented-source']
        self.assertFalse(paired.score_output(task, json.dumps(bad))['source_refs'])
        bad = copy.deepcopy(output)
        bad['claims'][0]['text'] = 'Guaranteed sales for $20.'
        score = paired.score_output(task, json.dumps(bad))
        self.assertFalse(score['claim_allowlist'])
        self.assertFalse(score['forbidden_claims'])
        self.assertFalse(paired.score_output(task, 'not json')['format'])
        bad = copy.deepcopy(output)
        bad['claims'] = []
        self.assertFalse(paired.score_output(task, json.dumps(bad))['required_facts'])
        self.assertFalse(paired.score_output(task, json.dumps(output), tool_calls=1)['tool_free'])


class TransportTests(unittest.TestCase):
    def test_real_subprocess_captures_exit_timeout_and_redacts_log_secrets(self):
        paired = importlib.import_module('evaluation.paired')
        import sys
        import tempfile
        from pathlib import Path
        with tempfile.TemporaryDirectory() as tmp:
            ok = paired.run_command([sys.executable, '-c',
                                     'import os; print(os.isatty(0)); print("Bearer test-only-secret")'],
                                    Path(tmp), 5)
            self.assertEqual(ok['exit_code'], 0)
            self.assertIn('True', ok['transcript'])
            self.assertNotIn('test-only-secret', ok['transcript'])
            self.assertGreater(ok['wall_seconds'], 0)
            bad = paired.run_command([sys.executable, '-c', 'raise SystemExit(7)'], Path(tmp), 5)
            self.assertEqual(bad['exit_code'], 7)
            timed = paired.run_command([sys.executable, '-c', 'import time; time.sleep(4)'], Path(tmp), 0.05)
            self.assertTrue(timed['timed_out'])
            self.assertLess(timed['wall_seconds'], 2)
            closed = paired.run_command([sys.executable, '-c',
                'import os,time; os.close(0); os.close(1); os.close(2); time.sleep(4)'], Path(tmp), 0.05)
            self.assertTrue(closed['timed_out'])
            self.assertLess(closed['wall_seconds'], 2)
            missing = paired.run_command(['/nonexistent/TEST_ONLY'], Path(tmp), 5)
            self.assertIsNone(missing['exit_code'])
            self.assertIn('No such file', missing['transcript'])


class RunnerTests(unittest.TestCase):
    def test_dry_run_pins_prompts_and_failure_accounting_does_not_drop_arms(self):
        paired = importlib.import_module('evaluation.paired')
        import sys
        import tempfile
        from pathlib import Path
        dataset = {'schema_version': 1, 'tasks': [
            {'task_id': name, 'source_kind': 'fictional', 'brief': 'Draft copy',
             'sources': [{'id': 'S1', 'text': 'Test fact'}],
             'rubric': {'required_facts': ['Test fact'], 'forbidden_patterns': []}}
            for name in ['a', 'b', 'c']]}
        packet = 'TEST ONLY reference instruction'
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            dry = paired.run_study(dataset, packet, root / 'dry', root / 'work',
                                   execute=False, provider_argv=['TEST_ONLY'])
            self.assertEqual(dry['summary']['planned_calls'], 6)
            self.assertEqual(dry['summary']['attempted_calls'], 0)
            self.assertTrue(all(r['status'] == 'not_run' for r in dry['runs']))
            with self.assertRaises(ValueError):
                paired.run_study(dataset, packet, root / 'over-budget', root / 'work',
                                 execute=True, provider_argv=['TEST_ONLY'], max_calls=5)
            with self.assertRaises(ValueError):
                paired.run_study(dataset, packet, root / 'empty-command', root / 'work',
                                 execute=False, provider_argv=[])
            # Real local subprocesses, explicitly TEST ONLY; never model observations.
            failed = paired.run_study(dataset, packet, root / 'failed', root / 'work',
                                      execute=True, provider_argv=[sys.executable, '-c',
                                                                 'raise SystemExit(7)'],
                                      provider_label='TEST_ONLY_LOCAL_SUBPROCESS')
            self.assertEqual(failed['summary']['attempted_calls'], 6)
            self.assertEqual(failed['summary']['failed_calls'], 6)
            self.assertEqual(failed['summary']['completed_calls'], 0)
            self.assertEqual(len(failed['runs']), 6)
            self.assertTrue(all(r['human_scores'] is None for r in failed['runs']))
            self.assertTrue(all(r['cost_usd'] is None for r in failed['runs']))
            self.assertTrue((root / 'failed' / 'human-scoring.json').exists())
            form = json.loads((root / 'failed' / 'human-scoring.json').read_text())
            self.assertNotIn('baseline', json.dumps(form))
            self.assertNotIn('atlas_reference', json.dumps(form))
            self.assertEqual(paired.verify_study(root / 'failed'), [])
            prompt = root / 'failed' / failed['runs'][0]['prompt_path']
            prompt.write_text('tampered')
            self.assertTrue(paired.verify_study(root / 'failed'))

    def test_blinded_bundle_contains_only_exact_outputs_not_condition_keys(self):
        paired = importlib.import_module('evaluation.paired')
        import tempfile
        from pathlib import Path
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'answer.txt').write_text('TEST_ONLY exact provider output')
            runs = [{'run_id': 'a', 'arm': 'baseline', 'task_id': 't', 'status': 'completed',
                     'output_path': 'answer.txt', 'output_digest': 'test-digest'}]
            form, key = paired.human_form({'runs': runs}, {'t': {'brief': 'Test only'}}, 17, root)
            self.assertEqual(form['rows'][0]['output'], 'TEST_ONLY exact provider output')
            self.assertIsNone(form['rows'][0]['scores']['brand_fit'])
            self.assertNotIn('baseline', json.dumps(form))
            self.assertEqual(key['X001']['arm'], 'baseline')

    def test_verifier_checks_task_locks_beyond_resealed_manifest(self):
        paired = importlib.import_module('evaluation.paired')
        import tempfile
        from pathlib import Path
        dataset = {'schema_version': 1, 'tasks': [
            {'task_id': 'test-only', 'source_kind': 'fictional', 'brief': 'Test only',
             'sources': [{'id': 'S1', 'text': 'Test fact'}],
             'rubric': {'required_facts': ['Test fact'], 'forbidden_patterns': []}}]}
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paired.run_study(dataset, 'TEST ONLY packet', root / 'study', root / 'work')
            path = root / 'study' / 'manifest.json'
            report = json.loads(path.read_text())
            report['runs'][0]['task_digest'] = '0' * 64
            path.write_text(json.dumps(report))
            (path.parent / 'manifest.sha256').write_text(paired.digest_bytes(path.read_bytes()))
            self.assertIn('task digest mismatch: run-01', paired.verify_study(path.parent))

    def test_event_usage_is_actual_or_unknown_and_tools_are_detected(self):
        paired = importlib.import_module('evaluation.paired')
        # Clearly synthetic protocol fixtures for parser coverage, not trial data.
        events = '\n'.join(json.dumps(x) for x in [
            {'type': 'item.completed', 'item': {'type': 'command_execution'}},
            {'type': 'turn.completed', 'usage': {'input_tokens': 3, 'output_tokens': 4}}])
        parsed = paired.parse_events(events)
        self.assertEqual(parsed['usage'], {'input_tokens': 3, 'output_tokens': 4})
        self.assertEqual(parsed['tool_calls'], 1)
        self.assertTrue(parsed['turn_completed'])
        self.assertIsNone(paired.parse_events('bad log')['usage'])


class SyntheticProtocolRegressionTests(unittest.TestCase):
    """Fictional LOCAL subprocess fixtures, never provider/model evidence."""

    def setUp(self):
        import tempfile
        from pathlib import Path
        self.paired = importlib.import_module('evaluation.paired')
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.dataset = {'schema_version': 1, 'tasks': [
            {'task_id': 'TEST_ONLY_LOCAL', 'source_kind': 'fictional', 'brief': 'Test only',
             'sources': [{'id': 'S1', 'text': 'TEST_ONLY fictional fact'}],
             'rubric': {'required_facts': ['TEST_ONLY fictional fact'], 'forbidden_patterns': []}}]}

    def local_argv(self, terminal=None):
        import sys
        task = self.dataset['tasks'][0]
        answer = json.dumps({'task_id': task['task_id'], 'status': 'draft',
                             'positioning': 'Test draft', 'headlines': ['One', 'Two', 'Three'],
                             'cta': 'Test only', 'claims': [
                                 {'text': task['sources'][0]['text'], 'source_ids': ['S1']}],
                             'gaps': ['TEST_ONLY missing approval']}, ensure_ascii=False)
        events = [
            {'type': 'item.completed', 'item': {'type': 'agent_message', 'text': answer}},
            {'type': 'turn.completed', 'usage': {'input_tokens': 1, 'output_tokens': 1}}]
        if terminal:
            events.append({'type': terminal, 'message': 'TEST_ONLY terminal failure'})
        script = 'print(' + repr('\n'.join(json.dumps(e) for e in events)) + ')'
        return [sys.executable, '-c', script], answer.encode()

    def study(self, argv):
        return self.paired.run_study(
            self.dataset, 'TEST_ONLY packet', self.root / 'study', self.root / 'work',
            execute=True, provider_argv=argv, provider_label='TEST_ONLY_LOCAL_SUBPROCESS')

    def cli(self, argv, *, execute=True, total_timeout='5'):
        import subprocess
        import sys
        from pathlib import Path
        (self.root / 'dataset.json').write_text(json.dumps(self.dataset))
        (self.root / 'packet.txt').write_text('TEST_ONLY packet')
        command = [sys.executable, '-m', 'evaluation.paired', 'run',
                   '--dataset', str(self.root / 'dataset.json'),
                   '--packet', str(self.root / 'packet.txt'),
                   '--output', str(self.root / 'study'),
                   '--scratch-root', str(self.root / 'work'),
                   '--provider-command-json', json.dumps(argv),
                   '--total-timeout-seconds', total_timeout]
        if execute:
            command.append('--execute')
        return subprocess.run(command, cwd=Path(__file__).resolve().parents[1],
                              capture_output=True, text=True, timeout=10)

    def test_cli_executed_budget_exhaustion_is_nonzero_even_without_failed_calls(self):
        argv, _ = self.local_argv()
        result = self.cli(argv, total_timeout='1e-12')
        summary = json.loads(result.stdout)
        self.assertEqual(summary['attempted_calls'], 0)
        self.assertEqual(summary['failed_calls'], 0)
        self.assertEqual(summary['not_run_calls'], 2)
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        report = json.loads((self.root / 'study' / 'manifest.json').read_text())
        self.assertTrue(all(r['failure_reason'] == 'total_timeout_budget' for r in report['runs']))
        self.assertEqual(self.paired.verify_study(self.root / 'study'), [])

    def test_verifier_rejects_completed_status_hiding_terminal_failure_with_resealed_counts(self):
        argv, _ = self.local_argv('turn.failed')
        report = self.study(argv)
        report['runs'][0]['status'] = 'completed'
        report['runs'][0]['failure_reason'] = None
        report['summary'] = self.paired.summarize(report['runs'])
        manifest = self.root / 'study' / 'manifest.json'
        manifest.write_text(json.dumps(report))
        (manifest.parent / 'manifest.sha256').write_text(
            self.paired.digest_bytes(manifest.read_bytes()))
        self.assertIn('completed run contradicts execution evidence: run-01',
                      self.paired.verify_study(manifest.parent))

    def test_event_only_preserves_exact_answer_before_log_redaction_and_scoring(self):
        from pathlib import Path
        fact = 'Bearer TEST_ONLY_NOT_A_CREDENTIAL; fictional path ' + str(Path.home())
        self.dataset['tasks'][0]['sources'][0]['text'] = fact
        self.dataset['tasks'][0]['rubric']['required_facts'] = [fact]
        argv, answer = self.local_argv()
        argv[2] += '\nprint("Authorization: Bearer TEST_ONLY_DIAGNOSTIC_NOT_A_CREDENTIAL")'
        self.assertTrue(self.paired.score_output(self.dataset['tasks'][0], answer.decode())['all_passed'])
        report = self.study(argv)
        self.assertEqual(report['summary']['completed_calls'], 2)
        for run in report['runs']:
            self.assertEqual((self.root / 'study' / run['output_path']).read_bytes(), answer)
            self.assertEqual(run['output_digest'], self.paired.digest_bytes(answer))
            self.assertTrue(run['gates']['all_passed'])
            log = (self.root / 'study' / run['log_path']).read_text()
            self.assertNotIn('TEST_ONLY_NOT_A_CREDENTIAL', log)
            self.assertNotIn('TEST_ONLY_DIAGNOSTIC_NOT_A_CREDENTIAL', log)
            self.assertNotIn(str(Path.home()), log)
            self.assertIn('<REDACTED>', log)
            self.assertIn('<HOME>', log)
        form = json.loads((self.root / 'study' / 'human-scoring.json').read_text())
        self.assertTrue(all(row['output'] == answer.decode() for row in form['rows']))
        for path in (self.root / 'study').rglob('*'):
            if path.is_file():
                self.assertNotIn(b'TEST_ONLY_DIAGNOSTIC_NOT_A_CREDENTIAL', path.read_bytes())
        self.assertEqual(self.paired.verify_study(self.root / 'study'), [])

    def test_cli_terminal_failure_returns_nonzero_and_retains_both_arms(self):
        argv, _ = self.local_argv('turn.failed')
        result = self.cli(argv)
        self.assertNotEqual(result.returncode, 0, result.stderr)
        summary = json.loads(result.stdout)
        self.assertEqual((summary['completed_calls'], summary['failed_calls'],
                          summary['not_run_calls']), (0, 1, 1))
        self.assertEqual(self.paired.verify_study(self.root / 'study'), [])

    def test_cli_dry_plan_succeeds_without_executing_command(self):
        argv, _ = self.local_argv()
        argv[2] = 'raise RuntimeError("TEST_ONLY must not execute dry run")'
        result = self.cli(argv, execute=False)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)['attempted_calls'], 0)
        self.assertFalse((self.root / 'work').exists() and list((self.root / 'work').iterdir()))
        self.assertEqual(self.paired.verify_study(self.root / 'study'), [])

    def test_cli_complete_local_execution_succeeds(self):
        argv, _ = self.local_argv()
        result = self.cli(argv)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)['completed_calls'], 2)
        self.assertEqual(self.paired.verify_study(self.root / 'study'), [])

    def test_error_event_after_completed_also_invalidates_run(self):
        argv, _ = self.local_argv('error')
        report = self.study(argv)
        self.assertEqual((report['summary']['completed_calls'], report['summary']['failed_calls'],
                          report['summary']['not_run_calls']), (0, 1, 1))
        self.assertEqual(self.paired.verify_study(self.root / 'study'), [])

    def test_output_file_bytes_take_precedence_over_event_message(self):
        argv, answer = self.local_argv()
        # Exact file bytes include trailing CRLF; the event is deliberately different.
        answer += b'\r\n'
        argv[2] = ('import pathlib, sys\npathlib.Path(sys.argv[1]).write_bytes(' + repr(answer)
                   + ')\nprint(\'{"type":"item.completed","item":{"type":"agent_message",'
                   '"text":"TEST_ONLY noncanonical event summary"}}\')\n'
                   'print(\'{"type":"turn.completed"}\')')
        argv.append('{output}')
        report = self.study(argv)
        for run in report['runs']:
            self.assertEqual(run['status'], 'completed')
            self.assertEqual((self.root / 'study' / run['output_path']).read_bytes(), answer)
            self.assertEqual(run['output_digest'], self.paired.digest_bytes(answer))
            self.assertTrue(run['gates']['all_passed'])
        self.assertEqual(self.paired.verify_study(self.root / 'study'), [])

    def test_terminal_failure_after_completed_invalidates_run_and_retains_evidence(self):
        argv, answer = self.local_argv('turn.failed')
        report = self.study(argv)
        self.assertEqual(report['summary']['completed_calls'], 0)
        self.assertEqual(report['summary']['failed_calls'], 1)
        self.assertEqual(report['summary']['not_run_calls'], 1)
        first, second = report['runs']
        self.assertEqual(first['status'], 'failed')
        self.assertEqual(first['failure_reason'], 'provider_or_protocol_failure')
        self.assertEqual(second['failure_reason'], 'prior_provider_failure')
        self.assertEqual((self.root / 'study' / first['output_path']).read_bytes(), answer)
        self.assertIn('turn.failed', (self.root / 'study' / first['log_path']).read_text())
        self.assertEqual(self.paired.verify_study(self.root / 'study'), [])


if __name__ == '__main__':
    unittest.main()
