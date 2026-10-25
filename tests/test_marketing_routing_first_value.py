"""First-value regression contracts for the local rules-based helper."""
import unittest

from marketing_team.planner import plan_task


class RoutingFirstValueTests(unittest.TestCase):
    def test_narrow_revisions_reuse_bundled_methods_without_network(self):
        from marketing_team.discovery import discover_task
        from marketing_team.github import GitHubClient
        from unittest.mock import patch
        for task in ('幫我把這段文案縮短', 'Rewrite this copy',
                     'Resize this IG post', 'Edit this newsletter',
                     '幫我改好這個商品頁的標題和 CTA'):
            with self.subTest(task=task):
                policy = plan_task(task)['discovery_policy']
                self.assertEqual(policy, {'required': False, 'reason': 'BUNDLED_METHOD_REUSE'})
                client = GitHubClient(transport=lambda *a: self.fail('must not search'))
                with patch('marketing_team.discovery.GitHubClient', side_effect=AssertionError('must not construct')):
                    result = discover_task(task, client=client)
                    self.assertEqual(discover_task(task)['discovery']['requests'], 0)
                discovery = result['discovery']
                self.assertEqual(discovery['status'], 'SKIPPED_REUSE')
                self.assertEqual(discovery['availability'], 'BUNDLED_METHOD_REUSE')
                self.assertFalse(discovery['attempted'])
                self.assertEqual(discovery['queries'], [])
                self.assertEqual(discovery['candidates'], [])
                self.assertEqual(discovery['requests'], 0)
                self.assertFalse(result['executed'])

    def test_research_freshness_and_capability_gaps_override_revision_reuse(self):
        from marketing_team.discovery import discover_task
        from marketing_team.github import GitHubClient, Response
        for task in ('重新研究市場', '改寫並查最新趨勢', 'Rewrite copy and search latest trends',
                     'Edit copy with new sources', 'Revise SEO using a missing capability',
                     'Rewrite copy with a new method', 'Shorten copy and research competitors',
                     'Edit copy and find hot trends', 'SEO audit', 'Plan IG calendar'):
            with self.subTest(task=task):
                self.assertTrue(plan_task(task)['discovery_policy']['required'])
                calls = []
                def transport(*args):
                    calls.append(args)
                    return Response(200, {}, b'{"items":[],"total_count":0,"incomplete_results":false}')
                for unused in range(2):
                    result = discover_task(task, client=GitHubClient(transport=transport))
                    self.assertTrue(result['discovery']['attempted'])
                self.assertGreaterEqual(len(calls), 2)
                self.assertNotIn(task, str(calls))

    def test_force_search_overrides_reuse_through_api_and_cli(self):
        import contextlib
        import io
        import json
        from unittest.mock import patch
        from marketing_team.__main__ import main
        from marketing_team.discovery import discover_task
        from marketing_team.github import GitHubClient, Response
        calls = []
        def transport(*args):
            calls.append(args)
            return Response(200, {}, b'{"items":[],"total_count":0,"incomplete_results":false}')
        task = 'Shorten this copy'
        result = discover_task(task, client=GitHubClient(transport=transport), force_search=True)
        self.assertTrue(result['discovery']['attempted'])
        self.assertTrue(result['discovery_policy']['required'])
        self.assertEqual(result['discovery_policy']['reason'], 'FORCED_SEARCH')
        output = io.StringIO()
        with patch('marketing_team.discovery.GitHubClient', return_value=GitHubClient(transport=transport)), contextlib.redirect_stdout(output):
            code = main(['discover', '--task', task, '--force-search'])
        self.assertEqual(code, 0)
        self.assertTrue(json.loads(output.getvalue())['discovery']['attempted'])
        self.assertEqual(len(calls), 2)

    def test_common_core_search_policy_distinguishes_small_revisions(self):
        from pathlib import Path
        root = Path(__file__).resolve().parents[1]
        for relative in ('team_core/SKILL.md', 'team_core/resources/discovery.md'):
            with self.subTest(path=relative):
                text = (root / relative).read_text()
                self.assertIn('capability or method gap', text)
                self.assertIn('small revisions', text)
                self.assertIn('SKIPPED_REUSE', text)
                self.assertIn('--force-search', text)
                self.assertIn('untrusted', text)

    def test_frozen_twelve_natural_marketing_requests(self):
        cases = [
            ('幫我規劃 IG 下個月的內容', {'social'}),
            ('幫我做品牌定位', {'brand'}),
            ('幫我寫 7 篇 LinkedIn 貼文', {'social'}),
            ('幫我提高官網轉換率', {'analytics', 'copy'}),
            ('幫我找適合合作的 KOL', {'research'}),
            ('幫我分析這份 GA4 數據', {'analytics'}),
            ('幫我規劃 Meta 廣告測試', {'ads'}),
            ('替新產品寫一封 EDM', {'email'}),
            ('幫我做 SEO audit', {'seo'}),
            ('把這場活動整理成貼文', {'events', 'social'}),
            ('幫我改好這個商品頁的標題和 CTA', {'copy'}),
            ('幫我把這段文案縮短', {'copy'}),
        ]
        self.assertEqual(len(cases), 12)
        for task, expected in cases:
            with self.subTest(task=task):
                plan = plan_task(task)
                self.assertEqual(plan['status'], 'PLANNED')
                self.assertTrue(expected.intersection(plan['domains']))
                self.assertTrue(plan['methods'])
                self.assertFalse(plan['executed'])

    def test_creator_collaboration_guidance_requires_evidence(self):
        for task in ('找適合合作的 KOL', 'KOC shortlist', 'influencer collaboration'):
            with self.subTest(task=task):
                guidance = plan_task(task)['workflow'][0]['guidance'].lower()
                self.assertIn('creator', guidance)
                self.assertIn('audience fit', guidance)
                self.assertIn('unverified', guidance)
                self.assertIn('disclosure', guidance)

    def test_aliases_do_not_match_incidental_ascii_substrings(self):
        for task in ('help me', 'content', '幫我處理一下', 'big figure',
                     'fbx export', 'microcontroller', 'octagon', 'kolkata',
                     'kocoon', 'influencerish', 'my_linkedin_backup'):
            with self.subTest(task=task):
                self.assertEqual(plan_task(task)['status'], 'NEEDS_CLARIFICATION')
        for task, domain in [('FB calendar', 'social'), ('CRO audit', 'analytics'),
                             ('CTA revision', 'copy'), ('KOC shortlist', 'research'),
                             ('influencer collaboration', 'research')]:
            with self.subTest(task=task):
                self.assertIn(domain, plan_task(task)['domains'])
