from __future__ import annotations

from typing import List, Dict
from datetime import timedelta

from ..models import Attempt


def _catalog() -> List[Dict[str, str]]:
    return [
        {"id": "perfect", "name": "Perfection!", "desc": "Earned a perfect 100% once."},
        {"id": "zero", "name": "Rock Bottom", "desc": "Scored 0% once (we all start somewhere)."},
        {"id": "fifty", "name": "Perfectly Average", "desc": "Hit exactly 50% once."},
        {"id": "clarity_master", "name": "Clarity Master", "desc": "Scored ≥95 in Clarity three times."},
        {"id": "conciseness_master", "name": "Conciseness Master", "desc": "Scored ≥95 in Conciseness three times."},
        {"id": "tone_master", "name": "Tone Master", "desc": "Scored ≥95 in Tone three times."},
        {"id": "grammar_master", "name": "Grammar Master", "desc": "Scored ≥95 in Grammar three times."},
        {"id": "completeness_master", "name": "Completeness Master", "desc": "Scored ≥95 in Completeness three times."},
        {"id": "politeness_master", "name": "Politeness Master", "desc": "Scored ≥95 in Politeness three times."},
        {"id": "consistent", "name": "Consistent Performer", "desc": "Five attempts with 80% or higher."},
        {"id": "comeback", "name": "Comeback", "desc": "Improved by 20+ points in one attempt."},
        {"id": "streak", "name": "Streak Starter", "desc": "Practiced on 3 or more different days."},
        {"id": "secret", "name": "???", "desc": "You discovered a secret condition."},
    ]


def compute_achievements() -> List[Dict[str, str]]:
    attempts: List[Attempt] = Attempt.query.order_by(Attempt.submitted_at.asc()).all()
    badges: List[Dict[str, str]] = []
    if not attempts:
        return badges

    totals = [a.score_total or 0 for a in attempts]

    if any(t == 100 for t in totals):
        badges.append({"name": "Perfection!", "desc": "Earned a perfect 100% once."})
    if any(t == 0 for t in totals):
        badges.append({"name": "Rock Bottom", "desc": "Scored 0% once (we all start somewhere)."})
    if any(t == 50 for t in totals):
        badges.append({"name": "Perfectly Average", "desc": "Hit exactly 50% once."})

    def at_least_three(getattr_name: str) -> bool:
        scores = [getattr(a, getattr_name) or 0 for a in attempts]
        return sum(1 for s in scores if s >= 95) >= 3

    if at_least_three("score_clarity"):
        badges.append({"name": "Clarity Master", "desc": "Scored ≥95 in Clarity three times."})
    if at_least_three("score_conciseness"):
        badges.append({"name": "Conciseness Master", "desc": "Scored ≥95 in Conciseness three times."})
    if at_least_three("score_tone"):
        badges.append({"name": "Tone Master", "desc": "Scored ≥95 in Tone three times."})
    if at_least_three("score_grammar"):
        badges.append({"name": "Grammar Master", "desc": "Scored ≥95 in Grammar three times."})
    if at_least_three("score_completeness"):
        badges.append({"name": "Completeness Master", "desc": "Scored ≥95 in Completeness three times."})
    if at_least_three("score_politeness"):
        badges.append({"name": "Politeness Master", "desc": "Scored ≥95 in Politeness three times."})

    if sum(1 for t in totals if t >= 80) >= 5:
        badges.append({"name": "Consistent Performer", "desc": "Five attempts with 80% or higher."})

    for prev, cur in zip(totals, totals[1:]):
        if (cur - prev) >= 20:
            badges.append({"name": "Comeback", "desc": "Improved by 20+ points in one attempt."})
            break

    unique_days = []
    seen = set()
    for a in attempts:
        if a.submitted_at:
            d = a.submitted_at.date()
            if d not in seen:
                seen.add(d)
                unique_days.append(d)
    if len(unique_days) >= 3:
        badges.append({"name": "Streak Starter", "desc": "Practiced on 3 or more different days."})

    if any((a.score_tone or 0) == 73 for a in attempts):
        badges.append({"name": "???", "desc": "You discovered a secret condition."})

    return badges


def compute_achievements_status() -> List[Dict[str, str]]:
    unlocked = {b["name"] for b in compute_achievements()}
    status: List[Dict[str, str]] = []
    for ach in _catalog():
        entry = dict(ach)
        entry["unlocked"] = "true" if ach["name"] in unlocked else "false"
        status.append(entry)
    return status
