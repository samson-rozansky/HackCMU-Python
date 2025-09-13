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
    return os.environ.get("USE_MOCK_LLM", "0") == "1"


def _extract_json(blob: str) -> Dict[str, Any]:
    try:
        return json.loads(blob)
    except Exception:
        pass
    m = re.search(r"\{[\s\S]*\}", blob)
    if m:
        try:
            return json.loads(m.group(0))
        except Exception:
            pass
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
    return (
        "Provide minimal context, avoid explicit hints. Only 1-2 high-level success criteria."
    )


def _ollama_generate(prompt: str, model: str, timeout: int = 10) -> Dict[str, Any]:
    base_url = current_app.config.get("OLLAMA_BASE_URL")
    resp = requests.post(
        f"{base_url}/api/generate",
        json={"model": model, "prompt": prompt, "stream": False},
        timeout=timeout,
    )
    resp.raise_for_status()
    data = resp.json().get("response", "{}")
    return _extract_json(data)


def generate_scenario_llm(difficulty: str, category: str, focus_area: str, model: str) -> Dict[str, Any]:
    guidance = _difficulty_guidance(difficulty)
    prompt = (
        "You are generating ONLY a scenario JSON, NOT an email. Never write the email body.\n"
        "Output must be a single JSON object, no commentary.\n"
        "Create a highly specific, realistic professional email scenario. Avoid generic situations.\n"
        "Include the following keys: \n"
        "- character_name (string)\n- character_role (string)\n- scenario_text (string; detailed context, numbers/dates if relevant)\n"
        "- success_criteria (array; tuned to difficulty)\n- tone (string)\n- rubric_text (string; short scoring guidelines matching the success criteria)\n"
        f"Difficulty: {difficulty} (Guidance: {guidance})\n"
        f"Category (free text): {category}\nFocus Area: {focus_area}\n"
        "Return ONLY valid JSON with those keys. Do NOT include the email itself."
    )
    return _ollama_generate(prompt, model, timeout=12)


def generate_scenario(difficulty: str, category: str, focus_area: str) -> Dict[str, Any]:
    if not _use_mock():
        try:
            model = current_app.config.get("LLM_MODEL_NAME", "llama3.1")
            parsed = generate_scenario_llm(difficulty, category, focus_area, model)
            if parsed:
                return parsed
        except Exception:
            pass
        try:
            small = current_app.config.get("OLLAMA_SMALL_MODEL", "llama3.2:3b")
            parsed = generate_scenario_llm(difficulty, category, focus_area, small)
            if parsed:
                return parsed
        except Exception:
            pass

    # Mock fallback now also returns rubric_text
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
    rubric_text = (
        "Scores prioritize clarity and tone; include one concrete evidence point and propose a realistic next step."
    )
    return {
        "character_name": name,
        "character_role": role,
        "scenario_text": text,
        "success_criteria": success,
        "tone": "professional, confident, concise",
        "rubric_text": rubric_text,
    }


essential_skills = [
    "clarity",
    "conciseness",
    "tone",
    "grammar",
    "completeness",
    "politeness",
]


def evaluate_email(scenario_text: str, email_body: str, weights: Dict[str, float]) -> Dict[str, Any]:
    # unchanged from previous step
    if _use_mock():
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

    base_url = current_app.config.get("OLLAMA_BASE_URL")
    model = current_app.config.get("LLM_MODEL_NAME", "llama3.1")
    w_json = json.dumps(weights)
    prompt = (
        "Evaluate the email using this rubric (0–100 each). Return ONLY JSON.\n"
        "Required keys: scores, total, feedback, suggestions, rubric_text.\n"
        "scores must include clarity, conciseness, tone, grammar, completeness, politeness (0-100).\n"
        f"Rubric weights: {w_json}\n"
        f"Scenario: {scenario_text}\n"
        f"Email: {email_body}"
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
        try:
            small = current_app.config.get("OLLAMA_SMALL_MODEL", "llama3.2:3b")
            resp = requests.post(
                f"{base_url}/api/generate",
                json={"model": small, "prompt": prompt, "stream": False},
                timeout=8,
            )
            resp.raise_for_status()
            data = resp.json().get("response", "{}")
            parsed = _extract_json(data)
            if parsed and "scores" in parsed and "total" in parsed:
                return parsed
        except Exception:
            pass
        return evaluate_email.__wrapped__(scenario_text, email_body, weights)  # type: ignore
