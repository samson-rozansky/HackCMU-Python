from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField, FloatField, SelectField
from wtforms.validators import DataRequired, Length, NumberRange


class EmailComposeForm(FlaskForm):
    email_subject = StringField("Subject", validators=[Length(max=200)])
    email_body = TextAreaField("Body", validators=[DataRequired(), Length(min=1, max=10000)])
    submit = SubmitField("Submit")


class SettingsForm(FlaskForm):
    llm_model_name = StringField("LLM Model Name", validators=[Length(max=100)])
    weight_clarity = FloatField("Clarity", validators=[NumberRange(min=0, max=1)])
    weight_conciseness = FloatField("Conciseness", validators=[NumberRange(min=0, max=1)])
    weight_tone = FloatField("Tone", validators=[NumberRange(min=0, max=1)])
    weight_grammar = FloatField("Grammar", validators=[NumberRange(min=0, max=1)])
    weight_completeness = FloatField("Completeness", validators=[NumberRange(min=0, max=1)])
    weight_politeness = FloatField("Politeness", validators=[NumberRange(min=0, max=1)])
    submit = SubmitField("Save Settings")


class ScenarioCreateForm(FlaskForm):
    difficulty = SelectField(
        "Difficulty",
        choices=[("beginner", "Beginner"), ("intermediate", "Intermediate"), ("advanced", "Advanced")],
        validators=[DataRequired()],
        default="beginner",
    )
    category = StringField("Category (free text)", validators=[Length(max=64)], default="academic")
    focus = StringField("Focus Area (clarity, tone, etc.)", validators=[Length(max=64)], default="clarity")
    submit = SubmitField("Create Scenario")
