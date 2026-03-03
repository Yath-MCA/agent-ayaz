"""Risk Engine — dynamic risk scoring for execution plans.

Risk scale: 1 (safe) to 10 (critical).
Destructive, production, and restart commands raise the score.
"""

from dataclasses import dataclass, field
from typing import Optional

HIGH_RISK_KEYWORDS = [
    "rm ", "del ", "remove-item", "format", "shutdown", "restart",
    "drop ", "truncate", "delete from", "wipe", "kill",
]
MEDIUM_RISK_KEYWORDS = [
    "deploy", "push", "release", "publish", "migrate",
    "overwrite", "force", "--force", "-f ",
]
PRODUCTION_SIGNALS = ["prod", "production", "live", "main", "master"]


@dataclass
class RiskResult:
    score: int                        # 1–10
    level: str                        # low | medium | high | critical
    reasons: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {"score": self.score, "level": self.level, "reasons": self.reasons}


def _level(score: int) -> str:
    if score <= 2: return "low"
    if score <= 5: return "medium"
    if score <= 7: return "high"
    return "critical"


def score_plan(
    command: Optional[str],
    project: Optional[str],
    plan_type: str,
    auto_approve: bool,
) -> RiskResult:
    score = 1
    reasons: list[str] = []

    cmd_lower = (command or "").lower()
    proj_lower = (project or "").lower()

    for kw in HIGH_RISK_KEYWORDS:
        if kw in cmd_lower:
            score += 4
            reasons.append(f"High-risk keyword: '{kw.strip()}'")
            break

    for kw in MEDIUM_RISK_KEYWORDS:
        if kw in cmd_lower:
            score += 2
            reasons.append(f"Medium-risk keyword: '{kw.strip()}'")
            break

    for sig in PRODUCTION_SIGNALS:
        if sig in proj_lower or sig in cmd_lower:
            score += 2
            reasons.append(f"Production signal: '{sig}'")
            break

    if plan_type == "command" and not auto_approve:
        score += 1
        reasons.append("Manual approval required")

    if not reasons:
        reasons.append("No risk factors detected")

    score = min(score, 10)
    return RiskResult(score=score, level=_level(score), reasons=reasons)
