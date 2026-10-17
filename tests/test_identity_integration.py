"""Optional integration tests; every identity/approval below is a SYNTHETIC FIXTURE."""
import importlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

try:
    import jwt
    from cryptography.hazmat.primitives.asymmetric import rsa
except ImportError:
    jwt = None


ISSUER = "https://synthetic-idp.invalid"
AUDIENCE = "atlas-callback-fixture"


@unittest.skipIf(jwt is None, "install integrations/requirements-oidc.txt for mandatory identity suite")
class IdentityIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

    def module(self):
        try:
            return importlib.import_module("integrations.trusted_identity")
        except ModuleNotFoundError:
            self.fail("trusted identity integration module is not implemented")

    def token(self, trusted_nonce, subject="fixture-author", **changes):
        now = int(time.time())
        claims = dict(iss=ISSUER, aud=AUDIENCE, sub=subject, iat=now, exp=now + 240, nonce=trusted_nonce)
        claims.update(changes)
        return jwt.encode(claims, self.key, algorithm="RS256", headers={"kid": "fixture-rsa"})

    def verifier(self):
        return self.module().CallbackVerifier(issuer=ISSUER, audience=AUDIENCE,
                                               public_keys={"fixture-rsa": self.key.public_key()})

    def test_callback_verifies_real_rs256_and_returns_only_issuer_subject(self):
        verifier = self.verifier()
        pending = verifier.begin_login()
        identity = verifier.complete_login(pending.handle, self.token(
            pending.nonce, tenant="attacker", roles=["reviewer"], owner="attacker"))
        self.assertEqual((identity.issuer, identity.subject), (ISSUER, "fixture-author"))
        self.assertFalse(hasattr(identity, "roles"))
        self.assertFalse(hasattr(identity, "tenant"))
        self.assertFalse(hasattr(identity, "token"))

    def test_nonce_is_trusted_one_time_and_pending_login_expires(self):
        verifier = self.verifier()
        pending = verifier.begin_login()
        raw = self.token(pending.nonce)
        verifier.complete_login(pending.handle, raw)
        with self.assertRaises(PermissionError):
            verifier.complete_login(pending.handle, raw)
        pending = verifier.begin_login()
        with self.assertRaises(PermissionError):
            verifier.complete_login(pending.handle, self.token("attacker-nonce"))
        # A failed callback consumes the pending login too.
        with self.assertRaises(PermissionError):
            verifier.complete_login(pending.handle, self.token(pending.nonce))
        with self.assertRaises(PermissionError):
            verifier.complete_login("caller-invented", raw)
        pending = verifier.begin_login()
        raw = self.token(pending.nonce)
        with patch("integrations.trusted_identity.time.time", return_value=time.time() + 301):
            with self.assertRaises(PermissionError):
                verifier.complete_login(pending.handle, raw)

    def test_callback_rejects_forgery_algorithm_confusion_and_untrusted_key_sources(self):
        verifier = self.verifier()
        rogue = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        now = int(time.time())
        for attack in ("rogue-signature", "unsigned", "hs256", "jku", "jwk", "x5u", "crit", "unknown-kid"):
            with self.subTest(attack=attack):
                pending = verifier.begin_login()
                claims = dict(iss=ISSUER, sub="fixture-author", aud=AUDIENCE,
                              iat=now, exp=now + 240, nonce=pending.nonce)
                headers = {"kid": "fixture-rsa"}
                key, algorithm = self.key, "RS256"
                if attack == "rogue-signature":
                    key = rogue
                elif attack == "unsigned":
                    key, algorithm = None, "none"
                elif attack == "hs256":
                    key, algorithm = b"synthetic-hmac-fixture-not-an-rsa-key", "HS256"
                elif attack == "unknown-kid":
                    headers["kid"] = "../attacker"
                else:
                    headers[attack] = (["attacker"] if attack == "crit" else
                                       {"kty": "RSA"} if attack == "jwk" else "https://attacker.invalid/keys")
                raw = jwt.encode(claims, key, algorithm=algorithm, headers=headers)
                with self.assertRaisesRegex(PermissionError, "^login rejected$"):
                    verifier.complete_login(pending.handle, raw)

    def test_callback_rejects_wrong_claims_and_stale_id_tokens(self):
        verifier = self.verifier()
        now = int(time.time())
        invalid = ({"iss": "https://attacker.invalid"}, {"aud": "foreign-app"},
                   {"aud": [AUDIENCE, "foreign-app"]}, {"sub": ""}, {"sub": 42},
                   {"iat": now + 60}, {"iat": now - 301}, {"iat": str(now)},
                   {"exp": now - 1}, {"exp": str(now + 240)}, {"exp": now + 3600},
                   {"nonce": None}, {"nonce": 42}, {"azp": "foreign-app"},
                   {"nbf": True})
        for index, changes in enumerate(invalid):
            with self.subTest(case=index):
                pending = verifier.begin_login()
                with self.assertRaisesRegex(PermissionError, "^login rejected$"):
                    verifier.complete_login(pending.handle, self.token(pending.nonce, **changes))
        for claim in ("iss", "aud", "sub", "iat", "exp", "nonce"):
            pending = verifier.begin_login()
            claims = dict(iss=ISSUER, sub="fixture-author", aud=AUDIENCE,
                          iat=now, exp=now + 240, nonce=pending.nonce)
            del claims[claim]
            with self.subTest(missing=claim), self.assertRaises(PermissionError):
                verifier.complete_login(pending.handle, jwt.encode(
                    claims, self.key, algorithm="RS256", headers={"kid": "fixture-rsa"}))
        for raw in ("not-a-jwt", "x" * 20000, None, {}):
            pending = verifier.begin_login()
            with self.assertRaises(PermissionError):
                verifier.complete_login(pending.handle, raw)

    def policy(self):
        m = self.module()
        users = {m.Identity(ISSUER, "fixture-" + name): "fixture-" + name
                 for name in ("author", "verifier", "reviewer", "consumer", "outsider")}
        grants = {(m.Identity(ISSUER, "fixture-" + role), "shared"): frozenset({role})
                  for role in ("author", "verifier", "reviewer", "consumer")}
        return m.ServerPolicy(users=users, grants=grants)

    def service(self, directory, policy=None):
        m = self.module()
        self.assertTrue(hasattr(m, "TeamService"), "role-gated team facade is missing")
        resource = m.TeamResource("acme", "atlas", "marketing", "content", "team-library")
        return m.TeamService(verifier=self.verifier(), policy=policy or self.policy(),
                             resources={"shared": resource}, storage_root=directory)

    def login(self, service, role, **claims):
        pending = service.begin_login()
        return service.login(pending.handle, self.token(pending.nonce, "fixture-" + role, **claims))

    def record(self, service, session, **changes):
        fields = dict(task_id="fixture-task", source_ref="fixture://baseline",
                      result_ref="fixture://candidate", metric="defects", baseline=5,
                      candidate=1, direction="lower", success=True)
        fields.update(changes)
        return service.record_outcome(session, "shared", **fields)

    def approved(self, service):
        author = self.login(service, "author")
        self.record(service, author)
        service.verify_outcome(self.login(service, "verifier"), "shared", "fixture-task")
        draft = service.draft(author, "shared", content="Verify citations before delivery.",
                              task_ids=["fixture-task"], market_code="us-en", condition={"action": "write"},
                              skill_id="fixture-skill")
        service.review(self.login(service, "reviewer"), "shared", draft["skill_id"], 1, decision="approve")
        return draft

    def test_authorized_second_user_reuses_same_resource_after_fresh_instance(self):
        with tempfile.TemporaryDirectory() as directory:
            service = self.service(directory)
            draft = self.approved(service)
            restarted = self.service(directory)
            consumer = self.login(restarted, "consumer")
            lessons = restarted.recommendations(consumer, "shared", "us-en", {"action": "write"})
            self.assertEqual([item["digest"] for item in lessons], [draft["digest"]])
            self.assertEqual(lessons[0]["scope"]["user"], "team-library")
            self.assertEqual(lessons[0]["review"]["reviewer"], "fixture-reviewer")
            receipt = restarted.reuse(consumer, "shared", "fixture-skill", 1, task_id="fixture-reuse")
            self.assertEqual(receipt["digest"], draft["digest"])
            self.assertEqual(receipt["actor"], "fixture-consumer")
            self.assertFalse(hasattr(restarted, "registry"))
            self.assertFalse(hasattr(restarted, "adapter"))
            snapshot = next(Path(directory).rglob("registry.json"))
            stored = json.loads(snapshot.read_text())
            self.assertEqual(stored["scope"]["user"], "team-library")
            self.assertEqual(len(stored["skills"]), 1)
            self.assertNotIn("eyJ", snapshot.read_text())

    def test_membership_removal_denies_existing_session_on_the_next_operation(self):
        m = self.module()
        policy = self.policy()
        self.assertTrue(hasattr(policy, "set_roles"), "trusted membership update API is missing")
        with tempfile.TemporaryDirectory() as directory:
            service = self.service(directory, policy)
            self.approved(service)
            session = self.login(service, "consumer")
            self.assertEqual(len(service.recommendations(session, "shared", "us-en", {"action": "write"})), 1)
            policy.set_roles(m.Identity(ISSUER, "fixture-consumer"), "shared", frozenset())
            with patch("integrations.trusted_identity.SkillRegistry") as opened:
                with self.assertRaises(PermissionError):
                    service.recommendations(session, "shared", "us-en", {"action": "write"})
                with self.assertRaises(PermissionError):
                    service.reuse(session, "shared", "fixture-skill", 1, task_id="denied-reuse")
                opened.assert_not_called()

    def test_invalid_trusted_configuration_fails_closed(self):
        m = self.module()
        for changes in ({"issuer": "http://insecure.invalid"}, {"issuer": ""}, {"audience": ""},
                        {"public_keys": {}}, {"public_keys": {"fixture-rsa": b"not-rsa"}},
                        {"public_keys": {"fixture-rsa": self.key}}):
            fields = dict(issuer=ISSUER, audience=AUDIENCE, public_keys={"fixture-rsa": self.key.public_key()})
            fields.update(changes)
            with self.subTest(config=next(iter(changes))), self.assertRaises(ValueError):
                m.CallbackVerifier(**fields)
        identity = m.Identity(ISSUER, "fixture-author")
        with self.assertRaises(ValueError):
            m.ServerPolicy(users={identity: "../owner"}, grants={})
        with self.assertRaises(ValueError):
            m.ServerPolicy(users={identity: "same", m.Identity(ISSUER, "other"): "same"}, grants={})
        policy = self.policy()
        for roles in ("reviewer", {"administrator"}, {"consumer", "reviewer-claimed"}):
            with self.assertRaises(ValueError):
                policy.set_roles(identity, "shared", roles)
        with self.assertRaises(ValueError):
            policy.set_roles(m.Identity(ISSUER, "unknown"), "shared", {"consumer"})
        with self.assertRaises(ValueError):
            m.TeamResource("../acme", "atlas", "marketing", "content", "team-library")

    def test_untrusted_claims_and_forged_sessions_cannot_grant_any_operation(self):
        with tempfile.TemporaryDirectory() as directory:
            service = self.service(directory)
            self.approved(service)
            outsider = self.login(service, "outsider", roles=["author", "verifier", "reviewer", "consumer"],
                                  tenant="acme", brand="atlas", team="content", owner="team-library",
                                  reviewer="fixture-reviewer", user="fixture-reviewer")
            calls = [lambda s: self.record(service, s),
                     lambda s: service.verify_outcome(s, "shared", "fixture-task"),
                     lambda s: service.draft(s, "shared", content="Read citations.", task_ids=["fixture-task"],
                                             market_code="us-en", condition={}),
                     lambda s: service.review(s, "shared", "fixture-skill", 1, decision="approve"),
                     lambda s: service.recommendations(s, "shared", "us-en", {}),
                     lambda s: service.reuse(s, "shared", "fixture-skill", 1, task_id="denied")]
            with patch("pathlib.Path.read_text", side_effect=AssertionError("read before authorization")):
                for session in (outsider, "invented-session", self.token("not-a-login"), {},
                                self.module().Identity(ISSUER, "fixture-reviewer")):
                    for operation, call in enumerate(calls):
                        with self.subTest(operation=operation), self.assertRaises(PermissionError):
                            call(session)
            author = self.login(service, "author", roles=["reviewer", "verifier"])
            consumer = self.login(service, "consumer", roles=["author"])
            with patch("integrations.trusted_identity.SkillRegistry") as opened:
                for call in (lambda: service.review(author, "shared", "fixture-skill", 1, decision="approve"),
                             lambda: service.verify_outcome(author, "shared", "fixture-task"),
                             lambda: self.record(service, consumer)):
                    with self.assertRaises(PermissionError):
                        call()
                with self.assertRaises(TypeError):
                    service.review(author, "shared", "fixture-skill", 1, decision="approve",
                                   reviewer="fixture-reviewer")
                opened.assert_not_called()
            with patch("integrations.trusted_identity.time.time", return_value=time.time() + 301):
                with self.assertRaises(PermissionError):
                    service.recommendations(consumer, "shared", "us-en", {})

    def test_foreign_tenant_brand_and_department_with_same_team_are_isolated(self):
        m = self.module()
        with tempfile.TemporaryDirectory() as directory:
            local_policy = self.policy()
            resources = {"shared": m.TeamResource("acme", "atlas", "marketing", "content", "team-library"),
                         "foreign-tenant": m.TeamResource("other", "atlas", "marketing", "content", "team-library"),
                         "foreign-brand": m.TeamResource("acme", "other", "marketing", "content", "team-library"),
                         "foreign-department": m.TeamResource("acme", "atlas", "other", "content", "team-library")}
            users, grants = dict(local_policy._users), dict(local_policy._grants)
            for resource_id in resources:
                if resource_id != "shared":
                    identity = m.Identity(ISSUER, "fixture-" + resource_id)
                    users[identity] = "fixture-" + resource_id
                    grants[(identity, resource_id)] = frozenset({"consumer"})
            service = m.TeamService(verifier=self.verifier(), policy=m.ServerPolicy(users=users, grants=grants),
                                    resources=resources, storage_root=directory)
            self.approved(service)
            consumer = self.login(service, "consumer", tenant="other", brand="other", team="content")
            for resource_id in resources:
                if resource_id == "shared":
                    continue
                foreign = self.login(service, resource_id, roles=["reviewer"], tenant="acme")
                with patch("pathlib.Path.read_text", side_effect=AssertionError("foreign read")):
                    with self.assertRaises(PermissionError):
                        service.recommendations(consumer, resource_id, "us-en", {})
                    with self.assertRaises(PermissionError):
                        service.recommendations(foreign, "shared", "us-en", {})
                self.assertEqual(service.recommendations(foreign, resource_id, "us-en", {}), [])
            self.assertEqual(len(service.recommendations(consumer, "shared", "us-en", {"action": "write"})), 1)
            with patch("pathlib.Path.read_text", side_effect=AssertionError("path read")):
                for resource_id in ("../shared", "/shared", "missing", {"owner": "team-library"}):
                    with self.assertRaises(PermissionError):
                        service.recommendations(consumer, resource_id, "us-en", {})

    def test_symlinked_or_unprotected_storage_parents_are_denied_before_read(self):
        for depth in range(6):
            with self.subTest(depth=depth), tempfile.TemporaryDirectory() as directory:
                root = Path(directory) / "store"
                root.mkdir(mode=0o700)
                service = self.service(root)
                self.approved(service)
                consumer = self.login(service, "consumer")
                path = root.joinpath(*("acme", "atlas", "marketing", "content", "team-library")[:depth])
                detached = path.with_name(path.name + "-detached")
                path.rename(detached)
                path.symlink_to(detached, target_is_directory=True)
                with patch("pathlib.Path.read_text", side_effect=AssertionError("read through symlink")):
                    with self.assertRaises(PermissionError):
                        service.recommendations(consumer, "shared", "us-en", {})
        with tempfile.TemporaryDirectory() as directory:
            service = self.service(directory)
            self.approved(service)
            consumer = self.login(service, "consumer")
            (Path(directory) / "acme").chmod(0o755)
            with patch("pathlib.Path.read_text", side_effect=AssertionError("read unprotected path")):
                with self.assertRaises(PermissionError):
                    service.recommendations(consumer, "shared", "us-en", {})

    def test_real_core_scanner_and_transport_credential_screening_are_enforced(self):
        with tempfile.TemporaryDirectory() as directory:
            service = self.service(directory)
            author = self.login(service, "author")
            raw = self.token("synthetic-not-a-callback")
            # No policy injection: these use the actual numeric-aware core scanner.
            for changes in ({"baseline": 2025550123}, {"result_ref": "password=fixture-secret"},
                            {"source_ref": raw}):
                with self.assertRaises(ValueError):
                    self.record(service, author, **changes)
            self.record(service, author)
            service.verify_outcome(self.login(service, "verifier"), "shared", "fixture-task")
            for content, condition in (("Verify citations.", {"password": 2468}),
                                       ("Verify citations.", {"nested": [2025550123]}),
                                       ("-----BEGIN PRIVATE KEY-----", {}), (raw, {})):
                with self.assertRaises(ValueError):
                    service.draft(author, "shared", content=content, condition=condition,
                                  task_ids=["fixture-task"], market_code="us-en")
            snapshots = list(Path(directory).rglob("registry.json"))
            self.assertEqual(len(snapshots), 1)
            self.assertNotIn(raw, snapshots[0].read_text())
            self.assertNotIn("fixture-secret", snapshots[0].read_text())
            safe = service.draft(author, "shared", content="Verify citations.", condition={},
                                 task_ids=["fixture-task"], market_code="us-en")
            service.review(self.login(service, "reviewer"), "shared", safe["skill_id"], 1, decision="approve")
            with self.assertRaises(ValueError):
                service.reuse(self.login(service, "consumer"), "shared", safe["skill_id"], 1, task_id=raw)
            self.assertNotIn(raw, snapshots[0].read_text())

    def test_cli_proves_real_subprocess_restart_with_machine_readable_evidence(self):
        root = Path(__file__).resolve().parents[1]
        demo = root / "examples" / "authenticated-team" / "demo.py"
        self.assertTrue(demo.is_file(), "runnable authenticated-team acceptance demo is missing")
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "evidence.json"
            run = subprocess.run([sys.executable, str(demo), "--evidence", str(output)],
                                 cwd=root, text=True, capture_output=True, timeout=45)
            self.assertEqual(run.returncode, 0, run.stderr)
            evidence = json.loads(output.read_text())
            self.assertEqual(json.loads(run.stdout), evidence)
            self.assertTrue(evidence["fixture_only"])
            self.assertFalse(evidence["external_idp_configured"])
            self.assertTrue(evidence["passed"])
            self.assertTrue(evidence["process_restart"]["verified"])
            self.assertTrue(evidence["process_restart"]["fresh_login_required"])
            self.assertIn("first_pid", evidence["process_restart"], "restart evidence must identify actual workers")
            self.assertNotEqual(evidence["process_restart"]["first_pid"], evidence["process_restart"]["second_pid"])
            self.assertEqual(evidence["process_restart"]["first_exit_code"], 0)
            self.assertEqual(evidence["process_restart"]["second_exit_code"], 0)
            self.assertTrue(evidence["checks"])
            self.assertTrue(all(evidence["checks"].values()))
            self.assertEqual(evidence["approval"]["digest"], evidence["reuse"]["digest"])
            self.assertEqual(evidence["approval"]["reviewer"], "fixture-reviewer")
            self.assertEqual(evidence["reuse"]["actor"], "fixture-consumer")
            self.assertEqual(evidence["resource_owner"], "team-library")
            self.assertEqual(output.stat().st_mode & 0o777, 0o600)
            self.assertNotIn("eyJ", run.stdout)
            self.assertNotIn("PRIVATE KEY", run.stdout + run.stderr)


if __name__ == "__main__":
    unittest.main()
