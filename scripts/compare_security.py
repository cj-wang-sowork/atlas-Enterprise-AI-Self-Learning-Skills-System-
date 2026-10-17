#!/usr/bin/env python3
"""Measured detector regression against a pinned repository commit, not AI quality."""
import argparse
import json
import subprocess
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from security_checker import SecurityChecker

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--baseline', default='525dcc2b27aa0c745c4ce7b1dfcf8672d4a4abd1')
args = parser.parse_args()
baseline_sha = subprocess.check_output(
    ['git', 'rev-parse', '--verify', args.baseline + '^{commit}'], cwd=ROOT, text=True).strip()
source = subprocess.check_output(
    ['git', 'show', baseline_sha + ':security_checker.py'], cwd=ROOT, text=True)
baseline_module = types.ModuleType('_atlas_baseline_security')
sys.modules[baseline_module.__name__] = baseline_module
exec(compile(source, baseline_sha + ':security_checker.py', 'exec'), baseline_module.__dict__)

# Synthetic fixtures, not credentials from any account. Report identifiers only.
fixtures = [
    ('clean_prose', 'A reviewed research workflow.', True),
    ('clean_scope_description', 'Use separate brands and teams.', True),
    ('labelled_password', 'password: synthetic-value', False),
    ('labelled_email', 'email: alice@example.com', False),
    ('unlabelled_email', 'Contact alice@example.com for help.', False),
    ('json_key', '{"api_key": "synthetic-value"}', False),
    ('standalone_openai_shape', 'sk-proj-' + 'a' * 48, False),
    ('standalone_github_shape', 'ghp_' + 'A' * 36, False),
    ('standalone_aws_shape', 'AKIA' + 'X' * 16, False),
    ('standalone_bearer', 'Bearer ' + 'Ab9_' * 12, False),
    ('traditional_chinese_password', '密碼：測試值', False),
    ('chinese_api_key', 'API金鑰 = synthetic-value', False),
    ('format_obfuscation', 'to\u200bken: synthetic-value', False),
    ('wide_equals', 'password＝synthetic-value', False),
    ('taiwan_mobile_shape', '請致電 0912-345-678', False),
    ('taiwan_id_shape', '身分證 A123456789', False),
    ('private_key_header', '-----BEGIN RSA PRIVATE KEY-----', False),
]
results = []
for case_id, content, expected_safe in fixtures:
    baseline_safe = baseline_module.SecurityChecker().scan_content(content)[0]
    candidate_safe = SecurityChecker().scan_content(content)[0]
    results.append({'id': case_id, 'expected_safe': expected_safe,
                    'baseline_safe': baseline_safe, 'candidate_safe': candidate_safe,
                    'baseline_correct': baseline_safe == expected_safe,
                    'candidate_correct': candidate_safe == expected_safe})
report = {
    'benchmark_type': 'security_fixture_regression_not_llm_quality',
    'baseline_commit': baseline_sha,
    'cases': len(results),
    'baseline_correct': sum(r['baseline_correct'] for r in results),
    'candidate_correct': sum(r['candidate_correct'] for r in results),
    'limitations': 'Curated deterministic fixtures; not representative DLP recall, production penetration testing, or evidence ATLAS outperforms a general AI workflow.',
    'results': results,
}
print(json.dumps(report, indent=2))
