"""Regression tests use synthetic content, never live credentials."""
import tempfile
import unittest
from pathlib import Path

from security_checker import SecurityChecker


class SecurityRegressionTests(unittest.TestCase):
    def test_unlabelled_email_is_sensitive(self):
        safe, violations = SecurityChecker().scan_content('Please contact alice@example.com')
        self.assertFalse(safe)
        self.assertIn('email', [v.violation_type for v in violations])

    def test_unlabelled_and_multilingual_credentials_are_sensitive(self):
        samples = [
            'Use sk-proj-' + 'a' * 48,
            'Here is ghp_' + 'A' * 36,
            'AKIA' + 'X' * 16,
            'Bearer ' + 'Ab9_' * 12,
            '密碼：不應保存的測試值',
            'API金鑰 = synthetic-test-value',
            '{"api_key": "synthetic-key"}',
            'to\u200bken: synthetic-test-token',
            'password＝synthetic-value',
        ]
        for content in samples:
            with self.subTest(content=content[:12]):
                safe, violations = SecurityChecker().scan_content(content)
                self.assertFalse(safe)
                self.assertTrue(any(v.severity.value == 'critical' for v in violations))

    def test_policy_allows_only_exact_email_not_credentials(self):
        checker = SecurityChecker(allowed_emails={'press@example.com'})
        self.assertTrue(checker.scan_content('Contact press@example.com')[0])
        self.assertFalse(checker.scan_content('Contact notpress@example.com')[0])
        self.assertFalse(checker.scan_content('api_key: press@example.com')[0])

    def test_classification_review_and_deny_terms_fail_closed(self):
        checker = SecurityChecker(deny_terms={'project-cobalt'})
        self.assertFalse(checker.scan_content('Internal project-cobalt notes')[0])
        for classification in ('confidential', 'restricted', 'unknown'):
            with self.subTest(classification=classification):
                safe, violations = checker.scan_content('ordinary prose', classification=classification)
                self.assertFalse(safe)
                self.assertIn('review_required', [v.violation_type for v in violations])
        self.assertTrue(checker.scan_content('ordinary prose', classification='internal')[0])

    def test_access_marker_is_exact_frontmatter_not_body_substring(self):
        checker = SecurityChecker()
        for content in ['body says @public', '---\naccess: @publicity\n---\n',
                        '---\naccess: @public\naccess: @private\n---\n',
                        '---\naccess: @public\nnever closed']:
            with self.subTest(content=content):
                self.assertFalse(checker.validate_access_marker(content)[0])
        self.assertTrue(checker.validate_access_marker('---\naccess: "@internal"\n---\ntext')[0])

    def test_taiwan_pii_in_chinese_prose_is_sensitive(self):
        for content in ('請致電 0912-345-678', '身分證 A123456789'):
            with self.subTest(content=content):
                self.assertFalse(SecurityChecker().scan_content(content)[0])

    def test_safe_prose_and_known_secret_shapes(self):
        self.assertTrue(SecurityChecker().scan_content('Use verified research and request human review.')[0])
        for content in ('-----BEGIN RSA PRIVATE KEY-----',
                        'xoxb-' + 'a' * 24, 'AIza' + 'z' * 35):
            with self.subTest(kind=content[:5]):
                self.assertFalse(SecurityChecker().scan_content(content)[0])

    def test_audit_does_not_contain_detected_values(self):
        import json
        with tempfile.TemporaryDirectory() as directory:
            audit = Path(directory) / 'audit.jsonl'
            checker = SecurityChecker(audit_log_path=str(audit))
            checker.scan_content('secret: synthetic-sensitive-value')
            output = audit.read_text()
            self.assertNotIn('synthetic-sensitive-value', output)
            self.assertTrue(json.loads(output)['violation_type'])
            self.assertEqual(checker.clear_violations(), 1)
            self.assertEqual(checker.get_violations(), [])

    def test_learning_audit_uses_same_sensitive_content_policy(self):
        from learn_system import AccessLevel, LearnFile, LearningLevel, LearnSecurityValidator
        validator = LearnSecurityValidator()
        for content in ('Contact alice@example.com', 'API金鑰 = synthetic-value'):
            resource = LearnFile(Path('safe.md'), LearningLevel.BRAND, AccessLevel.INTERNAL,
                                 content, '2026-10-17', 'tester')
            self.assertFalse(validator.validate_file(resource)[0])


if __name__ == '__main__':
    unittest.main()
