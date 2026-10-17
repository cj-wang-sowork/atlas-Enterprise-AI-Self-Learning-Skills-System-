"""Outcome learning acceptance tests (no network or real user data)."""
import unittest
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from hermes_adapter import HermesAdapter, LearningMode


def governed(**kwargs):
    return HermesAdapter(
        scope={"tenant": "acme", "brand": "atlas", "team": "content", "user": "owner"},
        reviewers={"human:alice"}, verifiers={"runner:qa"}, **kwargs,
    )


def evidence(adapter, task="task-1", **overrides):
    fields = dict(task_id=task, source_ref="run://" + task,
                  result_ref="report://" + task, metric="defects", baseline=5,
                  candidate=1, direction="lower", success=True)
    fields.update(overrides)
    adapter.record_outcome(**fields)
    adapter.verify_outcome(task, validator="runner:qa")
    return task


def draft(adapter, task="task-1", skill_id=None):
    adapter.observe_access("us-en", "team", "write", True)
    pattern_id = next(iter(adapter.patterns))
    return adapter.draft_lesson(pattern_id, "Check citations before delivery.", [task],
                                skill_id=skill_id)


class StructuredSafetyTests(unittest.TestCase):
    def test_numeric_json_values_and_assignments_are_screened(self):
        from skill_registry import scan_safe
        from security_checker import SecurityChecker
        checker = SecurityChecker()
        samples = ({'password': 2468}, {'nested': [{'phone': 2025550123}]},
                   {'api_key': 123456}, {'nested': [2025550123]})
        for value in samples:
            with self.subTest(value=value):
                self.assertFalse(checker.scan_content(json.dumps(value))[0])
                with self.assertRaises(ValueError):
                    scan_safe(checker, value)
        scan_safe(checker, {'baseline': 5, 'candidate': 1, 'success': True})

    def test_numeric_sensitive_data_is_blocked_at_all_learning_boundaries(self):
        # Explicit test-only policy constructs a legacy unsafe fixture so the
        # default policy can be exercised on observations, restart and import.
        class LegacyFixturePolicy:
            def scan_content(self, content):
                return True, []

        for values in ({'password': 2468}, {'nested': [{'phone': 2025550123}]}):
            with self.subTest(values=values), TemporaryDirectory() as directory:
                consumer = governed()
                with self.assertRaises(ValueError):
                    consumer.learn_market_behavior('us-en', values)
                self.assertEqual(consumer.patterns, {})
                producer = governed(data_dir=directory, security_checker=LegacyFixturePolicy())
                producer.learn_market_behavior('us-en', values)
                evidence(producer)
                lesson = producer.draft_lesson(next(iter(producer.patterns)), 'Verify sources.', ['task-1'])
                producer.review_skill(lesson['skill_id'], 1, reviewer='human:alice', decision='approve')
                bundle = Path(directory) / 'legacy-fixture.json'
                producer.export_patterns(str(bundle))
                with self.assertRaises(ValueError):
                    governed(data_dir=directory)
                with self.assertRaises(ValueError):
                    consumer.import_patterns(str(bundle))
                self.assertEqual(consumer.patterns, {})
                assert consumer.registry is not None
                self.assertEqual(consumer.registry.list_skills(), [])

    def test_non_json_containers_cannot_bypass_observation_screening(self):
        from skill_registry import scan_safe
        from security_checker import SecurityChecker
        secret = 'sk-proj-' + 'A' * 24
        for value in ({'nested': (secret,)}, {'nested': ('safe text',)}):
            with self.subTest(kind='tuple'):
                with self.assertRaises(ValueError):
                    scan_safe(SecurityChecker(), value)
        with TemporaryDirectory() as directory:
            adapter = governed(data_dir=directory)
            with self.assertRaises(ValueError):
                adapter.learn_market_behavior('us-en', {'nested': (secret,)})
            self.assertEqual(adapter.patterns, {})
            self.assertFalse((Path(directory) / 'registry.json').exists())


class ReviewedLifecycleTests(unittest.TestCase):
    def test_malformed_or_replayed_evidence_cannot_support_approval(self):
        invalid = [dict(task_id=""), dict(source_ref=""), dict(result_ref=""),
                   dict(metric=""), dict(direction="up"), dict(success="yes"),
                   dict(baseline=True), dict(candidate=float("nan")),
                   dict(baseline=float("inf")), dict(candidate="1")]
        for changes in invalid:
            with self.subTest(changes=changes):
                with self.assertRaises(ValueError):
                    evidence(governed(), **changes)
        adapter = governed()
        evidence(adapter)
        with self.assertRaises(ValueError):
            evidence(adapter)
        with self.assertRaises(ValueError):
            adapter.observe_access("us-en", "team", "write")
            adapter.draft_lesson(next(iter(adapter.patterns)), "Lesson", ["task-1", "task-1"])

    def test_evidence_replay_cannot_be_renamed_or_overflow_comparison(self):
        adapter = governed()
        evidence(adapter)
        invalid = [dict(task_id=[]), dict(task_id={}), dict(baseline=10 ** 1000),
                   dict(baseline=-1e308, candidate=1e308)]
        for changes in invalid:
            with self.subTest(changes=changes):
                with self.assertRaises(ValueError):
                    evidence(governed(), **changes)
        with self.assertRaises(ValueError):
            evidence(adapter, task="task-2", source_ref="run://task-1", result_ref="report://task-1")

    def test_unverified_failed_or_nonimproving_tasks_cannot_be_approved(self):
        for changes in (dict(success=False), dict(candidate=7), dict(candidate=5)):
            adapter = governed()
            evidence(adapter, **changes)
            revision = draft(adapter)
            with self.assertRaises(ValueError):
                adapter.review_skill(revision["skill_id"], 1, reviewer="human:alice", decision="approve")
            self.assertEqual(adapter.get_adaptive_recommendations("us-en", {"action": "write", "success": True}), [])
        adapter = governed()
        adapter.record_outcome(task_id="task-1", source_ref="run://one", result_ref="report://one",
                               metric="quality", baseline=1, candidate=2, direction="higher", success=True)
        revision = draft(adapter)
        with self.assertRaises(PermissionError):
            adapter.verify_outcome("task-1", validator="agent:writer")
        with self.assertRaises(ValueError):
            adapter.review_skill(revision["skill_id"], 1, reviewer="human:alice", decision="approve")

    def test_reject_revoke_edit_and_rollback_require_new_reviews(self):
        adapter = governed()
        evidence(adapter)
        first = draft(adapter)
        sid = first["skill_id"]
        adapter.review_skill(sid, 1, reviewer="human:alice", decision="reject")
        with self.assertRaises(ValueError):
            adapter.review_skill(sid, 1, reviewer="human:alice", decision="approve")
        second = draft(adapter, skill_id=sid)
        self.assertEqual(second["revision"], 2)
        adapter.review_skill(sid, 2, reviewer="human:alice", decision="approve")
        # Returned objects and legacy public dictionaries are never authoritative.
        second["content"] = "Bypass review"
        second["state"] = "approved"
        third = draft(adapter, skill_id=sid)
        self.assertNotEqual(second["digest"], third["digest"])
        self.assertEqual(adapter.get_adaptive_recommendations("us-en", {"action": "write", "success": True}), [])
        adapter.review_skill(sid, 3, reviewer="human:alice", decision="approve")
        adapter.review_skill(sid, 3, reviewer="human:alice", decision="revoke")
        self.assertEqual(adapter.get_adaptive_recommendations("us-en", {"action": "write", "success": True}), [])
        rollback = adapter.rollback_skill(sid, 2, reviewer="human:alice")
        self.assertEqual(rollback["revision"], 4)
        self.assertEqual(rollback["state"], "pending")
        self.assertEqual(rollback["content"], first["content"])
        adapter.review_skill(sid, 4, reviewer="human:alice", decision="approve")
        reused = adapter.get_adaptive_recommendations("us-en", {"action": "write", "success": True})
        reused[0]["content"] = "tampered"
        self.assertEqual(adapter.registry.get_revision(sid, 4)["content"], first["content"])
        self.assertEqual(adapter.registry.get_revision(sid, 1)["state"], "rejected")
        self.assertEqual(adapter.registry.get_revision(sid, 3)["state"], "revoked")
        with self.assertRaises(ValueError):
            adapter.review_skill(sid, 0, reviewer="human:alice", decision="approve")

    def test_draft_rejects_malformed_explicit_identifiers(self):
        adapter = governed()
        evidence(adapter)
        for skill_id in ("", [], {}, 42):
            with self.subTest(skill_id=skill_id):
                with self.assertRaises(ValueError):
                    draft(adapter, skill_id=skill_id)

    def test_verified_outcome_then_human_approval_allows_reuse(self):
        adapter = governed()
        evidence(adapter)
        revision = draft(adapter)
        self.assertEqual(revision["state"], "pending")
        self.assertEqual(adapter.get_adaptive_recommendations("us-en", {"action": "write", "success": True}), [])
        with self.assertRaises(PermissionError):
            adapter.review_skill(revision["skill_id"], 1, reviewer="agent:writer", decision="approve")
        approved = adapter.review_skill(revision["skill_id"], 1,
                                        reviewer="human:alice", decision="approve")
        self.assertEqual(approved["review"]["reviewer"], "human:alice")
        self.assertTrue(approved["review"]["at"])
        self.assertEqual(approved["review"]["digest"], approved["digest"])
        reused = adapter.get_adaptive_recommendations("us-en", {"action": "write", "success": True})
        self.assertEqual(len(reused), 1)
        self.assertEqual(reused[0]["content"], "Check citations before delivery.")
        self.assertEqual(reused[0]["evidence"][0]["verification"]["validator"], "runner:qa")
        self.assertEqual(adapter.get_learning_summary()["rules"], 1)
        self.assertEqual(adapter.get_learning_summary()["skills_by_state"], {"approved": 1})


class PersistenceTests(unittest.TestCase):
    def test_persisted_tampering_is_rejected_before_reuse(self):
        from skill_registry import digest
        for change in ("content", "approval", "evidence", "state", "verification", "secret"):
            with self.subTest(change=change), TemporaryDirectory() as root:
                adapter = governed(data_dir=root)
                evidence(adapter)
                first = draft(adapter)
                adapter.review_skill(first["skill_id"], 1, reviewer="human:alice", decision="approve")
                path = Path(root) / "registry.json"
                saved = json.loads(path.read_text())
                entry = saved["skills"][first["skill_id"]][0]
                if change == "content":
                    entry["artifact"]["content"] = "Unchecked edit"
                    entry["digest"] = digest(entry["artifact"])
                elif change == "approval":
                    entry["review"]["reviewer"] = "agent:writer"
                elif change == "evidence":
                    entry["artifact"]["evidence"][0]["candidate"] = float("nan")
                elif change == "verification":
                    saved["evidence"]["task-1"]["verification"]["digest"] = "forged"
                elif change == "secret":
                    entry["artifact"]["content"] = "password=not-a-real-secret"
                else:
                    entry["state"] = "pending"
                # This checksum is integrity detection, deliberately NOT authentication.
                if change != "evidence":
                    saved["integrity"] = digest({k: v for k, v in saved.items() if k != "integrity"})
                path.write_text(json.dumps(saved))
                with self.assertRaises(ValueError):
                    governed(data_dir=root)

    def test_default_scanner_blocks_secret_content_evidence_and_observations(self):
        with TemporaryDirectory() as root:
            adapter = governed(data_dir=root)
            with self.assertRaises(ValueError):
                evidence(adapter, result_ref="password=not-a-real-secret")
            evidence(adapter)
            with self.assertRaises(ValueError):
                adapter.learn_market_behavior("us-en", {"api_key": "not-a-real-secret"})
            adapter.observe_access("us-en", "team", "write")
            with self.assertRaises(ValueError):
                adapter.draft_lesson(next(iter(adapter.patterns)), "password=not-a-real-secret", ["task-1"])
            self.assertNotIn("not-a-real-secret", (Path(root) / "registry.json").read_text())

    def test_unprotected_or_symlinked_store_is_not_trusted(self):
        with TemporaryDirectory() as root:
            path = Path(root) / "unsafe"
            path.mkdir(mode=0o777)
            path.chmod(0o777)
            with self.assertRaises(PermissionError):
                governed(data_dir=path)
            link = Path(root) / "link"
            link.symlink_to(path, target_is_directory=True)
            with self.assertRaises(PermissionError):
                governed(data_dir=link)

    def test_stale_instance_cannot_reuse_or_overwrite_a_revocation(self):
        with TemporaryDirectory() as root:
            owner = governed(data_dir=root)
            evidence(owner)
            first = draft(owner)
            sid = first["skill_id"]
            owner.review_skill(sid, 1, reviewer="human:alice", decision="approve")
            stale = governed(data_dir=root)
            owner.review_skill(sid, 1, reviewer="human:alice", decision="revoke")
            with self.assertRaises(ValueError):
                stale.get_adaptive_recommendations("us-en", {"action": "write", "success": True})
            with self.assertRaises(ValueError):
                stale.reuse_skill(sid, 1, task_id="task-2")
            with self.assertRaises(ValueError):
                evidence(stale, task="task-3")
            self.assertEqual(governed(data_dir=root).registry.get_revision(sid, 1)["state"], "revoked")

    def test_disk_failure_does_not_activate_in_memory_or_on_restart(self):
        from unittest.mock import patch
        with TemporaryDirectory() as root:
            adapter = governed(data_dir=root)
            evidence(adapter)
            first = draft(adapter)
            with patch("skill_registry.os.replace", side_effect=OSError("disk unavailable")):
                with self.assertRaises(OSError):
                    adapter.review_skill(first["skill_id"], 1, reviewer="human:alice", decision="approve")
            self.assertEqual(adapter.registry.get_revision(first["skill_id"], 1)["state"], "pending")
            self.assertEqual(governed(data_dir=root).registry.get_revision(first["skill_id"], 1)["state"], "pending")

    def test_restart_preserves_approved_versions_and_revocations(self):
        with TemporaryDirectory() as root:
            directory = Path(root) / "registry"
            adapter = governed(data_dir=directory)
            evidence(adapter)
            first = draft(adapter)
            adapter.review_skill(first["skill_id"], 1, reviewer="human:alice", decision="approve")
            restarted = governed(data_dir=directory)
            self.assertEqual(restarted.get_adaptive_recommendations("us-en", {"action": "write", "success": True})[0]["digest"], first["digest"])
            with self.assertRaises(ValueError):
                evidence(restarted)
            restarted.review_skill(first["skill_id"], 1, reviewer="human:alice", decision="revoke")
            again = governed(data_dir=directory)
            self.assertEqual(again.get_adaptive_recommendations("us-en", {"action": "write", "success": True}), [])
            self.assertEqual(again.registry.get_revision(first["skill_id"], 1)["state"], "revoked")
            self.assertEqual(directory.stat().st_mode & 0o777, 0o700)
            self.assertEqual((directory / "registry.json").stat().st_mode & 0o777, 0o600)

    def test_failed_promotion_is_never_persisted_as_active(self):
        with TemporaryDirectory() as root:
            adapter = governed(data_dir=root)
            evidence(adapter, success=False)
            first = draft(adapter)
            with self.assertRaises(ValueError):
                adapter.review_skill(first["skill_id"], 1, reviewer="human:alice", decision="approve")
            restarted = governed(data_dir=root)
            self.assertEqual(restarted.registry.get_revision(first["skill_id"], 1)["state"], "pending")
            self.assertEqual(restarted.get_adaptive_recommendations("us-en", {"action": "write", "success": True}), [])


class ImportIsolationTests(unittest.TestCase):
    def test_imported_approvals_and_verifications_are_untrusted_drafts(self):
        with TemporaryDirectory() as root:
            original = governed()
            evidence(original)
            first = draft(original)
            original.review_skill(first["skill_id"], 1, reviewer="human:alice", decision="approve")
            bundle = Path(root) / "export.json"
            original.export_patterns(str(bundle))
            target = governed(data_dir=Path(root) / "target")
            self.assertTrue(target.import_patterns(str(bundle)))
            self.assertEqual(target.get_adaptive_recommendations("us-en", {"action": "write", "success": True}), [])
            imported = target.registry.list_skills()[0]
            self.assertEqual(imported["state"], "pending")
            self.assertIsNone(imported["evidence"][0]["verification"])
            with self.assertRaises(ValueError):
                target.review_skill(imported["skill_id"], 1, reviewer="human:alice", decision="approve")
            target.verify_outcome("task-1", validator="runner:qa")
            revised = target.revise_skill(imported["skill_id"], "Check citations before delivery.")
            target.review_skill(revised["skill_id"], 2, reviewer="human:alice", decision="approve")
            self.assertEqual(len(target.get_adaptive_recommendations("us-en", {"action": "write", "success": True})), 1)

    def test_cross_scope_or_unscoped_imports_fail_without_partial_effects(self):
        with TemporaryDirectory() as root:
            original = governed()
            evidence(original)
            first = draft(original)
            bundle = Path(root) / "export.json"
            original.export_patterns(str(bundle))
            data = json.loads(bundle.read_text())
            for field in ("tenant", "brand", "team", "user"):
                foreign = json.loads(json.dumps(data))
                foreign["scope"][field] = "other"
                bundle.write_text(json.dumps(foreign))
                target = governed()
                with self.assertRaises(ValueError):
                    target.import_patterns(str(bundle))
                self.assertEqual(target.registry.list_skills(), [])
                self.assertEqual(target.patterns, {})
            bundle.write_text(json.dumps(data))
            with self.assertRaises(PermissionError):
                HermesAdapter().import_patterns(str(bundle))

    def test_import_validation_is_atomic_and_checks_each_skill_scope(self):
        with TemporaryDirectory() as root:
            original = governed()
            evidence(original)
            draft(original)
            bundle = Path(root) / "export.json"
            original.export_patterns(str(bundle))
            data = json.loads(bundle.read_text())
            foreign = json.loads(json.dumps(data["skills"][0]))
            foreign["skill_id"] = "foreign-skill"
            foreign["scope"]["brand"] = "other"
            data["skills"].append(foreign)
            bundle.write_text(json.dumps(data))
            target = governed(data_dir=Path(root) / "target")
            with self.assertRaises(ValueError):
                target.import_patterns(str(bundle))
            self.assertEqual(target.registry.list_skills(), [])
            self.assertEqual(target.patterns, {})
            self.assertFalse((Path(root) / "target" / "registry.json").exists())
            data["skills"].pop()
            data["skills"][0]["evidence"][0]["candidate"] = float("nan")
            bundle.write_text(json.dumps(data))
            with self.assertRaises(ValueError):
                target.import_patterns(str(bundle))

    def test_public_mutation_cannot_create_a_reusable_rule(self):
        adapter = governed()
        adapter.observe_access("us-en", "team", "write")
        pattern = next(iter(adapter.patterns.values()))
        pattern.confidence = 1.0
        self.assertFalse(adapter._generate_adaptive_rule(pattern))
        from hermes_adapter import AdaptationRule
        adapter.adaptation_rules["forged"] = AdaptationRule("forged", "access", "us-en", {}, {})
        self.assertEqual(adapter.get_adaptive_recommendations("us-en", {}), [])
        with self.assertRaises(PermissionError):
            HermesAdapter().record_outcome(task_id="missing-scope")


class ReuseComparisonTests(unittest.TestCase):
    def test_reuse_is_version_bound_then_measured_not_self_promoted(self):
        with TemporaryDirectory() as root:
            adapter = governed(data_dir=root)
            evidence(adapter)
            first = draft(adapter)
            sid = first["skill_id"]
            with self.assertRaises(ValueError):
                adapter.reuse_skill(sid, 1, task_id="task-2")
            adapter.review_skill(sid, 1, reviewer="human:alice", decision="approve")
            receipt = adapter.reuse_skill(sid, 1, task_id="task-2")
            self.assertEqual(receipt["digest"], first["digest"])
            with self.assertRaises(ValueError):
                adapter.reuse_skill(sid, 1, task_id="task-2")
            adapter.record_reuse_outcome(task_id="task-2", source_ref="run://two",
                                        result_ref="report://two", metric="defects",
                                        baseline=5, candidate=8, direction="lower", success=False)
            comparison = adapter.compare_outcome("task-2")
            self.assertIsNone(comparison["improved"])
            adapter.verify_outcome("task-2", validator="runner:qa")
            comparison = adapter.compare_outcome("task-2")
            self.assertFalse(comparison["improved"])
            self.assertEqual(comparison["delta"], 3)
            self.assertEqual(comparison["skill_id"], sid)
            self.assertEqual(comparison["revision"], 1)
            restarted = governed(data_dir=root)
            self.assertEqual(restarted.compare_outcome("task-2"), comparison)
            self.assertEqual(restarted.registry.get_revision(sid, 1)["digest"], first["digest"])
            self.assertEqual(len(restarted.registry.list_skills()), 1)
            revised = restarted.revise_skill(sid, "Changed procedure.")
            self.assertEqual(revised["revision"], 2)
            with self.assertRaises(ValueError):
                restarted.reuse_skill(sid, 1, task_id="task-3")
            with self.assertRaises(ValueError):
                restarted.record_reuse_outcome(task_id="task-unknown", source_ref="run://three",
                                              result_ref="report://three", metric="defects",
                                              baseline=5, candidate=1, direction="lower", success=True)


class ObservationTests(unittest.TestCase):
    def test_repeated_failures_never_establish_correctness_or_reuse(self):
        adapter = HermesAdapter()
        adapter.set_learning_mode(LearningMode.OPTIMIZATION)
        for _ in range(30):
            adapter.observe_access("us-en", "team", "publish", False)
        pattern = next(iter(adapter.patterns.values()))
        self.assertEqual(pattern.occurrences, 30)
        self.assertEqual(pattern.confidence, 0.0)
        self.assertEqual(adapter.get_adaptive_recommendations("us-en", {}), [])
        self.assertEqual(adapter.get_learning_summary()["rules"], 0)


if __name__ == "__main__":
    unittest.main()
