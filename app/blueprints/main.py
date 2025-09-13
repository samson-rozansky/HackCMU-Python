from flask import Blueprint, render_template, current_app, request, redirect, url_for, send_file
import io
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from ..models import Attempt
from ..services.analytics import compute_average_scores, compute_streak_days
from ..forms import SettingsForm
from ..services.settings import set_setting, get_setting

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def dashboard():
    avg = compute_average_scores()
    recent_attempts = Attempt.query.order_by(Attempt.submitted_at.desc()).limit(10).all()
    streak = compute_streak_days()
    return render_template("dashboard.html", avg=avg, recent_attempts=recent_attempts, streak=streak)


@main_bp.route("/history")
def history():
    attempts = Attempt.query.order_by(Attempt.submitted_at.desc()).all()
    return render_template("history.html", attempts=attempts)


@main_bp.route("/analytics")
def analytics_page():
    return render_template("analytics.html")


@main_bp.route("/analytics/chart/trend.png")
def chart_trend_png():
    attempts = Attempt.query.order_by(Attempt.submitted_at.asc()).all()
    x = list(range(1, len(attempts) + 1))
    y = [a.score_total or 0 for a in attempts]
    fig, ax = plt.subplots(figsize=(5, 3))
    ax.plot(x, y, marker='o')
    ax.set_title('Total Score Trend')
    ax.set_xlabel('Attempt #')
    ax.set_ylabel('Score')
    ax.set_ylim(0, 100)
    buf = io.BytesIO()
    plt.tight_layout()
    fig.savefig(buf, format='png')
    plt.close(fig)
    buf.seek(0)
    return send_file(buf, mimetype='image/png')


@main_bp.route("/analytics/chart/skills.png")
def chart_skills_png():
    avg = compute_average_scores()
    labels = ["clarity", "conciseness", "tone", "grammar", "completeness", "politeness"]
    values = [avg.get(k, 0) for k in labels]
    fig, ax = plt.subplots(figsize=(5, 3))
    ax.bar(labels, values)
    ax.set_title('Average Skill Breakdown')
    ax.set_ylim(0, 100)
    plt.xticks(rotation=30)
    buf = io.BytesIO()
    plt.tight_layout()
    fig.savefig(buf, format='png')
    plt.close(fig)
    buf.seek(0)
    return send_file(buf, mimetype='image/png')


@main_bp.route("/settings", methods=["GET", "POST"]) 
def settings():
    cfg = current_app.config
    form = SettingsForm()
    if request.method == 'GET':
        form.llm_model_name.data = get_setting('LLM_MODEL_NAME', cfg.get('LLM_MODEL_NAME', ''))
        weights = get_setting('RUBRIC_WEIGHTS', cfg.get('RUBRIC_WEIGHTS', {}))
        form.weight_clarity.data = weights.get('clarity', 0.2)
        form.weight_conciseness.data = weights.get('conciseness', 0.15)
        form.weight_tone.data = weights.get('tone', 0.2)
        form.weight_grammar.data = weights.get('grammar', 0.15)
        form.weight_completeness.data = weights.get('completeness', 0.15)
        form.weight_politeness.data = weights.get('politeness', 0.15)

    if form.validate_on_submit():
        set_setting('LLM_MODEL_NAME', form.llm_model_name.data or cfg.get('LLM_MODEL_NAME'))
        set_setting('RUBRIC_WEIGHTS', {
            'clarity': float(form.weight_clarity.data or 0),
            'conciseness': float(form.weight_conciseness.data or 0),
            'tone': float(form.weight_tone.data or 0),
            'grammar': float(form.weight_grammar.data or 0),
            'completeness': float(form.weight_completeness.data or 0),
            'politeness': float(form.weight_politeness.data or 0),
        })
        return redirect(url_for('main.settings'))

    # Toggle mock vs real via query param for quick testing
    use_mock = request.args.get('mock')
    if use_mock in {'0','1'}:
        cfg['USE_MOCK_LLM'] = (use_mock == '1')

    return render_template('settings.html', form=form)
