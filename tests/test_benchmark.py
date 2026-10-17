import json
import subprocess
import sys
import unittest
from pathlib import Path


class ComparisonTests(unittest.TestCase):
    def test_security_comparison_is_real_and_explicitly_not_llm_benchmark(self):
        root = Path(__file__).resolve().parents[1]
        run = subprocess.run([sys.executable, str(root / 'scripts/compare_security.py')],
                             cwd=root, text=True, capture_output=True)
        self.assertEqual(run.returncode, 0, run.stderr)
        report = json.loads(run.stdout)
        self.assertEqual(report['benchmark_type'], 'security_fixture_regression_not_llm_quality')
        self.assertGreater(report['candidate_correct'], report['baseline_correct'])
        self.assertEqual(report['candidate_correct'], report['cases'])
        self.assertEqual(len(report['results']), report['cases'])


if __name__ == '__main__':
    unittest.main()
