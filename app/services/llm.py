import json
import os
import random
import re
from typing import Dict, Any

import requests
from flask import current_app


def _use_mock() -> bool:
    cfg_flag = current_app.config.get("USE_MOCK_LLM")
    if cfg_flag is not None:
        return bool(cfg_flag)
    # Default to real LLM unless explicitly set
    return os.environ.get("USE_MOCK_LLM", "0") == "1"


def _extract_json(blob: str) -> Dict[str, Any]:
    # Try strict parse
    try:
        return json.loads(blob)
    except Exception:
        pass
    # Try to find first {...} block
    m = re.search(r"\{[\s\S]*\}", blob)
    if m:
        try:
            return json.loads(m.group(0))
        except Exception:
            pass
    # Try strip code fences
    blob = blob.strip()
    if blob.startswith("```"):
        blob = re.sub(r"^```[a-zA-Z]*", "", blob).strip()
        blob = re.sub(r"```$", "", blob).strip()
        try:
            return json.loads(blob)
        except Exception:
            pass
    return {}


def _difficulty_guidance(difficulty: str) -> str:
    if difficulty == "beginner":
        return (
            "Provide rich context and concrete hints the learner can follow. Include 3-5 success criteria."
        )
    if difficulty == "intermediate":
        return (
            "Provide moderate context and 2-3 success criteria. Avoid step-by-step hints."
        )
    # advanced
    return (
        "Provide minimal context, avoid explicit hints. Only 1-2 high-level success criteria."
    )


def generate_scenario(difficulty: str, category: str, focus_area: str) -> Dict[str, Any]:
    if _use_mock():
        # More specific mock based on difficulty/category
        seeds = {
            "academic": [
                "Write to your professor requesting rounding your 89.4% to 90% due to consistent top-quartile performance and extra credit completed.",
                "Email your TA to ask for a regrade on Question 3 citing rubric misinterpretation.",
                "Request a deadline extension for your literature review due to conference travel with attached itinerary.",
            ],
            "business": [
                "Negotiate a 5% delivery delay with a client after a supplier recall; propose mitigation and revised timeline.",
                "Ask your manager to approve a $1,200 budget increase for user testing with data-backed rationale.",
                "Escalate a production incident summary to the VP with clear next steps and owners.",
            ],
            "personal": [
                "Ask your mentor for a recommendation letter highlighting two recent projects and deadlines.",
                "Email a club president to propose merging overlapping workshops into one event.",
                "Request a landlord repair with photos and proposed appointment windows.",
            ],
        }
        bucket = "academic" if "acad" in category.lower() or "prof" in category.lower() else (
            "business" if any(k in category.lower() for k in ["client", "manager", "work", "biz", "company", "salary"]) else "personal"
        )
        text = random.choice(seeds[bucket])
        # Guidance tuning
        if difficulty == "beginner":
            success = [
                "Open with specific course/subject and your identifier",
                "State the request clearly with concrete rationale",
                "Cite at least one piece of evidence",
                "Propose a realistic next step/date",
                "Maintain a respectful tone",
            ]
        elif difficulty == "intermediate":
            success = [
                "Clear request with concise rationale",
                "One evidence point",
                "Proposed next step",
            ]
        else:
            success = ["Clear request", "Professional tone"]
        name = random.choice(["Dr. Avery", "Prof. Kim", "Jordan Patel", "Sam Rivera"])
        role = random.choice(["Professor", "Manager", "Client Success Lead", "TA"])
        return {
            "character_name": name,
            "character_role": role,
            "scenario_text": text,
            "success_criteria": success,
            "tone": "professional, confident, concise",
        }

    # Attempt to call a local LLM if configured (best-effort)
    base_url = current_app.config.get("OLLAMA_BASE_URL")
    model = current_app.config.get("LLM_MODEL_NAME", "llama3.1")
    guidance = _difficulty_guidance(difficulty)
    prompt = (
        "Generate a highly specific, realistic professional email scenario. Avoid generic situations.\n"
        "Include:\n- Character name & role\n- Situation context (numbers/dates if relevant)\n- Specific challenge/request\n- Success criteria list tuned to difficulty\n- Tone requirements\n- Key information that must be included\n"
        f"Difficulty: {difficulty} (Guidance: {guidance})\n"
        f"Category (free text): {category}\nFocus Area: {focus_area}\n"
        "Return ONLY valid JSON with keys: character_name, character_role, scenario_text, success_criteria (list sized to difficulty), tone."
    )
    try:
        resp = requests.post(
            f"{base_url}/api/generate",
            json={"model": model, "prompt": prompt, "stream": False},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json().get("response", "{}")
        parsed = _extract_json(data)
        if parsed:
            return parsed
        raise ValueError("Malformed LLM scenario JSON")
    except Exception:
        # Switch to mock mode to avoid recursion then return mock result
        os.environ["USE_MOCK_LLM"] = "1"
        current_app.config["USE_MOCK_LLM"] = True
        return generate_scenario(difficulty, category, focus_area)


essential_skills = [
    "clarity",
    "conciseness",
    "tone",
    "grammar",
    "completeness",
    "politeness",
]


def evaluate_email(scenario_text: str, email_body: str, weights: Dict[str, float]) -> Dict[str, Any]:
    if _use_mock():
        # Deterministic-ish based on length and simple heuristics
        length = len(email_body)
        base = min(100, 40 + length // 40)
        random.seed(len(email_body) + len(scenario_text))
        scores = {
            "clarity": min(100, base + random.randint(-10, 10)),
            "conciseness": min(100, max(40, 100 - (length // 60) + random.randint(-10, 10))),
            "tone": min(100, base + random.randint(-10, 10)),
            "grammar": min(100, base + random.randint(-10, 10)),
            "completeness": min(100, base + random.randint(-10, 10)),
            "politeness": min(100, base + random.randint(-10, 10)),
        }
        total = int(sum(scores[k] * weights.get(k, 0) for k in scores))
        rubric_text = (
            "Rubric (mock): clarity, conciseness, tone, grammar, completeness, politeness."
        )
        feedback = (
            "This is a mock evaluation. Focus on being specific, concise, and polite."
        )
        suggestions = [
            "Open with a clear purpose line.",
            "Trim redundant phrases to improve conciseness.",
            "Close with a concrete next step and thanks.",
        ]
        return {"scores": scores, "total": total, "feedback": feedback, "suggestions": suggestions, "rubric_text": rubric_text}

    # If not mocking, do a best-effort local call expecting JSON in the response
    base_url = current_app.config.get("OLLAMA_BASE_URL")
    model = current_app.config.get("LLM_MODEL_NAME", "llama3.1")
    w_json = json.dumps(weights)
    prompt = (
        "Evaluate the email using this rubric (0–100 each):\n"
        "1) Clarity 2) Conciseness 3) Tone 4) Grammar/Spelling 5) Completeness 6) Politeness\n"
        f"Rubric weights: {w_json}\n"
        f"Scenario: {scenario_text}\n"
        f"Email: {email_body}\n"
        "Return ONLY valid JSON with keys: \n"
        "scores (object with clarity, conciseness, tone, grammar, completeness, politeness 0-100),\n"
        "total (weighted 0-100), feedback (string), suggestions (array of strings), rubric_text (string with short scoring guidelines)."
    )
    try:
        resp = requests.post(
            f"{base_url}/api/generate",
            json={"model": model, "prompt": prompt, "stream": False},
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json().get("response", "{}")
        parsed = _extract_json(data)
        if parsed and "scores" in parsed and "total" in parsed:
            return parsed
        raise ValueError("Malformed LLM evaluation JSON")
    except Exception:
        # Fallback to mock with note
        os.environ["USE_MOCK_LLM"] = "1"
        current_app.config["USE_MOCK_LLM"] = True
        return evaluate_email(scenario_text, email_body, weights)
