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


if __name__ == '__main__':
    unittest.main()
