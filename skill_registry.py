"""Scoped, reviewed skill artifacts. No code in a skill is executed here."""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import tempfile
import uuid

from security_checker import SecurityChecker


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()


def now():
    return datetime.now(timezone.utc).isoformat()


def scan_safe(checker, value):
    """Scan decoded strings as well as field assignments (JSON quotes hide keys)."""
    # Screen the exact transport representation, including numeric leaves and
    # field assignments, then also scan decoded strings below (JSON escapes can
    # otherwise hide sensitive Unicode or labelled credentials).
    if not checker.scan_content(canonical(value))[0]:
        raise ValueError("unsafe learning content")
    if isinstance(value, str):
        if not checker.scan_content(value)[0]:
            raise ValueError("unsafe learning content")
    elif isinstance(value, dict):
        for key, item in value.items():
            if not isinstance(key, str):
                raise ValueError("JSON string keys required")
            scan_safe(checker, key)
            # Pair the decoded key with every JSON value, not only strings:
            # ensure_ascii transport escaping can hide multilingual/obfuscated
            # credential labels when their value is numeric, boolean or null.
            assignment = item if isinstance(item, str) else canonical(item)
            scan_safe(checker, key + ":" + assignment)
            scan_safe(checker, item)
    elif isinstance(value, list):
        for item in value:
            scan_safe(checker, item)
    elif value is not None and type(value) not in (bool, int, float):
        # json.dumps accepts tuples as arrays, but scanning must not silently
        # skip a type whose decoded representation will differ after restart.
        raise ValueError("only JSON objects, arrays, strings and scalar values are accepted")


class SkillRegistry:
    """Application-supplied scope and identities are trusted, not authentication."""

    def __init__(self, scope, *, reviewers=(), verifiers=(), security_checker=None, data_dir=None):
        if not isinstance(scope, dict) or set(scope) != {"tenant", "brand", "team", "user"}:
            raise ValueError("explicit tenant/brand/team/user scope required")
        if any(not isinstance(v, str) or not v.strip() for v in scope.values()):
            raise ValueError("scope values must be nonempty strings")
        self._checker = security_checker if security_checker is not None else SecurityChecker()
        self._scope = deepcopy(scope)
        self._reviewers = frozenset(reviewers)
        self._verifiers = frozenset(verifiers)
        self._evidence = {}
        self._skills = {}
        self._reuses = {}
        self._disk_integrity = None
        self._directory = Path(data_dir).expanduser() if data_dir is not None else None
        if self._directory:
            self._directory.mkdir(mode=0o700, parents=True, exist_ok=True)
            self._path = self._directory / "registry.json"
            self._check_store()
            if self._path.exists():
                data = json.loads(self._path.read_text(encoding="utf-8"))
                self._validate_snapshot(data)
                self._evidence, self._skills = data["evidence"], data["skills"]
                self._reuses = data["reuses"]
                self._disk_integrity = data["integrity"]

    def _check_store(self):
        paths = [self._directory]
        if self._path.exists() or self._path.is_symlink():
            paths.append(self._path)
        for path in paths:
            stat = path.lstat()
            if path.is_symlink() or (hasattr(os, "getuid") and stat.st_uid != os.getuid()) or stat.st_mode & 0o077:
                raise PermissionError("registry must be owner-only and not symlinked")
        if not self._directory.is_dir() or (self._path.exists() and not self._path.is_file()):
            raise PermissionError("invalid registry path type")

    @staticmethod
    def _timestamp(value):
        if not isinstance(value, str) or datetime.fromisoformat(value).tzinfo is None:
            raise ValueError("timezone-aware timestamp required")

    def _validate_verification(self, item):
        self._validate_evidence(item)
        verification = item["verification"]
        if verification is not None:
            if verification["validator"] not in self._verifiers:
                raise ValueError("untrusted outcome validator")
            self._timestamp(verification["at"])
            if verification["digest"] != digest({k: v for k, v in item.items() if k != "verification"}):
                raise ValueError("evidence verification digest mismatch")

    @staticmethod
    def _improved(item):
        return item["success"] and item["verification"] is not None and (
            item["candidate"] < item["baseline"] if item["direction"] == "lower"
            else item["candidate"] > item["baseline"])

    def _validate_snapshot(self, data):
        try:
            scan_safe(self._checker, data)
            if data["scope"] != self._scope or data["schema"] != 1:
                raise ValueError("registry scope or schema mismatch")
            if data["integrity"] != digest({k: v for k, v in data.items() if k != "integrity"}):
                raise ValueError("registry integrity mismatch")
            for task_id, item in data["evidence"].items():
                if task_id != item["task_id"]:
                    raise ValueError("evidence identity mismatch")
                self._validate_verification(item)
            for skill_id, versions in data["skills"].items():
                if not versions:
                    raise ValueError("empty version history")
                for revision, entry in enumerate(versions, 1):
                    artifact = entry["artifact"]
                    if artifact["scope"] != self._scope or artifact["skill_id"] != skill_id or artifact["revision"] != revision:
                        raise ValueError("skill identity or scope mismatch")
                    if entry["digest"] != digest(artifact):
                        raise ValueError("skill content digest mismatch")
                    if not isinstance(artifact["content"], str) or not artifact["content"].strip():
                        raise ValueError("lesson content required")
                    if not isinstance(artifact["condition"], dict) or not artifact["source"] or not artifact["market_code"]:
                        raise ValueError("source, market and condition required")
                    self._timestamp(artifact["created_at"])
                    tasks = set()
                    if not artifact["evidence"]:
                        raise ValueError("task evidence required")
                    for item in artifact["evidence"]:
                        self._validate_verification(item)
                        task = item["task_id"]
                        if task in tasks:
                            raise ValueError("duplicate task evidence")
                        tasks.add(task)
                        stored = data["evidence"][task]
                        if any(item[k] != stored[k] for k in item if k != "verification"):
                            raise ValueError("skill evidence differs from recorded outcome")
                        if item["verification"] is not None and item["verification"] != stored["verification"]:
                            raise ValueError("skill evidence verification differs")
                    history = entry["history"]
                    states = [h["state"] for h in history]
                    if states not in (["pending"], ["pending", "approved"], ["pending", "rejected"], ["pending", "approved", "revoked"]):
                        raise ValueError("invalid review history")
                    if states[-1] != entry["state"]:
                        raise ValueError("review state/history mismatch")
                    for h in history:
                        self._timestamp(h["at"])
                        if h["state"] != "pending" and (h["reviewer"] not in self._reviewers or h["digest"] != entry["digest"]):
                            raise ValueError("untrusted review history")
                    if entry["state"] in ("approved", "revoked"):
                        review = entry["review"]
                        if not review or review["reviewer"] not in self._reviewers or review["digest"] != entry["digest"]:
                            raise ValueError("untrusted approval or approval digest mismatch")
                        if {"state": "approved", **review} != history[1] or not all(self._improved(e) for e in artifact["evidence"]):
                            raise ValueError("approval lacks verified improvement")
                    elif entry["review"] is not None:
                        raise ValueError("unapproved skill has approval metadata")
            for task, receipt in data["reuses"].items():
                versions = data["skills"][receipt["skill_id"]]
                revision = receipt["revision"]
                if type(revision) is not int or not 1 <= revision <= len(versions):
                    raise ValueError("invalid reuse revision")
                entry = versions[revision - 1]
                self._timestamp(receipt["at"])
                if task != receipt["task_id"] or receipt["digest"] != entry["digest"] or entry["review"] is None:
                    raise ValueError("reuse receipt does not match reviewed artifact")
        except (KeyError, TypeError, AttributeError, OverflowError) as exc:
            raise ValueError("malformed registry") from exc

    def _check_fresh(self):
        if self._directory:
            self._check_store()
            if self._path.exists():
                data = json.loads(self._path.read_text(encoding="utf-8"))
                self._validate_snapshot(data)
                current = data["integrity"]
            else:
                current = None
            if current != self._disk_integrity:
                raise ValueError("registry changed; reopen before reading or writing")

    def _commit(self, *, evidence=None, skills=None, reuses=None):
        self._check_fresh()
        evidence = self._evidence if evidence is None else evidence
        skills = self._skills if skills is None else skills
        reuses = self._reuses if reuses is None else reuses
        data = dict(schema=1, scope=self._scope, evidence=evidence, skills=skills, reuses=reuses)
        data["integrity"] = digest(data)
        self._validate_snapshot(data)
        if self._directory:
            self._check_store()
            fd, temporary = tempfile.mkstemp(prefix=".registry-", dir=self._directory)
            try:
                with os.fdopen(fd, "w", encoding="utf-8") as handle:
                    handle.write(canonical(data))
                    handle.flush()
                    os.fsync(handle.fileno())
                os.replace(temporary, self._path)
                self._disk_integrity = data["integrity"]
            finally:
                if os.path.exists(temporary):
                    os.unlink(temporary)
        self._evidence, self._skills, self._reuses = evidence, skills, reuses

    def record_outcome(self, *, task_id, source_ref, result_ref, metric, baseline,
                       candidate, direction, success):
        item = dict(task_id=task_id, source_ref=source_ref, result_ref=result_ref,
                    metric=metric, baseline=baseline, candidate=candidate,
                    direction=direction, success=success, verification=None)
        self._validate_evidence(item)
        if task_id in self._evidence or any(e["result_ref"] == result_ref for e in self._evidence.values()):
            raise ValueError("task_id or result_ref already recorded")
        self._commit(evidence={**self._evidence, task_id: item})
        return deepcopy(item)

    @staticmethod
    def _validate_evidence(item):
        for key in ("task_id", "source_ref", "result_ref", "metric"):
            if not isinstance(item[key], str) or not item[key].strip():
                raise ValueError(f"{key} must be a nonempty string")
        if item["direction"] not in ("higher", "lower") or type(item["success"]) is not bool:
            raise ValueError("explicit direction and boolean success required")
        try:
            for key in ("baseline", "candidate"):
                value = item[key]
                if type(value) not in (int, float) or not math.isfinite(value):
                    raise ValueError("metrics must be finite numbers, not booleans")
            if not math.isfinite(item["candidate"] - item["baseline"]):
                raise ValueError("metric difference must be finite")
        except OverflowError as exc:
            raise ValueError("metric magnitude is unsupported") from exc

    def verify_outcome(self, task_id, *, validator):
        if validator not in self._verifiers:
            raise PermissionError("outcome validator is not authorized")
        item = deepcopy(self._evidence[task_id])
        if item["verification"] is not None:
            return item
        item["verification"] = {"validator": validator, "at": now(),
                                "digest": digest({k: v for k, v in item.items() if k != "verification"})}
        self._commit(evidence={**self._evidence, task_id: item})
        return deepcopy(item)

    def draft(self, *, content, task_ids, source, market_code, condition, skill_id=None):
        if not task_ids or len(set(task_ids)) != len(task_ids):
            raise ValueError("distinct task evidence is required")
        if not isinstance(content, str) or not content.strip():
            raise ValueError("lesson content required")
        if skill_id is not None and (not isinstance(skill_id, str) or not skill_id.strip()):
            raise ValueError("explicit skill_id must be a nonempty string")
        skill_id = uuid.uuid4().hex if skill_id is None else skill_id
        versions = self._skills.get(skill_id, [])
        artifact = dict(skill_id=skill_id, revision=len(versions) + 1,
                        scope=deepcopy(self._scope), content=content,
                        evidence=[deepcopy(self._evidence[t]) for t in task_ids],
                        source=deepcopy(source), market_code=market_code,
                        condition=deepcopy(condition), created_at=now())
        entry = dict(artifact=artifact, digest=digest(artifact), state="pending", review=None,
                     history=[{"state": "pending", "at": now()}])
        self._commit(skills={**self._skills, skill_id: [*versions, entry]})
        return self._view(entry)

    @staticmethod
    def _view(entry):
        result = deepcopy(entry["artifact"])
        result.update({key: deepcopy(entry[key]) for key in ("digest", "state", "review", "history")})
        return result

    @property
    def scope(self):
        return deepcopy(self._scope)

    def list_skills(self):
        """Current revisions, including pending/rejected, for review UIs only."""
        return [self._view(versions[-1]) for versions in self._skills.values()]

    def revise(self, skill_id, content, *, task_ids=None):
        old = self._skills[skill_id][-1]["artifact"]
        return self.draft(content=content,
                          task_ids=task_ids if task_ids is not None else [e["task_id"] for e in old["evidence"]],
                          source=old["source"], market_code=old["market_code"],
                          condition=old["condition"], skill_id=skill_id)

    def import_bundle(self, data):
        """Untrusted transport: accept only same-scope drafts, never attestations."""
        scan_safe(self._checker, data)
        if data.get("scope") != self._scope:
            raise ValueError("import scope mismatch")
        staged = SkillRegistry(self._scope, reviewers=self._reviewers, verifiers=self._verifiers,
                               security_checker=self._checker)
        staged._evidence, staged._skills = deepcopy(self._evidence), deepcopy(self._skills)
        staged._reuses = deepcopy(self._reuses)
        imported = {}
        try:
            for item in data.get("skills", []):
                if item["scope"] != self._scope or item["skill_id"] in staged._skills:
                    raise ValueError("foreign scope or existing skill identity")
                tasks = []
                for e in item["evidence"]:
                    self._validate_evidence(e)
                    base = {k: v for k, v in e.items() if k != "verification"}
                    task = e["task_id"]
                    if task in imported:
                        if imported[task] != base:
                            raise ValueError("conflicting imported task")
                    else:
                        staged.record_outcome(**base)
                        imported[task] = base
                    tasks.append(task)
                staged.draft(content=item["content"], task_ids=tasks, skill_id=item["skill_id"],
                             source={"imported_digest": item.get("digest"), "source": item["source"]},
                             market_code=item["market_code"], condition=item["condition"])
        except (KeyError, TypeError, AttributeError) as exc:
            raise ValueError("malformed learning import") from exc
        self._commit(evidence=staged._evidence, skills=staged._skills)

    def _entry(self, skill_id, revision):
        if type(revision) is not int or revision < 1 or revision > len(self._skills.get(skill_id, [])):
            raise ValueError("unknown revision")
        return self._skills[skill_id][revision - 1]

    def get_revision(self, skill_id, revision):
        return self._view(self._entry(skill_id, revision))

    def rollback(self, skill_id, revision, *, reviewer):
        if reviewer not in self._reviewers:
            raise PermissionError("human reviewer is not authorized")
        old = self._entry(skill_id, revision)["artifact"]
        return self.draft(content=old["content"], task_ids=[e["task_id"] for e in old["evidence"]],
                          source={"rollback_from": revision, "reviewer": reviewer,
                                  "original_source": old["source"]},
                          market_code=old["market_code"], condition=old["condition"], skill_id=skill_id)

    def review(self, skill_id, revision, *, reviewer, decision):
        if reviewer not in self._reviewers:
            raise PermissionError("human reviewer is not authorized")
        original = self._entry(skill_id, revision)
        entry = deepcopy(original)
        if decision in ("reject", "revoke"):
            required = "pending" if decision == "reject" else "approved"
            if entry["state"] != required:
                raise ValueError("invalid review state transition")
            entry["state"] = "rejected" if decision == "reject" else "revoked"
            entry["history"].append({"state": entry["state"], "reviewer": reviewer,
                                     "at": now(), "digest": entry["digest"]})
            self._replace_entry(skill_id, revision, entry)
            return self._view(entry)
        if decision != "approve":
            raise ValueError("unknown review decision")
        artifact = entry["artifact"]
        if original is not self._skills[skill_id][-1] or entry["state"] != "pending":
            raise ValueError("only the current pending revision can be approved")
        if not artifact["evidence"] or not all(self._improved(e) for e in artifact["evidence"]):
            raise ValueError("verified successful improvement required")
        entry["review"] = {"reviewer": reviewer, "at": now(), "digest": entry["digest"]}
        entry["state"] = "approved"
        entry["history"].append({"state": "approved", **entry["review"]})
        self._replace_entry(skill_id, revision, entry)
        return self._view(entry)

    def _replace_entry(self, skill_id, revision, entry):
        versions = list(self._skills[skill_id])
        versions[revision - 1] = entry
        self._commit(skills={**self._skills, skill_id: versions})

    def reuse(self, skill_id, revision, *, task_id):
        entry = self._entry(skill_id, revision)
        if entry is not self._skills[skill_id][-1] or entry["state"] != "approved":
            raise ValueError("only current approved skills may be reused")
        if not isinstance(task_id, str) or not task_id.strip() or task_id in self._reuses or task_id in self._evidence:
            raise ValueError("new unique reuse task_id required")
        receipt = dict(task_id=task_id, skill_id=skill_id, revision=revision,
                       digest=entry["digest"], at=now())
        self._commit(reuses={**self._reuses, task_id: receipt})
        return deepcopy(receipt)

    def record_reuse_outcome(self, **evidence):
        if evidence.get("task_id") not in self._reuses:
            raise ValueError("record reuse before recording its outcome")
        self.record_outcome(**evidence)
        return self.compare_outcome(evidence["task_id"])

    def compare_outcome(self, task_id):
        receipt = self._reuses[task_id]
        item = self._evidence[task_id]
        verified = item["verification"] is not None
        return {**deepcopy(receipt), **deepcopy(item), "verified": verified,
                "delta": item["candidate"] - item["baseline"],
                "improved": bool(self._improved(item)) if verified else None}

    def recommendations(self, market_code, context):
        self._check_fresh()
        return [self._view(entries[-1]) for entries in self._skills.values()
                if entries[-1]["state"] == "approved"
                and entries[-1]["artifact"]["market_code"] == market_code
                and all(context.get(k) == v for k, v in entries[-1]["artifact"]["condition"].items())]
