from __future__ import annotations

import json
import time
import re
from flask import Blueprint, redirect, render_template, request, url_for, jsonify

from .. import db
from ..forms import EmailComposeForm, ScenarioCreateForm
from ..models import Attempt, Scenario
from ..services.scenarios import create_scenario, get_scenario
from ..services.llm import evaluate_email, generate_scenario_llm
from ..services.presets import get_all_presets, get_preset_by_id
from flask import current_app

scenarios_bp = Blueprint("scenarios", __name__)


def _populate_preset_choices(form: ScenarioCreateForm) -> None:
    choices = [("", "— choose preset —")]
    presets = get_all_presets()
    for level in ["beginner", "intermediate", "advanced"]:
        for p in presets.get(level, []):
            choices.append((p["id"], f"{p['title']} ({level})"))
    form.preset_id.choices = choices


def _normalize_suggestions(raw) -> list[str]:
    if raw is None:
        return []
    # If already a list, stringify items
    if isinstance(raw, list):
        return [str(x).strip() for x in raw if str(x).strip()]
    # If dict, use values
    if isinstance(raw, dict):
        return [str(v).strip() for v in raw.values() if str(v).strip()]
    # If string, try to split sensibly
    if isinstance(raw, str):
        s = raw.strip().replace("\r\n", "\n")
        # Try newline split first
        parts = [p.strip(" -–—•·\t") for p in s.split("\n") if p.strip()]
        if len(parts) > 1:
            return parts
        # Try bullet/numbered split
        tokens = re.split(r"(?:^|\n)\s*(?:[-–—•·]|\d+[.)])\s+", s)
        tokens = [t.strip() for t in tokens if t.strip()]
        if len(tokens) > 1:
            return tokens
        # Fallback: single-item list
        return [s]
    # Anything else
    return [str(raw).strip()]


@scenarios_bp.route("/scenario/new", methods=["GET", "POST"]) 
def scenario_new():
    form = ScenarioCreateForm()
    _populate_preset_choices(form)

    if form.validate_on_submit():
        if form.mode.data == "preset" and form.preset_id.data:
            preset = get_preset_by_id(form.preset_id.data)
            if not preset:
                return render_template("error.html", message="Preset not found"), 404
            scenario = Scenario(
                character_name=preset.get('character_name'),
                character_role=preset.get('character_role'),
                character_image_path=None,
                scenario_text=preset.get('scenario_text', ''),
                difficulty=preset.get('difficulty', form.difficulty.data),
                category=preset.get('category', 'general'),
                success_criteria=json.dumps(preset.get('success_criteria', [])),
                rubric_text=preset.get('rubric_text', ''),
            )
            db.session.add(scenario)
            db.session.commit()
            return redirect(url_for("scenarios.scenario_view", id=scenario.id))
        # Custom with LLM
        try:
            scenario = create_scenario(
                difficulty=form.difficulty.data,
                category=form.category.data or "academic",
                focus_area=form.focus.data or "clarity",
            )
            return redirect(url_for("scenarios.scenario_view", id=scenario.id))
        except Exception:
            pass
        return redirect(url_for(
            'scenarios.scenario_loading',
            difficulty=form.difficulty.data,
            category=form.category.data or 'academic',
            focus=form.focus.data or 'clarity'
        ))

    return render_template("scenario_new.html", form=form)


@scenarios_bp.route("/scenario/loading")
def scenario_loading():
    return render_template("scenario_loading.html")


@scenarios_bp.route("/scenario/generate", methods=["POST"]) 
def scenario_generate():
    difficulty = request.args.get('difficulty', 'beginner')
    category = request.args.get('category', 'academic')
    focus = request.args.get('focus', 'clarity')
    try:
        small = current_app.config.get('OLLAMA_SMALL_MODEL', 'llama3.2:3b')
        parsed = generate_scenario_llm(difficulty, category, focus, small)
        scenario = Scenario(
            character_name=parsed.get('character_name'),
            character_role=parsed.get('character_role'),
            character_image_path=None,
            scenario_text=parsed.get('scenario_text', ''),
            difficulty=difficulty,
            category=category,
            success_criteria=json.dumps(parsed.get('success_criteria', [])),
            rubric_text=parsed.get('rubric_text', ''),
        )
        db.session.add(scenario)
        db.session.commit()
        return jsonify({"id": scenario.id})
    except Exception:
        scenario = create_scenario(difficulty=difficulty, category=category, focus_area=focus)
        return jsonify({"id": scenario.id})


@scenarios_bp.route("/scenario/<int:id>")
def scenario_view(id: int):
    scenario = get_scenario(id)
    if not scenario:
        return render_template("error.html", message="Scenario not found"), 404
    success = json.loads(scenario.success_criteria or "[]")
    return render_template("scenario_view.html", scenario=scenario, success_criteria=success)


@scenarios_bp.route("/attempt/new", methods=["GET", "POST"]) 
def attempt_new():
    scenario_id = request.args.get("scenario_id", type=int)
    scenario = get_scenario(scenario_id) if scenario_id else None
    if not scenario:
        scenario = create_scenario()

    form = EmailComposeForm()
    if form.validate_on_submit():
        weights = current_app.config.get("RUBRIC_WEIGHTS", {})
        result = evaluate_email(scenario.scenario_text, form.email_body.data, weights)
        scores = result.get("scores", {})
        normalized_suggestions = _normalize_suggestions(result.get("suggestions", []))
        attempt = Attempt(
            scenario_id=scenario.id,
            email_subject=form.email_subject.data,
            email_body=form.email_body.data,
            score_clarity=int(scores.get("clarity", 0)),
            score_conciseness=int(scores.get("conciseness", 0)),
            score_tone=int(scores.get("tone", 0)),
            score_grammar=int(scores.get("grammar", 0)),
            score_completeness=int(scores.get("completeness", 0)),
            score_politeness=int(scores.get("politeness", 0)),
            score_total=int(result.get("total", 0)),
            feedback=result.get("feedback", ""),
            suggestions=json.dumps(normalized_suggestions),
            rubric_text=result.get("rubric_text", ""),
        )
        last_attempt = (
            Attempt.query.filter_by(scenario_id=scenario.id)
            .order_by(Attempt.attempt_number.desc())
            .first()
        )
        attempt.attempt_number = (last_attempt.attempt_number + 1) if last_attempt else 1
        db.session.add(attempt)
        db.session.commit()
        return redirect(url_for("scenarios.result_view", attempt_id=attempt.id))

    success = json.loads(scenario.success_criteria or "[]")
    return render_template("compose.html", form=form, scenario=scenario, success_criteria=success)


@scenarios_bp.route("/result/<int:attempt_id>")
def result_view(attempt_id: int):
    attempt = Attempt.query.get(attempt_id)
    if not attempt:
        return render_template("error.html", message="Attempt not found"), 404
    try:
        loaded = json.loads(attempt.suggestions or "[]")
    except Exception:
        loaded = []
    if not isinstance(loaded, list):
        suggestions = _normalize_suggestions(loaded)
    else:
        suggestions = _normalize_suggestions(loaded)
    return render_template("result.html", attempt=attempt, suggestions=suggestions)
