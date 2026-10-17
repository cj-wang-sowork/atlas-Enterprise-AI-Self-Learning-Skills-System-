"""Regression tests for tenant-bound learning-file authorization."""
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import learn_system
from learn_system import MultiMarketLearnManager


MARKERS = {"enterprise": "@public", "brand": "@internal", "department": "@internal",
           "team": "@team-private", "personal": "@private"}


class AccessControlTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.manager = MultiMarketLearnManager(str(self.root))

    def context(self, **overrides):
        self.assertTrue(hasattr(learn_system, "AccessContext"), "trusted AccessContext API is missing")
        values = dict(tenant_id="acme", brand_id="alpha", user_id="alice",
                      department_ids=frozenset({"marketing"}),
                      team_ids=frozenset({("marketing", "social")}))
        values.update(overrides)
        return learn_system.AccessContext(**values)

    def document(self, relative, **overrides):
        parts = Path(relative).parts
        tenant, level = parts[:2]
        metadata = dict(tenant_id=tenant, level=level, access=MARKERS[level])
        if level != "enterprise":
            metadata["brand_id"] = parts[2]
        if level in {"department", "team"}:
            metadata["department_id"] = parts[3]
        if level == "team":
            metadata["team_id"] = parts[4]
        if level == "personal":
            metadata["owner_id"] = parts[3]
        metadata.update(overrides)
        path = self.root / "learn" / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("---\n" + "\n".join(f"{key}: {value}" for key, value in metadata.items())
                        + "\n---\nBODY SENTINEL\n", encoding="utf-8")
        return path

    def test_authorized_hierarchy_includes_own_personal_files(self):
        expected = {
            self.document("acme/enterprise/global.md"),
            self.document("acme/brand/alpha/brand.md"),
            self.document("acme/department/alpha/marketing/department.md"),
            self.document("acme/team/alpha/marketing/social/team.md"),
            self.document("acme/personal/alpha/alice/private.md"),
        }
        files = self.manager.load_learn_files(self.context())
        self.assertEqual({item.path for item in files}, expected)
        self.assertTrue(all("BODY SENTINEL" in item.content for item in files))

    def test_authorized_loaders_reject_sensitive_content_before_return(self):
        safe_owner = self.document("acme/personal/alpha/alice/safe.md", market="us-en")
        context = self.context()
        for relative in ("acme/enterprise/unsafe.md", "acme/brand/alpha/unsafe.md",
                         "acme/personal/alpha/alice/unsafe.md"):
            for sensitive in ("sk-proj-" + "A" * 24, "alice@example.com"):
                with self.subTest(relative=relative, kind=sensitive[:3]):
                    path = self.document(relative, market="us-en")
                    with path.open("a", encoding="utf-8") as stream:
                        stream.write(sensitive + "\n")
                    with self.assertRaises(ValueError) as rejected:
                        self.manager.load_learn_file(path, context)
                    self.assertNotIn(sensitive, str(rejected.exception))
                    self.assertEqual([item.path for item in self.manager.load_learn_files(context)],
                                     [safe_owner])
                    self.assertEqual([item.path for item in self.manager.get_market_context("us-en", context)],
                                     [safe_owner])
                    report = self.manager.audit_security()
                    self.assertFalse(report["valid"])
                    self.assertTrue(any(str(path) in finding for finding in report["violations"]))
                    self.assertNotIn(sensitive, str(report))
                    path.unlink()
        self.assertIn("BODY SENTINEL", self.manager.load_learn_file(safe_owner, context).content)

    def test_direct_read_denies_foreign_scopes_before_open(self):
        self.assertTrue(hasattr(self.manager, "load_learn_file"), "scoped direct-read API is missing")
        denied = [
            "other/enterprise/public.md",
            "acme/brand/beta/brand.md",
            "acme/department/alpha/finance/department.md",
            "acme/team/alpha/marketing/paid/team.md",
            "acme/team/beta/marketing/social/same-name-team.md",
            "acme/team/alpha/finance/social/same-name-department.md",
            "acme/personal/alpha/bob/private.md",
            "other/personal/alpha/alice/same-name-owner.md",
        ]
        context = self.context()
        for relative in denied:
            path = self.document(relative)
            with self.subTest(relative=relative), mock.patch.object(
                self.manager, "_parse_learn_file", wraps=self.manager._parse_learn_file
            ) as parse:
                with self.assertRaises(PermissionError):
                    self.manager.load_learn_file(path, context)
                parse.assert_not_called()
        with mock.patch.object(self.manager, "_open_scoped_file", wraps=self.manager._open_scoped_file) as opened:
            self.assertEqual(self.manager.load_learn_files(context), [])
            opened.assert_not_called()

    def test_invalid_metadata_is_rejected_before_body_read(self):
        valid = self.document("acme/team/alpha/marketing/social/invalid.md")
        original = valid.read_text(encoding="utf-8")
        invalid_headers = [
            original.replace("tenant_id: acme\n", ""),
            original.replace("tenant_id: acme", "tenant_id: other"),
            original.replace("brand_id: alpha", "brand_id: beta"),
            original.replace("department_id: marketing", "department_id: finance"),
            original.replace("team_id: social", "team_id: paid"),
            original.replace("level: team", "level: enterprise"),
            original.replace("access: @team-private", "access: @public"),
            original.replace("access: @team-private", "access: @unknown"),
            original.replace("level: team", "level: team\nlevel: enterprise"),
            original.replace("---\nBODY", "owner_id: alice\n---\nBODY"),
            "BODY SENTINEL\n",
            "---\nlevel: team\nBODY SENTINEL\n",
        ]
        for content in invalid_headers:
            with self.subTest(header=content):
                valid.write_text(content, encoding="utf-8")
                with mock.patch.object(self.manager, "_read_body", create=True) as body:
                    self.assertEqual(self.manager.load_learn_files(self.context()), [])
                    with self.assertRaises((ValueError, PermissionError)):
                        self.manager.load_learn_file(valid, self.context())
                    body.assert_not_called()

    def test_symlinks_are_rejected_even_inside_authorized_scope(self):
        target = self.document("acme/team/alpha/marketing/social/real.md")
        leaf = target.with_name("alias.md")
        leaf.symlink_to(target)
        nested = target.parent / "linked-directory"
        nested.symlink_to(target.parent, target_is_directory=True)
        for path in (leaf, nested / "real.md"):
            with self.subTest(path=path), mock.patch.object(
                self.manager, "_read_body", wraps=self.manager._read_body
            ) as body:
                with self.assertRaises((ValueError, OSError, PermissionError)):
                    self.manager.load_learn_file(path, self.context())
                body.assert_not_called()
        self.assertEqual([item.path for item in self.manager.load_learn_files(self.context())], [target])

    def test_traversal_is_rejected_before_open_and_nested_files_remain_scoped(self):
        own = self.document("acme/team/alpha/marketing/social/nested/deeper/own.md")
        foreign = self.document("other/enterprise/foreign.md")
        traversal = own.parent / "../../../../../../../../other/enterprise/foreign.md"
        with mock.patch.object(self.manager, "_parse_learn_file") as parse:
            with self.assertRaises((ValueError, PermissionError)):
                self.manager.load_learn_file(traversal, self.context())
            parse.assert_not_called()
        self.assertEqual([item.path for item in self.manager.load_learn_files(self.context())], [own])
        self.assertEqual(self.manager.load_learn_file(own, self.context()).level, learn_system.LearningLevel.TEAM)
        self.assertTrue(foreign.exists())

    def test_identity_is_validated_and_memberships_are_immutable(self):
        invalid = [
            {"tenant_id": ""}, {"tenant_id": "../other"}, {"tenant_id": "acme/other"},
            {"brand_id": ""}, {"user_id": ""}, {"user_id": ".."},
            {"department_ids": "marketing"}, {"department_ids": {"marketing"}},
            {"department_ids": frozenset({"../finance"})},
            {"team_ids": frozenset({"social"})},
            {"team_ids": frozenset({("marketing", "social", "extra")})},
            {"team_ids": frozenset({("marketing", "../paid")})},
        ]
        for values in invalid:
            with self.subTest(values=values), self.assertRaises((ValueError, TypeError)):
                self.context(**values)
        context = self.context()
        with self.assertRaises(AttributeError):
            context.tenant_id = "other"
        with self.assertRaises(PermissionError):
            self.manager.load_learn_files({"tenant_id": "acme"})
        with self.assertRaises(PermissionError):
            self.manager.load_learn_files(learn_system.LearningLevel.TEAM)

    def test_invalid_scope_identifiers_are_rejected_before_open(self):
        path = self.document("acme/brand/invalid brand/forged.md")
        with mock.patch.object(self.manager, "_parse_learn_file") as parse:
            with self.assertRaises(ValueError):
                self.manager._scope_for_path(path)
            parse.assert_not_called()
        with self.assertRaises(ValueError):
            learn_system.ResourceScope("acme", learn_system.LearningLevel.ENTERPRISE, brand_id="alpha")

    def test_market_filter_requires_context_and_does_not_grant_scope(self):
        allowed = self.document("acme/brand/alpha/us.md", market="us-en")
        self.document("acme/brand/alpha/jp.md", market="jp-ja")
        self.document("other/enterprise/us.md", market="us-en")
        self.document("acme/brand/beta/us.md", market="us-en")
        with self.assertRaises(PermissionError):
            self.manager.get_market_context("us-en")
        try:
            files = self.manager.get_market_context("us-en", self.context())
        except PermissionError:
            self.fail("market-context loading does not forward the authenticated context")
        self.assertEqual([item.path for item in files], [allowed])

    def test_audit_reports_malformed_files_and_continues_without_context_loading(self):
        self.document("acme/enterprise/good.md")
        malformed = self.document("other/brand/beta/bad.md", access="@unknown")
        malformed.write_text("---\nlevel: NO_SUCH_LEVEL\n---\nSECRET BODY\n", encoding="utf-8")
        legacy = self.root / "learn" / "team" / "legacy.md"
        legacy.parent.mkdir(parents=True)
        legacy.write_text("legacy body", encoding="utf-8")
        with mock.patch.object(self.manager, "load_learn_files", side_effect=AssertionError("audit is separate")):
            report = self.manager.audit_security()
        self.assertFalse(report["valid"])
        self.assertEqual(report["files"], 3)
        self.assertEqual(len(report["violations"]), 2)
        self.assertNotIn("SECRET BODY", str(report))
        self.assertTrue(any(str(malformed) in violation for violation in report["violations"]))
        self.assertTrue(any(str(legacy) in violation for violation in report["violations"]))

    def test_audit_reports_directory_symlinks_without_following_them(self):
        good = self.document("acme/enterprise/good.md")
        link = good.parent / "linked"
        link.symlink_to(good.parent, target_is_directory=True)
        report = self.manager.audit_security()
        self.assertFalse(report["valid"])
        self.assertTrue(any(str(link) in violation for violation in report["violations"]))
        self.assertEqual(report["files"], 1)

    def test_symlinked_learn_root_is_not_a_valid_empty_audit(self):
        real = self.root / "external"
        real.mkdir()
        (self.root / "learn").symlink_to(real, target_is_directory=True)
        report = self.manager.audit_security()
        self.assertFalse(report["valid"])
        self.assertTrue(report["violations"])
        self.assertEqual(self.manager.load_learn_files(self.context()), [])

    def test_loading_without_authenticated_context_fails_closed(self):
        with self.assertRaises(PermissionError):
            self.manager.load_learn_files()


if __name__ == "__main__":
    unittest.main()
