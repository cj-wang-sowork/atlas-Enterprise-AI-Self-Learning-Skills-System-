#!/usr/bin/env python3
"""Five-layer learning files and access validation for ATLAS."""

from __future__ import annotations

import hashlib
import logging
import os
import re
import stat
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class LearningLevel(Enum):
    ENTERPRISE = "enterprise"
    BRAND = "brand"
    DEPARTMENT = "department"
    TEAM = "team"
    PERSONAL = "personal"


class AccessLevel(Enum):
    PUBLIC = "@public"
    INTERNAL = "@internal"
    TEAM_PRIVATE = "@team-private"
    PRIVATE = "@private"


def _validate_identifier(value: str) -> None:
    if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,127}", value):
        raise ValueError("scope identifiers must be 1-128 ASCII letters, digits, underscores or hyphens")


@dataclass(frozen=True)
class AccessContext:
    """Authenticated identity supplied by the trusted embedding application.

    Memberships are scoped to the selected tenant and brand. Team memberships
    are (department_id, team_id) pairs, never globally meaningful team names.
    This value is not an authentication provider or a user-claim verifier.
    """

    tenant_id: str
    brand_id: str
    user_id: str
    department_ids: frozenset[str] = frozenset()
    team_ids: frozenset[tuple[str, str]] = frozenset()

    def __post_init__(self) -> None:
        for identifier in (self.tenant_id, self.brand_id, self.user_id):
            _validate_identifier(identifier)
        if not isinstance(self.department_ids, frozenset) or not isinstance(self.team_ids, frozenset):
            raise ValueError("memberships must be immutable frozensets")
        for department in self.department_ids:
            _validate_identifier(department)
        for team in self.team_ids:
            if not isinstance(team, tuple) or len(team) != 2:
                raise ValueError("team membership must be a (department_id, team_id) pair")
            for identifier in team:
                _validate_identifier(identifier)


@dataclass(frozen=True)
class ResourceScope:
    tenant_id: str
    level: LearningLevel
    brand_id: Optional[str] = None
    department_id: Optional[str] = None
    team_id: Optional[str] = None
    owner_id: Optional[str] = None

    def __post_init__(self) -> None:
        _validate_identifier(self.tenant_id)
        fields = {
            LearningLevel.ENTERPRISE: (),
            LearningLevel.BRAND: ("brand_id",),
            LearningLevel.DEPARTMENT: ("brand_id", "department_id"),
            LearningLevel.TEAM: ("brand_id", "department_id", "team_id"),
            LearningLevel.PERSONAL: ("brand_id", "owner_id"),
        }
        if self.level not in fields:
            raise ValueError("invalid learning level")
        for field in ("brand_id", "department_id", "team_id", "owner_id"):
            value = getattr(self, field)
            if field in fields[self.level]:
                _validate_identifier(value)
            elif value is not None:
                raise ValueError("unexpected scope identifier for this learning level")


@dataclass
class LearnFile:
    path: Path
    level: LearningLevel
    access: AccessLevel
    content: str
    created: str
    author: str
    market: Optional[str] = None
    department: Optional[str] = None
    checksum: Optional[str] = None


class LearnSecurityValidator:
    """Apply the same sensitive-content policy used by the skill registry."""

    def __init__(self, security_checker=None) -> None:
        from security_checker import SecurityChecker
        self.checker = security_checker if security_checker is not None else SecurityChecker()
        self.violations: List[str] = []

    def validate_file(self, learn_file: LearnFile) -> Tuple[bool, List[str]]:
        _, found = self.checker.scan_content(learn_file.content)
        self.violations = [f"SENSITIVE_CONTENT:{item.violation_type}: {learn_file.path}" for item in found]
        if learn_file.level == LearningLevel.PERSONAL:
            self.violations.append(f"PERSONAL_LAYER_NOT_FOR_GIT: {learn_file.path}")
        return not self.violations, list(self.violations)


class LearnAccessControl:
    """Access checks for the ATLAS five-layer hierarchy."""

    REQUIRED_MARKERS = {
        LearningLevel.ENTERPRISE: AccessLevel.PUBLIC,
        LearningLevel.BRAND: AccessLevel.INTERNAL,
        LearningLevel.DEPARTMENT: AccessLevel.INTERNAL,
        LearningLevel.TEAM: AccessLevel.TEAM_PRIVATE,
        LearningLevel.PERSONAL: AccessLevel.PRIVATE,
    }

    def can_access(self, context: AccessContext, scope: ResourceScope) -> bool:
        if not isinstance(context, AccessContext) or not isinstance(scope, ResourceScope):
            return False
        if context.tenant_id != scope.tenant_id:
            return False
        if scope.level == LearningLevel.ENTERPRISE:
            return True
        if context.brand_id != scope.brand_id:
            return False
        if scope.level == LearningLevel.BRAND:
            return True
        if scope.level == LearningLevel.DEPARTMENT:
            return (scope.department_id in context.department_ids or
                    any(department == scope.department_id for department, _ in context.team_ids))
        if scope.level == LearningLevel.TEAM:
            return (scope.department_id, scope.team_id) in context.team_ids
        if scope.level == LearningLevel.PERSONAL:
            return scope.owner_id == context.user_id
        return False

    def verify_access_marker(self, learn_file: LearnFile) -> Tuple[bool, str]:
        expected = self._get_required_marker(learn_file.level)
        if learn_file.access == expected:
            return True, "access marker is valid"
        return False, f"expected {expected.value}, got {learn_file.access.value}"

    @staticmethod
    def _get_required_marker(level: LearningLevel) -> AccessLevel:
        return LearnAccessControl.REQUIRED_MARKERS[level]


class MultiMarketLearnManager:
    """Loads path-bound, tenant-scoped learning files after authorization."""

    def __init__(self, workspace_root: str = "~/.openclaw/workspace") -> None:
        self.workspace_root = Path(workspace_root).expanduser()
        self.learn_root = self.workspace_root / "learn"
        self.validator = LearnSecurityValidator()
        self.access_control = LearnAccessControl()
        self.logger = self._setup_logging()

    def _setup_logging(self) -> logging.Logger:
        logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")
        return logging.getLogger(__name__)

    @staticmethod
    def _require_context(context: Optional[AccessContext]) -> AccessContext:
        if not isinstance(context, AccessContext):
            raise PermissionError("authenticated AccessContext is required")
        return context

    def _scope_for_path(self, path: Path) -> ResourceScope:
        parts = path.relative_to(self.learn_root).parts
        if ".." in parts or path.suffix != ".md":
            raise ValueError("path traversal and non-Markdown resources are forbidden")
        if len(parts) < 3:
            raise ValueError("not a canonical scoped learning path")
        tenant, level_name = parts[:2]
        level = LearningLevel(level_name)
        fields = {
            LearningLevel.ENTERPRISE: (),
            LearningLevel.BRAND: ("brand_id",),
            LearningLevel.DEPARTMENT: ("brand_id", "department_id"),
            LearningLevel.TEAM: ("brand_id", "department_id", "team_id"),
            LearningLevel.PERSONAL: ("brand_id", "owner_id"),
        }[level]
        if len(parts) < 3 + len(fields):
            raise ValueError("missing path scope")
        return ResourceScope(tenant, level, **dict(zip(fields, parts[2:])))

    def load_learn_files(
        self, context: Optional[AccessContext] = None, *,
        level: Optional[LearningLevel] = None, market: Optional[str] = None
    ) -> List[LearnFile]:
        context = self._require_context(context)
        files: List[LearnFile] = []
        for path in sorted((self.learn_root / context.tenant_id).glob("**/*.md")):
            try:
                scope = self._scope_for_path(path)
                if level is not None and scope.level != level:
                    continue
                if not self.access_control.can_access(context, scope):
                    continue
                learn_file = self._parse_learn_file(path)
            except (ValueError, OSError):
                continue
            if market is None or learn_file.market == market:
                files.append(learn_file)
        return files

    def load_learn_file(self, path: Path, context: Optional[AccessContext] = None) -> LearnFile:
        context = self._require_context(context)
        path = Path(path)
        scope = self._scope_for_path(path)
        if not self.access_control.can_access(context, scope):
            raise PermissionError("learning resource is outside the authenticated scope")
        return self._parse_learn_file(path)

    def _parse_learn_file(self, file_path: Path) -> LearnFile:
        scope = self._scope_for_path(file_path)
        # Unbuffered header reads never prefetch a rejected resource's body.
        with self._open_scoped_file(file_path) as stream:
            header = self._read_header(stream)
            metadata = self._parse_metadata(header)
            self._verify_scope_metadata(scope, metadata)
            content = header + self._read_body(stream)
        # Scan every runtime entry point after authorization and bounded metadata
        # validation, but before content can enter the caller's context. Personal
        # owner access is allowed here; the offline no-personal-for-Git rule is not.
        if not self.validator.checker.scan_content(content)[0]:
            raise ValueError("learning resource contains unsafe content")
        return LearnFile(
            path=file_path,
            level=scope.level,
            access=AccessLevel(metadata["access"]),
            content=content,
            created=metadata.get("created", datetime.utcnow().date().isoformat()),
            author=metadata.get("author", "unknown"),
            market=metadata.get("market"),
            department=scope.department_id,
            checksum=hashlib.sha256(content.encode("utf-8")).hexdigest(),
        )

    @contextmanager
    def _open_scoped_file(self, path: Path):
        """Walk from the trusted workspace anchor without following links.

        Descriptor-relative opens prevent a checked directory from being replaced
        by a symlink between a path check and the eventual body read.
        """
        relative = path.relative_to(self.workspace_root).parts
        directory_flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
        directory = os.open(self.workspace_root, directory_flags)
        try:
            for part in relative[:-1]:
                child = os.open(part, directory_flags, dir_fd=directory)
                os.close(directory)
                directory = child
            descriptor = os.open(relative[-1], os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK,
                                 dir_fd=directory)
            try:
                if not stat.S_ISREG(os.fstat(descriptor).st_mode):
                    raise ValueError("learning resources must be regular files")
                with os.fdopen(descriptor, "rb", buffering=0, closefd=False) as stream:
                    yield stream
            finally:
                os.close(descriptor)
        finally:
            os.close(directory)

    @staticmethod
    def _read_header(stream) -> str:
        header = bytearray()
        line = bytearray()
        while len(header) < 16384:
            char = stream.read(1)
            if not char:
                raise ValueError("missing or unterminated metadata header")
            header.extend(char)
            line.extend(char)
            if char == b"\n":
                if len(header) == len(line):
                    if bytes(line).rstrip(b"\r\n") != b"---":
                        raise ValueError("metadata header must start with ---")
                elif bytes(line).rstrip(b"\r\n") == b"---":
                    return bytes(header).decode("utf-8")
                line.clear()
        raise ValueError("metadata header exceeds 16 KiB")

    @staticmethod
    def _read_body(stream) -> str:
        return stream.read().decode("utf-8")

    @staticmethod
    def _verify_scope_metadata(scope: ResourceScope, metadata: Dict[str, str]) -> None:
        expected = {
            "tenant_id": scope.tenant_id,
            "level": scope.level.value,
            "access": LearnAccessControl.REQUIRED_MARKERS[scope.level].value,
            "brand_id": scope.brand_id,
            "department_id": scope.department_id,
            "team_id": scope.team_id,
            "owner_id": scope.owner_id,
        }
        for key, value in expected.items():
            if metadata.get(key) != value:
                raise ValueError(f"metadata {key} does not match canonical path scope")

    def get_market_context(
        self, market: str, context: Optional[AccessContext] = None
    ) -> List[LearnFile]:
        return self.load_learn_files(context, market=market)

    def audit_security(self) -> Dict[str, object]:
        """Privileged offline audit across tenants; never use for agent context.

        The embedding application must restrict who may invoke this audit. It
        intentionally reads valid resources from every tenant, but returns only
        counts and findings, not learning content.
        """
        results = {"valid": True, "files": 0, "violations": []}
        roots = (self.workspace_root, self.learn_root)
        if any(root.is_symlink() or not root.is_dir() for root in roots):
            return {"valid": False, "files": 0, "violations": ["INVALID_AUDIT_ROOT"]}

        paths = []
        def walk_error(error):
            results["violations"].append(f"AUDIT_IO_ERROR: {error.filename}")

        for directory, directories, filenames in os.walk(
            self.learn_root, followlinks=False, onerror=walk_error
        ):
            for name in sorted(directories):
                path = Path(directory) / name
                if path.is_symlink():
                    results["violations"].append(f"SYMLINK_DIRECTORY: {path}")
                    directories.remove(name)
            directories.sort()
            paths.extend(Path(directory) / name for name in filenames if name.endswith(".md"))

        for path in sorted(paths):
            results["files"] += 1
            try:
                learn_file = self._parse_learn_file(path)
                _, violations = self.validator.validate_file(learn_file)
            except (ValueError, OSError):
                violations = [f"INVALID_RESOURCE: {path}"]
            if violations:
                results["valid"] = False
                results["violations"].extend(violations)
        results["valid"] = not results["violations"]
        return results

    @staticmethod
    def _parse_metadata(content: str) -> Dict[str, str]:
        lines = content.splitlines()
        if not lines or lines[0] != "---" or lines[-1] != "---":
            raise ValueError("metadata requires exact opening and closing fences")
        metadata: Dict[str, str] = {}
        for line in lines[1:-1]:
            if not line.strip():
                continue
            if ":" not in line:
                raise ValueError("metadata must use flat key: value entries")
            key, value = line.split(":", 1)
            key, value = key.strip(), value.strip()
            if not re.fullmatch(r"[a-z][a-z0-9_]*", key) or key in metadata or not value:
                raise ValueError("invalid or duplicate metadata key")
            if value[0] in "\"'":
                if len(value) < 2 or value[-1] != value[0]:
                    raise ValueError("unterminated metadata value")
                value = value[1:-1]
            if not value:
                raise ValueError("empty metadata value")
            metadata[key] = value
        return metadata


def main() -> None:
    manager = MultiMarketLearnManager()
    print(manager.audit_security())


if __name__ == "__main__":
    main()
