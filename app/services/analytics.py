from __future__ import annotations

from typing import Dict, List
from datetime import timedelta

from ..models import Attempt


def compute_average_scores() -> Dict[str, float]:
    attempts: List[Attempt] = Attempt.query.all()
    if not attempts:
        return {k: 0.0 for k in [
            "clarity", "conciseness", "tone", "grammar", "completeness", "politeness", "total"
        ]}
    n = len(attempts)
    sums = {
        "clarity": sum(a.score_clarity or 0 for a in attempts),
        "conciseness": sum(a.score_conciseness or 0 for a in attempts),
        "tone": sum(a.score_tone or 0 for a in attempts),
        "grammar": sum(a.score_grammar or 0 for a in attempts),
        "completeness": sum(a.score_completeness or 0 for a in attempts),
        "politeness": sum(a.score_politeness or 0 for a in attempts),
        "total": sum(a.score_total or 0 for a in attempts),
    }
    return {k: (v / n if n else 0.0) for k, v in sums.items()}


def compute_streak_days() -> int:
    attempts: List[Attempt] = Attempt.query.order_by(Attempt.submitted_at.desc()).all()
    if not attempts:
        return 0
    unique_days = []
    seen = set()
    for a in attempts:
        if not a.submitted_at:
            continue
        d = a.submitted_at.date()
        if d not in seen:
            seen.add(d)
            unique_days.append(d)
    if not unique_days:
        return 0
    unique_days.sort(reverse=True)
    streak = 1
    prev = unique_days[0]
    for d in unique_days[1:]:
        if (prev - d) == timedelta(days=1):
            streak += 1
            prev = d
        else:
            break
    return streak
