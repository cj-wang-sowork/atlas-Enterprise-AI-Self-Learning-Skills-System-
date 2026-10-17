#!/usr/bin/env python3
"""SYNTHETIC acceptance harness. No live IdP, web login, real people or credentials.

Private RSA material exists only in supervisor memory. Workers receive the pinned
public key and callback tokens over private process pipes, never argv/files/logs.
The worker protocol is a privileged test harness, NOT an HTTP/API deployment.
"""
import argparse
from contextlib import AbstractContextManager
import importlib.metadata
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from integrations.trusted_identity import CallbackVerifier, Identity, ServerPolicy, TeamResource, TeamService

ISSUER = "https://synthetic-idp.invalid"
AUDIENCE = "atlas-callback-fixture"


def fixture_service(directory, public_pem):
    """Server-owned fixture mappings; NEVER construct these from chat/token claims."""
    resources = {"shared": TeamResource("acme", "atlas", "marketing", "content", "team-library"),
                 "foreign-tenant": TeamResource("other", "atlas", "marketing", "content", "team-library"),
                 "foreign-brand": TeamResource("acme", "other", "marketing", "content", "team-library")}
    names = ("author", "verifier", "reviewer", "consumer", "outsider", "foreign-tenant", "foreign-brand")
    users = {Identity(ISSUER, "fixture-" + name): "fixture-" + name for name in names}
    grants = {(Identity(ISSUER, "fixture-" + role), "shared"): frozenset({role})
              for role in ("author", "verifier", "reviewer", "consumer")}
    for foreign in ("foreign-tenant", "foreign-brand"):
        grants[(Identity(ISSUER, "fixture-" + foreign), foreign)] = frozenset({"consumer"})
    policy = ServerPolicy(users=users, grants=grants)
    verifier = CallbackVerifier(issuer=ISSUER, audience=AUDIENCE,
                                public_keys={"fixture-rsa": serialization.load_pem_public_key(public_pem.encode())})
    return TeamService(verifier=verifier, policy=policy, resources=resources, storage_root=directory), policy


def worker(directory):
    initialization = json.loads(sys.stdin.readline())
    service, policy = fixture_service(directory, initialization["public_pem"])
    print(json.dumps({"ok": True, "pid": os.getpid()}), flush=True)
    allowed = {"begin_login", "login", "record_outcome", "verify_outcome", "draft", "review",
               "recommendations", "reuse"}
    for line in sys.stdin:
        request = json.loads(line)
        op = request["op"]
        if op == "quit":
            return
        try:
            if op == "fixture_remove_consumer":
                # Privileged fixture-only control, deliberately not on TeamService.
                policy.set_roles(Identity(ISSUER, "fixture-consumer"), "shared", frozenset())
                result = None
            elif op in allowed:
                result = getattr(service, op)(**request.get("args", {}))
                if op == "begin_login":
                    result = {"handle": result.handle, "nonce": result.nonce}
            else:
                raise PermissionError("unsupported operation")
            response = {"ok": True, "data": result}
        except (PermissionError, ValueError, TypeError) as exc:
            # No exception message/request echo: these can contain credentials.
            response = {"ok": False, "error": type(exc).__name__}
        print(json.dumps(response), flush=True)


class Worker(AbstractContextManager):
    def __init__(self, directory, public_pem):
        self.process = subprocess.Popen([sys.executable, __file__, "--worker", str(directory)],
                                        stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                        text=True, cwd=ROOT)
        self.process.stdin.write(json.dumps({"public_pem": public_pem}) + "\n")
        self.process.stdin.flush()
        ready = self._read()
        if not ready.get("ok"):
            raise RuntimeError("fixture worker failed to initialize")
        self.pid = ready["pid"]

    def _read(self):
        line = self.process.stdout.readline()
        if not line:
            raise RuntimeError("fixture worker exited without a response")
        return json.loads(line)

    def call(self, op, **args):
        self.process.stdin.write(json.dumps({"op": op, "args": args}) + "\n")
        self.process.stdin.flush()
        return self._read()

    def ok(self, op, **args):
        result = self.call(op, **args)
        if not result.get("ok"):
            raise AssertionError("expected fixture operation to succeed: " + op)
        return result["data"]

    def denied(self, op, *, error="PermissionError", **args):
        result = self.call(op, **args)
        if result != {"ok": False, "error": error}:
            raise AssertionError("expected fixture operation to be denied: " + op)
        return True

    def __exit__(self, exc_type, exc_value, traceback):
        try:
            self.process.stdin.write('{"op":"quit"}\n')
            self.process.stdin.flush()
            self.process.wait(timeout=10)
        finally:
            if self.process.poll() is None:
                self.process.kill()
                self.process.wait(timeout=10)
            self.process.stdin.close()
            self.process.stdout.close()
        if exc_type is None and self.process.returncode != 0:
            raise RuntimeError("fixture worker did not shut down successfully")


def signed(key, nonce, subject, **changes):
    now = int(time.time())
    claims = dict(iss=ISSUER, aud=AUDIENCE, sub="fixture-" + subject,
                  iat=now, exp=now + 240, nonce=nonce)
    claims.update(changes)
    return jwt.encode(claims, key, algorithm="RS256", headers={"kid": "fixture-rsa"})


def login(process, key, subject, **claims):
    pending = process.ok("begin_login")
    return process.ok("login", pending_handle=pending["handle"],
                      id_token=signed(key, pending["nonce"], subject, **claims))


def run_demo():
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_pem = key.public_key().public_bytes(serialization.Encoding.PEM,
                                              serialization.PublicFormat.SubjectPublicKeyInfo).decode()
    checks = {}
    with tempfile.TemporaryDirectory(prefix="atlas-identity-fixture-") as directory:
        with Worker(directory, public_pem) as first:
            first_pid = first.pid
            author = login(first, key, "author", roles=["reviewer"], tenant="attacker")
            verifier = login(first, key, "verifier")
            reviewer = login(first, key, "reviewer")
            consumer = login(first, key, "consumer")
            pending = first.ok("begin_login")
            rogue = rsa.generate_private_key(public_exponent=65537, key_size=2048)
            checks["forged_signature_denied"] = first.denied(
                "login", pending_handle=pending["handle"], id_token=signed(rogue, pending["nonce"], "reviewer"))
            pending = first.ok("begin_login")
            checks["wrong_nonce_denied"] = first.denied(
                "login", pending_handle=pending["handle"], id_token=signed(key, "attacker-nonce", "author"))
            pending = first.ok("begin_login")
            raw = signed(key, pending["nonce"], "author")
            first.ok("login", pending_handle=pending["handle"], id_token=raw)
            checks["nonce_replay_denied"] = first.denied(
                "login", pending_handle=pending["handle"], id_token=raw)
            outcome = dict(task_id="fixture-task", source_ref="fixture://baseline",
                           result_ref="fixture://candidate", metric="defects", baseline=5,
                           candidate=1, direction="lower", success=True)
            checks["unsafe_numeric_denied"] = first.denied(
                "record_outcome", error="ValueError", session=author, resource_id="shared",
                **{**outcome, "baseline": 2025550123})
            first.ok("record_outcome", session=author, resource_id="shared", **outcome)
            first.ok("verify_outcome", session=verifier, resource_id="shared", task_id="fixture-task")
            draft = first.ok("draft", session=author, resource_id="shared", content="Verify citations before delivery.",
                             task_ids=["fixture-task"], market_code="us-en", condition={"action": "write"},
                             skill_id="fixture-skill")
            checks["pending_not_reusable"] = first.denied(
                "reuse", error="ValueError", session=consumer, resource_id="shared",
                skill_id="fixture-skill", revision=1, task_id="fixture-too-early")
            checks["claimed_reviewer_denied"] = first.denied(
                "review", session=author, resource_id="shared", skill_id="fixture-skill", revision=1, decision="approve")
            approval = first.ok("review", session=reviewer, resource_id="shared",
                                skill_id="fixture-skill", revision=1, decision="approve")
        # The first process has EXITED. Re-open identical storage and pinned trust
        # in a new process; sessions/pending logins are deliberately not restored.
        with Worker(directory, public_pem) as second:
            checks["old_session_denied"] = second.denied(
                "record_outcome", session=author, resource_id="shared", **outcome)
            consumer = login(second, key, "consumer")
            lessons = second.ok("recommendations", session=consumer, resource_id="shared",
                                market_code="us-en", context={"action": "write"})
            if len(lessons) != 1 or lessons[0]["digest"] != draft["digest"]:
                raise AssertionError("approved skill not restored exactly")
            receipt = second.ok("reuse", session=consumer, resource_id="shared",
                                skill_id="fixture-skill", revision=1, task_id="fixture-reuse")
            if receipt["digest"] != approval["digest"] or receipt["actor"] != "fixture-consumer":
                raise AssertionError("cross-user receipt differs from approved artifact")
            outsider = login(second, key, "outsider", roles=["consumer", "reviewer"], owner="team-library")
            checks["unauthorized_user_denied"] = second.denied(
                "recommendations", session=outsider, resource_id="shared", market_code="us-en", context={})
            for foreign in ("foreign-tenant", "foreign-brand"):
                session = login(second, key, foreign, tenant="acme", brand="atlas")
                checks[foreign.replace("-", "_") + "_denied"] = second.denied(
                    "recommendations", session=session, resource_id="shared", market_code="us-en", context={})
                second.denied("recommendations", session=consumer, resource_id=foreign, market_code="us-en", context={})
                if second.ok("recommendations", session=session, resource_id=foreign, market_code="us-en", context={}) != []:
                    raise AssertionError("foreign empty library leaked another scope")
            reviewer = login(second, key, "reviewer")
            second.ok("review", session=reviewer, resource_id="shared", skill_id="fixture-skill", revision=1, decision="revoke")
            checks["revoked_skill_denied"] = second.denied(
                "reuse", error="ValueError", session=consumer, resource_id="shared",
                skill_id="fixture-skill", revision=1, task_id="fixture-after-revoke")
            second.ok("fixture_remove_consumer")
            checks["removed_membership_denied"] = second.denied(
                "recommendations", session=consumer, resource_id="shared", market_code="us-en", context={})
            restarted = first_pid != second.pid
        snapshots = list(Path(directory).rglob("registry.json"))
        if len(snapshots) != 1:
            raise AssertionError("expected exactly one persisted fixture library")
        snapshot_text = snapshots[0].read_text()
        if "eyJ" in snapshot_text or "PRIVATE KEY" in snapshot_text:
            raise AssertionError("transport credentials reached persistence")
    if not restarted or not all(checks.values()):
        raise AssertionError("acceptance checks failed")
    return dict(fixture_only=True, external_idp_configured=False, passed=True,
                trust_mode="pinned-rsa-public-key", resource_owner=approval["scope"]["user"],
                process_restart={"verified": restarted, "fresh_login_required": checks["old_session_denied"],
                                 "first_pid": first_pid, "second_pid": second.pid,
                                 "first_exit_code": first.process.returncode,
                                 "second_exit_code": second.process.returncode},
                approval={"skill_id": approval["skill_id"], "revision": approval["revision"],
                          "digest": approval["digest"], "reviewer": approval["review"]["reviewer"]},
                reuse=receipt, checks=checks,
                dependencies={name: importlib.metadata.version(name) for name in ("PyJWT", "cryptography")})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence", type=Path, help="new JSON evidence file outside the repository")
    parser.add_argument("--worker", type=Path, help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.worker is not None:
        worker(args.worker)
        return
    report = run_demo()
    encoded = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.evidence:
        descriptor = os.open(args.evidence, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(descriptor, "w") as output:
            output.write(encoded)
    print(encoded, end="")


if __name__ == "__main__":
    main()
