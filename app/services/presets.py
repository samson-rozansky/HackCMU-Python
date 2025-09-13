from __future__ import annotations

from typing import Dict, List, Optional


def _presets() -> Dict[str, List[dict]]:
    return {
        "beginner": [
            {
                "id": "beg_prof_round_90",
                "title": "Professor: Round 89.4% to 90%",
                "difficulty": "beginner",
                "category": "academic",
                "character_name": "Prof. Elena Kim",
                "character_role": "Professor",
                "scenario_text": (
                    "You earned an 89.4% in CS210. You consistently scored in the top quartile and completed all extra credit. "
                    "The syllabus allows rounding at instructor discretion. Request rounding to 90% and offer to discuss briefly in office hours."
                ),
                "success_criteria": [
                    "Identify course and your section/ID",
                    "State rounding request clearly",
                    "Cite consistent performance or extra credit",
                    "Offer a brief follow-up window",
                    "Polite, appreciative tone",
                ],
                "rubric_text": (
                    "Clarity: clear request and course details; Conciseness: <150 words; Tone: respectful; "
                    "Completeness: includes rationale and availability; Politeness: appreciative close."
                ),
            },
            {
                "id": "beg_client_delay",
                "title": "Client: Minor Delivery Delay",
                "difficulty": "beginner",
                "category": "business",
                "character_name": "Jordan Patel",
                "character_role": "Client Success Lead",
                "scenario_text": (
                    "A supplier recall causes a 3–5 day delay on a non-critical feature. Notify the client, propose a fallback, and share a revised ETA."
                ),
                "success_criteria": [
                    "Acknowledge issue and impact",
                    "Provide revised timeline",
                    "Propose mitigation",
                    "Invite questions",
                    "Maintain confident, calm tone",
                ],
                "rubric_text": (
                    "Clarity: state delay and new date; Conciseness: avoid fluff; Tone: calm/assuring; "
                    "Completeness: includes mitigation; Politeness: professional close."
                ),
            },
            {
                "id": "beg_deadline_extension",
                "title": "Professor: Deadline Extension",
                "difficulty": "beginner",
                "category": "academic",
                "character_name": "Dr. Ravi Shah",
                "character_role": "Professor",
                "scenario_text": (
                    "You will be traveling for a family obligation during the project deadline week. Request a 72-hour extension and propose a new submission date."
                ),
                "success_criteria": [
                    "State reason briefly",
                    "Propose specific new date",
                    "Confirm you understand policies",
                    "Offer to share proof if needed",
                    "Polite tone",
                ],
                "rubric_text": (
                    "Clarity: reason and ask; Tone: respectful; Completeness: new date; Conciseness: <150 words; Politeness."
                ),
            },
        ],
        "intermediate": [
            {
                "id": "int_grade_appeal_q3",
                "title": "TA: Grade Appeal (Q3 Rubric)",
                "difficulty": "intermediate",
                "category": "academic",
                "character_name": "Alex Rivera",
                "character_role": "TA",
                "scenario_text": (
                    "You believe rubric criteria for Question 3 were misapplied. Reference rubric line items and explain where your answer meets them."
                ),
                "success_criteria": [
                    "Reference rubric criteria by name/number",
                    "Point to specific lines in your answer",
                    "Request re-evaluation succinctly",
                ],
                "rubric_text": (
                    "Clarity: specific rubric references; Conciseness; Tone: neutral/professional; Completeness: includes example lines."
                ),
            },
            {
                "id": "int_salary_negotiation",
                "title": "HR: Salary Negotiation",
                "difficulty": "intermediate",
                "category": "business",
                "character_name": "Morgan Lee",
                "character_role": "Recruiter",
                "scenario_text": (
                    "You received an offer below market by ~8–12%. Provide data-backed range, reiterate enthusiasm, and request an adjusted base."
                ),
                "success_criteria": [
                    "Express enthusiasm",
                    "Provide market data range",
                    "Make a clear ask",
                ],
                "rubric_text": (
                    "Clarity: explicit request; Tone: confident/positive; Conciseness; Completeness: includes data."
                ),
            },
        ],
        "advanced": [
            {
                "id": "adv_exec_escalation",
                "title": "Executive Escalation: Incident Summary",
                "difficulty": "advanced",
                "category": "business",
                "character_name": "Dana Brooks",
                "character_role": "VP Engineering",
                "scenario_text": (
                    "After a sev-2 outage (47 minutes), send an executive-ready summary with root cause hypothesis, impact, and owners for next steps."
                ),
                "success_criteria": [
                    "Impact in numbers",
                    "Root cause hypothesis",
                    "Owners and next steps",
                ],
                "rubric_text": (
                    "Clarity: crisp executive summary; Tone: accountable; Completeness: impact + owners; Conciseness."
                ),
            },
            {
                "id": "adv_client_concession",
                "title": "Client: Price Concession Trade",
                "difficulty": "advanced",
                "category": "business",
                "character_name": "Taylor Ng",
                "character_role": "Client Director",
                "scenario_text": (
                    "Client requests a 7% discount. Propose a conditional concession tied to volume/term while protecting margins."
                ),
                "success_criteria": [
                    "Conditional concession",
                    "Protect margin language",
                    "Next-step proposal",
                ],
                "rubric_text": (
                    "Clarity: condition structure; Tone: firm but collaborative; Completeness: terms; Conciseness."
                ),
            },
        ],
    }


def get_all_presets() -> Dict[str, List[dict]]:
    return _presets()


def get_preset_by_id(preset_id: str) -> Optional[dict]:
    for group in _presets().values():
        for p in group:
            if p["id"] == preset_id:
                return p
    return None
