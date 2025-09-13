from datetime import datetime

from . import db


class Scenario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    character_name = db.Column(db.String(120))
    character_role = db.Column(db.String(120))
    character_image_path = db.Column(db.String(256))
    scenario_text = db.Column(db.Text, nullable=False)
    difficulty = db.Column(db.String(32))  # 'beginner'|'intermediate'|'advanced'
    category = db.Column(db.String(64))  # business/academic/personal
    success_criteria = db.Column(db.Text)  # JSON string list
    generated_at = db.Column(db.DateTime, default=datetime.utcnow)

    attempts = db.relationship("Attempt", backref="scenario", lazy=True)


class Attempt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    scenario_id = db.Column(db.Integer, db.ForeignKey("scenario.id"), nullable=False)
    email_subject = db.Column(db.String(200))
    email_body = db.Column(db.Text, nullable=False)
    score_clarity = db.Column(db.Integer)
    score_conciseness = db.Column(db.Integer)
    score_tone = db.Column(db.Integer)
    score_grammar = db.Column(db.Integer)
    score_completeness = db.Column(db.Integer)
    score_politeness = db.Column(db.Integer)
    score_total = db.Column(db.Integer)
    feedback = db.Column(db.Text)  # freeform
    suggestions = db.Column(db.Text)  # JSON string list
    rubric_text = db.Column(db.Text)  # LLM-provided rubric/guidelines
    attempt_number = db.Column(db.Integer, default=1)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)


class ProgressSnapshot(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    taken_at = db.Column(db.DateTime, default=datetime.utcnow)
    total_scenarios = db.Column(db.Integer)
    average_score = db.Column(db.Float)
    skill_breakdown = db.Column(db.Text)  # JSON map
    streak_days = db.Column(db.Integer)
    achievements = db.Column(db.Text)  # JSON list
    weaknesses = db.Column(db.Text)  # JSON list


class AppSetting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(128), unique=True, nullable=False)
    value = db.Column(db.Text, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
