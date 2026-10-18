"""Offline integrity checks for the frozen real pilot, not human outcome ratings."""
import hashlib
import json
import csv
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
STUDY = ROOT / 'studies' / 'sowork-acquisition'
RUN = STUDY / 'run-20261017'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path):
    return json.loads(path.read_text(encoding='utf-8'))


class FrozenAcquisitionStudyTests(unittest.TestCase):
    def test_frozen_plan_input_prompts_and_original_answers_match(self):
        manifest = load(RUN / 'manifest.json')
        self.assertTrue(manifest['complete'])
        self.assertEqual(manifest['config'], load(STUDY / 'execution-plan.json')['config'])
        self.assertEqual(len(manifest['invocations']), 5)
        self.assertEqual(len(manifest['task_runs']), 4)
        self.assertEqual({r['id'] for r in manifest['invocations']},
                         {'preflight', 'run-01', 'run-02', 'run-03', 'run-04'})
        config = manifest['config']
        self.assertEqual(config['source_pool_sha256'], sha(STUDY / 'source-pool.json'))
        self.assertEqual(config['protocol_sha256'], sha(STUDY / 'PROTOCOL.md'))
        self.assertEqual(config['runner_sha256'], sha(RUN / 'runner-at-execution.py.txt'))
        self.assertEqual(config['operating_packet_sha256'], sha(RUN / 'operating-packet.txt'))
        for record in manifest['invocations']:
            self.assertEqual(record['status'], 'completed')
            self.assertEqual(record['exit_code'], 0)
            self.assertFalse(record['timed_out'])
            self.assertEqual(record['protocol_errors'], [])
            self.assertEqual(record['tool_calls'], 0)
            self.assertEqual(record['output_sha256'], sha(RUN / 'outputs' / (record['id'] + '.txt')))
            self.assertEqual(record['log_sha256'], sha(RUN / 'logs' / (record['id'] + '.jsonl')))
        for name, value in config['prompt_sha256'].items():
            self.assertIn(name, {'run-01', 'run-02', 'run-03', 'run-04'})
            self.assertEqual(value, sha(RUN / 'prompts' / (name + '.txt')))
        prefix = (RUN / 'operating-packet.txt').read_text() + '\n\n'
        for baseline, candidate in [('run-01', 'run-02'), ('run-04', 'run-03')]:
            a = (RUN / 'prompts' / (baseline + '.txt')).read_text()
            b = (RUN / 'prompts' / (candidate + '.txt')).read_text()
            self.assertTrue(b.startswith(prefix))
            self.assertEqual(a, b[len(prefix):])

    def test_metadata_and_draft_contract_recompute_without_quality_claims(self):
        pool = load(STUDY / 'source-pool.json')['candidates']
        self.assertEqual(len(pool), 20)
        sources = {r['id']: r for r in pool}
        self.assertEqual(len(sources), 20)
        measurements = load(STUDY / 'measurements.json')['measurements']
        for run_id in ('run-03', 'run-04'):
            rows = load(RUN / 'outputs' / (run_id + '.txt'))['leads']
            self.assertEqual(len(rows), 20)
            self.assertEqual({row['source_id'] for row in rows}, set(sources))
            for row in rows:
                source = sources[row['source_id']]
                for field in ('company', 'signal_date', 'signal_url', 'source_access'):
                    self.assertEqual(row[field], source[field])
                for field in ('budget', 'decision_maker', 'agency_need', 'purchase_intent'):
                    self.assertEqual(row['unknowns'][field], 'unknown')
                self.assertEqual(row['outreach_status'], 'draft_not_sent')
                self.assertTrue(0 < len(row['outreach_draft']) <= 100)
            for field in ('lead_count', 'unique_source_ids', 'metadata_traceable_rows',
                          'explicit_unknown_fields_rows', 'unsent_draft_rows',
                          'drafts_at_most_100_codepoints'):
                self.assertEqual(measurements[run_id][field], 20)
            self.assertIn('NOT factual accuracy', measurements[run_id]['measurement_boundary'])
        self.assertEqual(sum(r['source_access'] == 'official_snippet_only' for r in pool), 2)
        self.assertEqual(sum(r['source_access'] == 'first_party_body_tls_unverified' for r in pool), 2)

    def test_delivered_csv_preserves_all_original_drafts_and_source_caveats(self):
        sources = {row['company']: row for row in load(STUDY / 'source-pool.json')['candidates']}
        arms = {arm: {row['company']: row for row in load(RUN / 'outputs' / (run_id + '.txt'))['leads']}
                for arm, run_id in [('A', 'run-04'), ('B', 'run-03')]}
        path = ROOT / 'outputs' / 'sowork-acquisition-20-comparison.csv'
        with path.open(encoding='utf-8-sig', newline='') as handle:
            rows = list(csv.DictReader(handle))
        self.assertEqual(len(rows), 20)
        self.assertEqual({row['公司'] for row in rows}, set(sources))
        for row in rows:
            company = row['公司']
            self.assertEqual(row['A組未寄送草稿'], arms['A'][company]['outreach_draft'])
            self.assertEqual(row['B組未寄送草稿'], arms['B'][company]['outreach_draft'])
            self.assertEqual(row['官方訊號URL'], sources[company]['signal_url'])
            self.assertEqual(row['來源存取狀態'], sources[company]['source_access'])
            self.assertEqual(row['總部或所在地證據'], sources[company]['country_evidence_status'])

    def test_proxy_boundary_no_invented_c_cycles_or_human_ratings(self):
        config = load(RUN / 'manifest.json')['config']
        scores = load(STUDY / 'human-scorecard.json')
        measurements = load(STUDY / 'measurements.json')
        self.assertIn('NOT actual ChatGPT UI', config['platform_boundary'])
        self.assertEqual(config['C_status'], 'blocked_not_run')
        self.assertEqual(config['approved_learning_cycles'], 0)
        self.assertIsNone(config['human_ratings'])
        self.assertEqual(scores['independent_raters'], 0)
        self.assertIsNone(scores['C']['scores'])
        self.assertIsNone(measurements['human_quality_scores'])
        self.assertIsNone(measurements['response_rate'])
        self.assertIsNone(measurements['conversion_rate'])
        self.assertTrue(all(r['independent_human_ratings'] is None
                            for r in measurements['measurements'].values()))


if __name__ == '__main__':
    unittest.main()
