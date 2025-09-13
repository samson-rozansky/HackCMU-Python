from flask import Blueprint, render_template, current_app, request, redirect, url_for, send_file
import io
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

from ..models import Attempt
from ..services.analytics import compute_average_scores, compute_streak_days
from ..services.achievements import compute_achievements_status
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


@main_bp.route("/achievements")
def achievements_page():
    badges = compute_achievements_status()
    return render_template("achievements.html", badges=badges)


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
    plt.setp(ax.get_xticklabels(), rotation=30, ha='right', fontsize=8)
    plt.setp(ax.get_yticklabels(), fontsize=8)
    buf = io.BytesIO()
    plt.tight_layout()
    fig.savefig(buf, format='png')
    plt.close(fig)
    buf.seek(0)
    return send_file(buf, mimetype='image/png')


@main_bp.route("/analytics/chart/radar.png")
def chart_radar_png():
    avg = compute_average_scores()
    labels = ["clarity", "conciseness", "tone", "grammar", "completeness", "politeness"]
    values = [max(0, min(100, avg.get(k, 0))) for k in labels]
    values += values[:1]
    angles = np.linspace(0, 2*np.pi, len(labels), endpoint=False).tolist()
    angles += angles[:1]

    fig = plt.figure(figsize=(4, 4))
    ax = fig.add_subplot(111, polar=True)
    ax.set_theta_offset(np.pi / 2)
    ax.set_theta_direction(-1)

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels([l.capitalize() for l in labels])
    ax.set_rlabel_position(0)
    ax.set_yticks([20, 40, 60, 80, 100])
    ax.set_yticklabels(["20", "40", "60", "80", "100"], fontsize=8)
    ax.set_ylim(0, 100)

    ax.plot(angles, values, color="#58CC02", linewidth=2)
    ax.fill(angles, values, color="#58CC02", alpha=0.25)
    ax.set_title('Average Skill Radar', va='bottom')

    buf = io.BytesIO()
    plt.tight_layout()
    fig.savefig(buf, format='png', bbox_inches='tight')
    plt.close(fig)
    buf.seek(0)
    return send_file(buf, mimetype='image/png')


@main_bp.route("/settings", methods=["GET", "POST"]) 
def settings():
    cfg = current_app.config
    form = SettingsForm()

    if request.args.get('autodetect') == '1':
        try:
            from ..services.ollama import autodetect_and_apply_model_preference
            autodetect_and_apply_model_preference()
        except Exception:
            pass

    if request.method == 'GET':
        form.llm_model_name.data = get_setting('LLM_MODEL_NAME', cfg.get('LLM_MODEL_NAME', ''))
        form.ollama_base_url.data = get_setting('OLLAMA_BASE_URL', cfg.get('OLLAMA_BASE_URL', ''))
        weights = get_setting('RUBRIC_WEIGHTS', cfg.get('RUBRIC_WEIGHTS', {}))
        form.weight_clarity.data = weights.get('clarity', 0.2)
        form.weight_conciseness.data = weights.get('conciseness', 0.15)
        form.weight_tone.data = weights.get('tone', 0.2)
        form.weight_grammar.data = weights.get('grammar', 0.15)
        form.weight_completeness.data = weights.get('completeness', 0.15)
        form.weight_politeness.data = weights.get('politeness', 0.15)

    if form.validate_on_submit():
        set_setting('LLM_MODEL_NAME', form.llm_model_name.data or cfg.get('LLM_MODEL_NAME'))
        if form.ollama_base_url.data:
            set_setting('OLLAMA_BASE_URL', form.ollama_base_url.data)
        set_setting('RUBRIC_WEIGHTS', {
            'clarity': float(form.weight_clarity.data or 0),
            'conciseness': float(form.weight_conciseness.data or 0),
            'tone': float(form.weight_tone.data or 0),
            'grammar': float(form.weight_grammar.data or 0),
            'completeness': float(form.weight_completeness.data or 0),
            'politeness': float(form.weight_politeness.data or 0),
        })
        return redirect(url_for('main.settings'))

    use_mock = request.args.get('mock')
    if use_mock in {'0','1'}:
        cfg['USE_MOCK_LLM'] = (use_mock == '1')

    return render_template('settings.html', form=form)
