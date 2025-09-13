from __future__ import annotations

import json
from flask import Blueprint, redirect, render_template, request, url_for

from .. import db
from ..forms import EmailComposeForm, ScenarioCreateForm
from ..models import Attempt
from ..services.scenarios import create_scenario, get_scenario
from ..services.llm import evaluate_email
from flask import current_app

scenarios_bp = Blueprint("scenarios", __name__)


@scenarios_bp.route("/scenario/new", methods=["GET", "POST"]) 
def scenario_new():
    form = ScenarioCreateForm()
    if form.validate_on_submit():
        scenario = create_scenario(
            difficulty=form.difficulty.data,
            category=form.category.data or "academic",
            focus_area=form.focus.data or "clarity",
        )
        return redirect(url_for("scenarios.scenario_view", id=scenario.id))
    return render_template("scenario_new.html", form=form)


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
        # If missing, create one for convenience
        scenario = create_scenario()

    form = EmailComposeForm()
    if form.validate_on_submit():
        weights = current_app.config.get("RUBRIC_WEIGHTS", {})
        result = evaluate_email(scenario.scenario_text, form.email_body.data, weights)
        scores = result.get("scores", {})
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
            suggestions=json.dumps(result.get("suggestions", [])),
            rubric_text=result.get("rubric_text", ""),
        )
        # Determine next attempt number for this scenario
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
    suggestions = json.loads(attempt.suggestions or "[]")
    return render_template("result.html", attempt=attempt, suggestions=suggestions)
