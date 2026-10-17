"""Trusted-server callback bridge. Not a web server or a complete OIDC client."""
from dataclasses import dataclass
from pathlib import Path
import os
import re
import secrets
import stat
import time

import jwt
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicKey
from urllib.parse import urlsplit

from learn_system import AccessContext, LearnAccessControl, LearningLevel, ResourceScope, _validate_identifier
from skill_registry import SkillRegistry, canonical, scan_safe
from security_checker import SecurityChecker


@dataclass(frozen=True)
class Identity:
    issuer: str
    subject: str


@dataclass(frozen=True)
class PendingLogin:
    handle: str
    nonce: str


class CallbackVerifier:
    def __init__(self, *, issuer, audience, public_keys):
        parsed = urlsplit(issuer) if isinstance(issuer, str) else None
        if (not parsed or parsed.scheme != "https" or not parsed.hostname or parsed.query
                or parsed.fragment or parsed.username or parsed.password
                or not isinstance(audience, str) or not audience.strip()
                or not isinstance(public_keys, dict) or not public_keys
                or any(not isinstance(kid, str) or not kid or not isinstance(key, RSAPublicKey)
                       or key.key_size < 2048 for kid, key in public_keys.items())):
            raise ValueError("trusted HTTPS issuer, audience and pinned RSA public keys required")
        self._issuer, self._audience = issuer, audience
        self._keys = dict(public_keys)
        self._pending = {}

    def begin_login(self):
        pending = PendingLogin(secrets.token_urlsafe(32), secrets.token_urlsafe(32))
        self._pending[pending.handle] = (pending.nonce, time.time() + 300)
        return pending

    def complete_login(self, pending_handle, id_token):
        try:
            nonce, expires = self._pending.pop(pending_handle)
            if time.time() >= expires:
                raise ValueError("expired pending login")
            if not isinstance(id_token, str) or len(id_token) > 16384:
                raise ValueError("invalid token")
            header = jwt.get_unverified_header(id_token)
            if (set(header) - {"alg", "typ", "kid"} or header.get("alg") != "RS256"
                    or header.get("typ") != "JWT" or not isinstance(header.get("kid"), str)):
                raise ValueError("unsupported header")
            claims = jwt.decode(id_token, self._keys[header["kid"]], algorithms=["RS256"],
                                issuer=self._issuer, audience=self._audience,
                                options={"require": ["iss", "aud", "sub", "iat", "exp", "nonce"],
                                         "strict_aud": True})
            now = time.time()
            if (not isinstance(claims["sub"], str) or not claims["sub"].strip()
                    or len(claims["sub"]) > 255
                    or type(claims["iat"]) is not int or type(claims["exp"]) is not int
                    or ("nbf" in claims and type(claims["nbf"]) is not int)
                    or ("azp" in claims and claims["azp"] != self._audience)
                    or not 0 <= now - claims["iat"] <= 300
                    or not claims["iat"] < claims["exp"] <= claims["iat"] + 300):
                raise ValueError("invalid callback claims")
            if not isinstance(claims["nonce"], str) or not secrets.compare_digest(claims["nonce"], nonce):
                raise ValueError("nonce mismatch")
            return Identity(claims["iss"], claims["sub"])
        except (jwt.PyJWTError, KeyError, TypeError, ValueError):
            raise PermissionError("login rejected") from None


@dataclass(frozen=True)
class TeamResource:
    tenant: str
    brand: str
    department: str
    team: str
    owner: str

    def __post_init__(self):
        for value in (self.tenant, self.brand, self.department, self.team, self.owner):
            _validate_identifier(value)

    @property
    def scope(self):
        # Owner is the stable configured shared library, NOT the current actor.
        return dict(tenant=self.tenant, brand=self.brand, team=self.team, user=self.owner)


class ServerPolicy:
    """Construct/update ONLY from trusted application configuration, never requests."""
    def __init__(self, *, users, grants):
        self._users = dict(users)
        if (len(set(self._users.values())) != len(self._users)
                or any(not isinstance(identity, Identity) or not identity.issuer or not identity.subject
                       for identity in self._users)):
            raise ValueError("distinct server users must map to issuer/subject pairs")
        for user in self._users.values():
            _validate_identifier(user)
        self._grants = {}
        for (identity, resource_id), roles in grants.items():
            self.set_roles(identity, resource_id, roles)

    def set_roles(self, identity, resource_id, roles):
        _validate_identifier(resource_id)
        if (identity not in self._users or not isinstance(roles, (set, frozenset))
                or not roles <= {"author", "verifier", "reviewer", "consumer"}):
            raise ValueError("known identity and explicit valid role set required")
        self._grants[(identity, resource_id)] = frozenset(roles)

    def roles(self, identity, resource_id):
        return self._grants.get((identity, resource_id), frozenset())

    def attestors(self, resource_id, role):
        return {self._users[identity] for identity in self._users
                if role in self.roles(identity, resource_id)}


class TeamService:
    """Server-only facade. Untrusted callers get results, never core capabilities."""
    def __init__(self, *, verifier, policy, resources, storage_root):
        self._verifier, self._policy = verifier, policy
        self._resources = dict(resources)
        self._root = Path(storage_root)
        self._sessions = {}

    def begin_login(self):
        return self._verifier.begin_login()

    def login(self, pending_handle, id_token):
        identity = self._verifier.complete_login(pending_handle, id_token)
        if identity not in self._policy._users:
            raise PermissionError("login rejected")
        session = secrets.token_urlsafe(32)
        self._sessions[session] = (identity, time.time() + 300)
        return session

    def _authorize(self, session, resource_id, role):
        try:
            identity, expires = self._sessions[session]
            resource = self._resources[resource_id]
            actor = self._policy._users[identity]
            if time.time() >= expires or role not in self._policy.roles(identity, resource_id):
                raise PermissionError("access denied")
            context = AccessContext(resource.tenant, resource.brand, actor,
                                    team_ids=frozenset({(resource.department, resource.team)}))
            scope = ResourceScope(resource.tenant, LearningLevel.TEAM, resource.brand,
                                  resource.department, resource.team)
            if not LearnAccessControl().can_access(context, scope):
                raise PermissionError("access denied")
            return actor, resource
        except (KeyError, TypeError):
            raise PermissionError("access denied") from None

    @staticmethod
    def _protected_directory(path):
        mode = path.lstat()
        if (not stat.S_ISDIR(mode.st_mode) or mode.st_mode & 0o077
                or (hasattr(os, "getuid") and mode.st_uid != os.getuid())):
            raise PermissionError("storage must be owner-only real directories")

    def _registry(self, session, resource_id, role):
        actor, resource = self._authorize(session, resource_id, role)
        # All ACL decisions precede even directory creation or snapshot reading.
        path = self._root
        self._protected_directory(path)
        for part in (resource.tenant, resource.brand, resource.department, resource.team, resource.owner):
            path = path / part
            path.mkdir(mode=0o700, exist_ok=True)
            self._protected_directory(path)
        registry = SkillRegistry(resource.scope, data_dir=path,
                                 reviewers=self._policy.attestors(resource_id, "reviewer"),
                                 verifiers=self._policy.attestors(resource_id, "verifier"))
        return actor, registry

    @staticmethod
    def _screen(payload):
        # Extra transport-credential guard, not a replacement or weakened scanner.
        scan_safe(SecurityChecker(), payload)
        if re.search(r"[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]*", canonical(payload)):
            raise ValueError("transport credentials cannot be learning content")

    def record_outcome(self, session, resource_id, **evidence):
        _, registry = self._registry(session, resource_id, "author")
        self._screen(evidence)
        return registry.record_outcome(**evidence)

    def verify_outcome(self, session, resource_id, task_id):
        actor, registry = self._registry(session, resource_id, "verifier")
        return registry.verify_outcome(task_id, validator=actor)

    def draft(self, session, resource_id, *, content, task_ids, market_code, condition, skill_id=None):
        actor, registry = self._registry(session, resource_id, "author")
        self._screen(dict(content=content, task_ids=task_ids, market_code=market_code,
                          condition=condition, skill_id=skill_id))
        return registry.draft(content=content, task_ids=task_ids, market_code=market_code,
                              condition=condition, skill_id=skill_id, source={"actor": actor})

    def review(self, session, resource_id, skill_id, revision, *, decision):
        actor, registry = self._registry(session, resource_id, "reviewer")
        return registry.review(skill_id, revision, reviewer=actor, decision=decision)

    def recommendations(self, session, resource_id, market_code, context):
        _, registry = self._registry(session, resource_id, "consumer")
        return registry.recommendations(market_code, context)

    def reuse(self, session, resource_id, skill_id, revision, *, task_id):
        actor, registry = self._registry(session, resource_id, "consumer")
        self._screen(dict(skill_id=skill_id, revision=revision, task_id=task_id))
        return {**registry.reuse(skill_id, revision, task_id=task_id), "actor": actor}
