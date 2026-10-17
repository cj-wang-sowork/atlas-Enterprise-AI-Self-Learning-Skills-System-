"""Security checks for ATLAS learning files and runtime content."""

from __future__ import annotations

import json
import logging
import re
import unicodedata
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class ViolationSeverity(Enum):
    INFO = "info"
    WARNING = "warning"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class SecurityViolation:
    violation_type: str
    message: str
    severity: ViolationSeverity = ViolationSeverity.WARNING
    market_code: Optional[str] = None
    file_path: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, str]:
        data = asdict(self)
        data["severity"] = self.severity.value
        data["created_at"] = self.created_at.isoformat()
        return data


class SecurityChecker:
    """Detects common secret, PII, path, and access-marker issues."""

    CREDENTIAL_PATTERNS = {
        "api_key": r"(?i)(?:api[_-]?key|apikey|api金鑰|api密钥|金鑰|密鑰|密钥)['\"]?\s*[:=]\s*['\"]?[^'\"\s,}]+",
        "password": r"(?i)(?:password|passwd|pwd|密碼|密码)['\"]?\s*[:=]\s*['\"]?[^'\"\s,}]+",
        "token": r"(?i)(?:secret|token|權杖|令牌)['\"]?\s*[:=]\s*['\"]?[^'\"\s,}]+",
        "bearer": r"(?i)\bBearer\s+[a-z0-9._~+/=-]{8,}",
        "private_key": r"-----BEGIN [A-Z ]*PRIVATE KEY-----",
        "openai_key": r"\bsk-(?:proj-|svcacct-)?[A-Za-z0-9_-]{20,}\b",
        "github_key": r"\b(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,})\b",
        "aws_access_key": r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b",
        "google_key": r"\bAIza[0-9A-Za-z_-]{35}\b",
        "slack_key": r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b",
    }
    PII_PATTERNS = {
        "taiwan_phone": r"(?<![A-Za-z0-9])(?:09\d{2}|\+886[-.\s]?9\d{2})[-.\s]?\d{3}[-.\s]?\d{3}(?![A-Za-z0-9])",
        "taiwan_id": r"(?i)(?<![a-z0-9])[a-z][12][0-9]{8}(?![a-z0-9])",
        "ssn": r"\b\d{3}-\d{2}-\d{4}\b",
        "phone": r"\b(?:\+?1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}\b",
        "email": r"(?i)(?<![\w.+-])[a-z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-z0-9](?:[a-z0-9-]*[a-z0-9])?(?:\.[a-z0-9](?:[a-z0-9-]*[a-z0-9])?)+(?![\w-])",
    }

    def __init__(
        self, audit_log_path: Optional[str] = None, logger: Optional[logging.Logger] = None,
        *, allowed_emails=(), deny_terms=(),
    ) -> None:
        self.allowed_emails = frozenset(email.casefold() for email in allowed_emails)
        self.deny_terms = frozenset(self._normalize(term).casefold() for term in deny_terms if term)
        self.audit_log_path = Path(audit_log_path).expanduser() if audit_log_path else None
        self.logger = logger or logging.getLogger(__name__)
        self.violations: List[SecurityViolation] = []

    def scan_content(
        self, content: str, market_code: Optional[str] = None, file_path: Optional[str] = None,
        *, classification: str = 'internal',
    ) -> Tuple[bool, List[SecurityViolation]]:
        found: List[SecurityViolation] = []
        content = self._normalize(content)
        for name, pattern in {**self.CREDENTIAL_PATTERNS, **self.PII_PATTERNS}.items():
            matches = list(re.finditer(pattern, content))
            if name == 'email':
                matches = [m for m in matches if m.group().casefold() not in self.allowed_emails]
            if matches:
                severity = ViolationSeverity.CRITICAL if name in self.CREDENTIAL_PATTERNS else ViolationSeverity.HIGH
                found.append(SecurityViolation(name, f"Detected {name}", severity, market_code, file_path))
        if any(term in content.casefold() for term in self.deny_terms):
            found.append(SecurityViolation('deny_term', 'Restricted organization term detected',
                                           ViolationSeverity.HIGH, market_code, file_path))
        if classification not in {'public', 'internal'}:
            found.append(SecurityViolation('review_required', 'Content requires classification review',
                                           ViolationSeverity.HIGH, market_code, file_path))
        for violation in found:
            self._record_violation(violation)
        return len(found) == 0, found

    def validate_content(
        self, content: str, market_code: Optional[str] = None, file_path: Optional[str] = None,
        *, classification: str = 'internal',
    ) -> Tuple[bool, List[SecurityViolation]]:
        return self.scan_content(content, market_code, file_path, classification=classification)

    @staticmethod
    def _normalize(content: str) -> str:
        return ''.join(c for c in unicodedata.normalize('NFKC', content)
                       if unicodedata.category(c) != 'Cf')

    def validate_file_path(self, file_path: str) -> Tuple[bool, str]:
        path = Path(file_path)
        if ".." in path.parts:
            return False, "path traversal is not allowed"
        if self._is_version_control_path(file_path):
            return False, "version-control internals are not valid learning paths"
        return True, "path is valid"

    def validate_access_marker(self, content: str) -> Tuple[bool, str]:
        if self._has_valid_access_marker(content):
            return True, "access marker found"
        return False, "missing access marker: @public, @internal, @team-private, or @private"

    def _has_valid_access_marker(self, content: str) -> bool:
        lines = content.splitlines()
        if not lines or lines[0].strip() != '---':
            return False
        try:
            end = next(index for index in range(1, len(lines)) if lines[index].strip() == '---')
        except StopIteration:
            return False
        values = [line.split(':', 1)[1].strip().strip('\"\'')
                  for line in lines[1:end] if line.split(':', 1)[0].strip() == 'access' and ':' in line]
        return len(values) == 1 and values[0] in {'@public', '@internal', '@team-private', '@private'}

    def _is_version_control_path(self, file_path: str) -> bool:
        return ".git" in Path(file_path).parts

    def _record_violation(self, violation: SecurityViolation) -> None:
        self.violations.append(violation)
        if self.audit_log_path:
            self.audit_log_path.parent.mkdir(parents=True, exist_ok=True)
            with self.audit_log_path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(violation.to_dict()) + "\n")

    def get_violations(
        self, market_code: Optional[str] = None, severity: Optional[ViolationSeverity] = None
    ) -> List[SecurityViolation]:
        results = self.violations
        if market_code:
            results = [item for item in results if item.market_code == market_code]
        if severity:
            results = [item for item in results if item.severity == severity]
        return results

    def clear_violations(self) -> int:
        count = len(self.violations)
        self.violations = []
        return count

    def export_audit_log(self, output_path: str) -> bool:
        data = [violation.to_dict() for violation in self.violations]
        Path(output_path).write_text(json.dumps(data, indent=2), encoding="utf-8")
        return True


if __name__ == "__main__":
    checker = SecurityChecker()
    print(checker.validate_content("hello"))
