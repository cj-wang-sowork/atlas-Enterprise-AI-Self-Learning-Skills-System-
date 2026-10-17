"""Pattern-learning adapter for ATLAS."""

from __future__ import annotations

import hashlib
import json
import logging
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from skill_registry import SkillRegistry, scan_safe
from security_checker import SecurityChecker


class LearningMode(Enum):
    OBSERVATION = "observation"
    ADAPTATION = "adaptation"
    OPTIMIZATION = "optimization"
    EMERGENCY = "emergency"


class PatternType(Enum):
    ACCESS_PATTERN = "access_pattern"
    VIOLATION_PATTERN = "violation_pattern"
    MARKET_BEHAVIOR = "market_behavior"
    SECURITY_RULE = "security_rule"
    PERFORMANCE_METRIC = "performance_metric"


@dataclass
class LearnedPattern:
    pattern_type: PatternType
    pattern_id: str
    market_code: str
    learning_level: str
    pattern_data: Dict[str, Any]
    confidence: float = 0.0
    occurrences: int = 0
    last_updated: datetime = field(default_factory=datetime.utcnow)
    source_data: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["pattern_type"] = self.pattern_type.value
        data["last_updated"] = self.last_updated.isoformat()
        return data


@dataclass
class AdaptationRule:
    rule_id: str
    rule_type: str
    market_code: str
    condition: Dict[str, Any]
    action: Dict[str, Any]
    auto_generated: bool = True
    confidence: float = 0.0
    created_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["created_at"] = self.created_at.isoformat()
        return data


class HermesAdapter:
    """Observes behavior; reusable lessons require verified outcomes and review."""

    def __init__(
        self,
        market_router: Optional[Any] = None,
        learn_system: Optional[Any] = None,
        security_checker: Optional[Any] = None,
        logger: Optional[logging.Logger] = None,
        *,
        scope=None,
        reviewers=(),
        verifiers=(),
        data_dir=None,
    ) -> None:
        self.security_checker = security_checker if security_checker is not None else SecurityChecker()
        self.registry = SkillRegistry(scope, reviewers=reviewers, verifiers=verifiers,
                                      security_checker=self.security_checker, data_dir=data_dir) if scope is not None else None
        self.market_router = market_router
        self.learn_system = learn_system
        self.logger = logger or logging.getLogger(__name__)
        self.learning_mode = LearningMode.OBSERVATION
        self.patterns: Dict[str, LearnedPattern] = {}
        self.adaptation_rules: Dict[str, AdaptationRule] = {}
        self.market_intelligence: Dict[str, Dict[str, Any]] = defaultdict(dict)
        self.learning_history: List[Dict[str, Any]] = []
        self.pattern_confidence_threshold = 0.7

    def observe_access(self, market_code: str, learning_level: str, action: str, success: bool = True) -> None:
        self._observe(
            PatternType.ACCESS_PATTERN,
            market_code,
            learning_level,
            {"action": action, "success": success},
        )

    def observe_violation(
        self, market_code: str, violation_type: str, learning_level: str, severity: str = "warning"
    ) -> None:
        self._observe(
            PatternType.VIOLATION_PATTERN,
            market_code,
            learning_level,
            {"violation_type": violation_type, "severity": severity},
        )

    def learn_market_behavior(self, market_code: str, behavior_data: Dict[str, Any]) -> None:
        self._observe(PatternType.MARKET_BEHAVIOR, market_code, "market", behavior_data)

    def get_adaptive_recommendations(self, market_code: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        return self.registry.recommendations(market_code, context) if self.registry else []

    def _registry(self):
        if self.registry is None:
            raise PermissionError("explicit trusted scope is required for learning")
        return self.registry

    def record_outcome(self, **evidence):
        return self._registry().record_outcome(**evidence)

    def verify_outcome(self, task_id, *, validator):
        return self._registry().verify_outcome(task_id, validator=validator)

    def draft_lesson(self, pattern_id, content, task_ids, *, skill_id=None):
        pattern = self.patterns[pattern_id]
        return self._registry().draft(content=content, task_ids=task_ids,
                                      source=pattern.to_dict(), market_code=pattern.market_code,
                                      condition=pattern.pattern_data, skill_id=skill_id)

    def review_skill(self, skill_id, revision, *, reviewer, decision):
        return self._registry().review(skill_id, revision, reviewer=reviewer, decision=decision)

    def reuse_skill(self, skill_id, revision, *, task_id):
        return self._registry().reuse(skill_id, revision, task_id=task_id)

    def record_reuse_outcome(self, **evidence):
        return self._registry().record_reuse_outcome(**evidence)

    def compare_outcome(self, task_id):
        return self._registry().compare_outcome(task_id)

    def revise_skill(self, skill_id, content, *, task_ids=None):
        return self._registry().revise(skill_id, content, task_ids=task_ids)

    def rollback_skill(self, skill_id, revision, *, reviewer):
        return self._registry().rollback(skill_id, revision, reviewer=reviewer)

    def _observe(
        self, pattern_type: PatternType, market_code: str, learning_level: str, pattern_data: Dict[str, Any]
    ) -> None:
        scan_safe(self.security_checker, [market_code, learning_level, pattern_data])
        key = json.dumps(
            {
                "type": pattern_type.value,
                "market": market_code,
                "level": learning_level,
                "data": pattern_data,
            },
            sort_keys=True,
        )
        pattern_id = self._generate_pattern_id(key)
        pattern = self.patterns.get(
            pattern_id,
            LearnedPattern(pattern_type, pattern_id, market_code, learning_level, pattern_data),
        )
        pattern.occurrences += 1
        pattern.last_updated = datetime.utcnow()
        # Frequency is not correctness evidence (even repeated success claims).
        pattern.confidence = 0.0
        pattern.source_data.append(pattern_type.value)
        self.patterns[pattern_id] = pattern
        self.learning_history.append(pattern.to_dict())

        if self.learning_mode in {LearningMode.ADAPTATION, LearningMode.OPTIMIZATION}:
            self._generate_adaptive_rule(pattern)

    def _generate_adaptive_rule(self, pattern: LearnedPattern) -> bool:
        # Compatibility hook only. Frequency can never authorize reuse.
        return False

    def _generate_pattern_id(self, pattern_key: str) -> str:
        return hashlib.sha256(pattern_key.encode("utf-8")).hexdigest()[:16]

    def set_learning_mode(self, mode: LearningMode) -> None:
        self.learning_mode = mode

    def export_patterns(self, output_path: str) -> bool:
        data = {
            "scope": self.registry.scope if self.registry else None,
            "patterns": [pattern.to_dict() for pattern in self.patterns.values()],
            "skills": self.registry.list_skills() if self.registry else [],
            "rules": [],  # legacy rules have no authority and are not exported
        }
        scan_safe(self.security_checker, data)
        Path(output_path).write_text(json.dumps(data, indent=2, allow_nan=False), encoding="utf-8")
        return True

    def import_patterns(self, input_path: str) -> bool:
        registry = self._registry()
        data = json.loads(Path(input_path).read_text(encoding="utf-8"))
        scan_safe(self.security_checker, data)
        if not isinstance(data, dict) or data.get("scope") != registry.scope:
            raise ValueError("import scope mismatch")
        patterns = {}
        try:
            for raw in data.get("patterns", []):
                item = dict(raw)
                item["pattern_type"] = PatternType(item["pattern_type"])
                item["last_updated"] = datetime.fromisoformat(item["last_updated"])
                item["confidence"] = 0.0
                pattern = LearnedPattern(**item)
                if type(pattern.occurrences) is not int or pattern.occurrences < 1 or not isinstance(pattern.pattern_data, dict):
                    raise ValueError("invalid observation")
                patterns[pattern.pattern_id] = pattern
        except (KeyError, TypeError, AttributeError) as exc:
            raise ValueError("malformed observation import") from exc
        registry.import_bundle(data)  # atomically validates all skills before mutation
        self.patterns.update(patterns)
        return True

    def get_learning_summary(self) -> Dict[str, Any]:
        by_type = Counter(pattern.pattern_type.value for pattern in self.patterns.values())
        by_market = Counter(pattern.market_code for pattern in self.patterns.values())
        states = Counter(skill["state"] for skill in self.registry.list_skills()) if self.registry else Counter()
        return {
            "mode": self.learning_mode.value,
            "patterns": len(self.patterns),
            "rules": states.get("approved", 0),
            "skills_by_state": dict(states),
            "by_type": dict(by_type),
            "by_market": dict(by_market),
        }


if __name__ == "__main__":
    adapter = HermesAdapter()
    adapter.observe_access("us-en", "team", "campaign_read", True)
    print(adapter.get_learning_summary())
