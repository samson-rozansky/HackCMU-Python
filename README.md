# Email Communication Game — Flask/Python Specification

## 0) Tech Stack (simple)

* **Python 3.11+**
* **Flask** (server-rendered Jinja templates; Blueprints)
* **Flask-SQLAlchemy** + **SQLite** (local storage)
* **Flask-Migrate** (alembic migrations)
* **Flask-WTF** (forms + CSRF)
* **Flask-Login** (optional, single-user is fine for hackathon)
* **Requests/httpx** (call local LLM APIs like Ollama)
* **Pillow** (optional: simple pixel avatar handling)
* **Matplotlib** (server-side PNG charts for analytics; no client JS)
* **CSV export** (standard library)

> No front-end framework. Server-rendered pages, plain `<textarea>` for email body (you can add a light JS editor later if you want).

---

## 1) Core Concept

Duolingo-style, but for professional email writing: generate a scenario → user writes email → local LLM grades via rubric → feedback → retry → progress tracking.

---

## 2) App Structure

```
email-game/
├─ app/
│  ├─ __init__.py          # create_app(), db, login_manager
│  ├─ models.py            # SQLAlchemy models
│  ├─ forms.py             # WTForms: EmailComposeForm, SettingsForm
│  ├─ services/
│  │  ├─ llm.py            # Scenario + Evaluation (Ollama HTTP wrapper)
│  │  ├─ scenarios.py      # scenario CRUD/generation orchestration
│  │  └─ analytics.py      # aggregates + matplotlib chart PNGs
│  ├─ blueprints/
│  │  ├─ main.py           # dashboard, history, analytics
│  │  ├─ scenarios.py      # new/view scenario, compose, submit
│  │  └─ exports.py        # CSV/JSON exports
│  ├─ templates/
│  │  ├─ base.html
│  │  ├─ dashboard.html
│  │  ├─ scenario_view.html
│  │  ├─ compose.html
│  │  ├─ result.html
│  │  ├─ history.html
│  │  ├─ analytics.html
│  │  └─ settings.html
│  └─ static/
│     ├─ css/ styles.css
│     └─ avatars/ (optional pixel sprites)
├─ migrations/             # alembic
├─ config.py               # SQLite path, LLM endpoints, secrets
├─ run.py                  # flask run entrypoint
└─ requirements.txt
```

---

## 3) Routes (server-rendered)

| Method   | Path                        | Purpose                                                      |
| -------- | --------------------------- | ------------------------------------------------------------ |
| GET      | `/`                         | Dashboard: quick stats, “Start New Scenario”                 |
| GET      | `/scenario/new`             | Generate and persist a new scenario (LLM) → redirect to view |
| GET      | `/scenario/<id>`            | Show scenario (context, criteria, avatar) + “Compose”        |
| GET/POST | `/attempt/new?scenario_id=` | Compose/submit email; on POST call evaluator                 |
| GET      | `/result/<attempt_id>`      | Show scores, feedback, suggestions, retry button             |
| GET      | `/history`                  | Paginated attempts; filters by difficulty/category           |
| GET      | `/analytics`                | Server-generated PNG charts (trend, radar)                   |
| GET      | `/export/csv`               | CSV export of attempts                                       |
| GET/POST | `/settings`                 | Difficulty focus areas, rubric weights, LLM model names      |

---

## 4) Game Loop (unchanged, Flaskified)

1. **Scenario Generation (LLM)** → store `Scenario`
2. **(Optional) Avatar**: choose from static sprites or simple Pillow pipeline
3. **Compose**: server form with Subject + Body (`<textarea>`)
4. **Evaluate (LLM)**: send scenario+email; receive scores (0–100 per metric) + feedback
5. **Persist Attempt**: scores, suggestions; display results
6. **Iterate**: “Try Again” prefills previous body; new attempt number increments
7. **Track**: update aggregates for analytics, streaks, weaknesses

---

## 5) Scoring Rubric (weights)

* Clarity 20%, Conciseness 15%, Tone 20%, Grammar 15%, Completeness 15%, Politeness 15%
  Total 0–100 (weighted). Weights editable in `/settings`.

---

## 6) Difficulty & Scenario Types

* **Beginner / Intermediate / Advanced**
* **Categories**: Business, Academic, Personal-Professional
* Examples retained from your list (deadline extension, grade appeal, salary negotiation, etc.). Use them as seed prompts when not using full LLM generation.

---

## 7) Data Models (SQLAlchemy)

```python
# models.py
from app import db
from datetime import datetime

class Scenario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    character_name = db.Column(db.String(120))
    character_role = db.Column(db.String(120))
    character_image_path = db.Column(db.String(256))
    scenario_text = db.Column(db.Text, nullable=False)
    difficulty = db.Column(db.String(32))   # 'beginner'|'intermediate'|'advanced'
    category = db.Column(db.String(64))     # business/academic/personal
    success_criteria = db.Column(db.Text)   # JSON string list
    generated_at = db.Column(db.DateTime, default=datetime.utcnow)

class Attempt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    scenario_id = db.Column(db.Integer, db.ForeignKey('scenario.id'), nullable=False)
    email_subject = db.Column(db.String(200))
    email_body = db.Column(db.Text, nullable=False)
    score_clarity = db.Column(db.Integer)
    score_conciseness = db.Column(db.Integer)
    score_tone = db.Column(db.Integer)
    score_grammar = db.Column(db.Integer)
    score_completeness = db.Column(db.Integer)
    score_politeness = db.Column(db.Integer)
    score_total = db.Column(db.Integer)
    feedback = db.Column(db.Text)           # freeform
    suggestions = db.Column(db.Text)        # JSON string list
    attempt_number = db.Column(db.Integer, default=1)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)

class ProgressSnapshot(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    taken_at = db.Column(db.DateTime, default=datetime.utcnow)
    total_scenarios = db.Column(db.Integer)
    average_score = db.Column(db.Float)
    skill_breakdown = db.Column(db.Text)    # JSON map
    streak_days = db.Column(db.Integer)
    achievements = db.Column(db.Text)       # JSON list
    weaknesses = db.Column(db.Text)         # JSON list
```

---

## 8) LLM Integration (Ollama or other local endpoint)

**Service contract (pure Python, HTTP):**

* `generate_scenario(difficulty, category, focus) -> Scenario fields`
* `evaluate_email(scenario_text, email_body, weights) -> scores + feedback + suggestions`

**Prompt templates (unchanged content):**

**Scenario Prompt**

```
Generate a professional email scenario with:
- Character name & role
- Situation context
- Specific challenge/request
- Success criteria (list)
- Tone requirements
- Key information that must be included
Difficulty: {difficulty}
Category: {category}
Focus Area: {focus_area}
Output JSON with keys: character_name, character_role, scenario_text, success_criteria (list), tone.
```

**Evaluation Prompt**

```
Evaluate the email using this rubric (0–100 each):
1) Clarity 2) Conciseness 3) Tone 4) Grammar/Spelling 5) Completeness 6) Politeness
Scenario: {scenario_text}
Email: {email_body}
Return JSON:
{ "scores": { "clarity":..., ... }, "total":..., "feedback":"...", "suggestions":["...", ...] }
```

---

## 9) UI/UX (server pages)

**Dashboard (`/`)**

* Stats tiles (avg score, attempts, streak)
* Button: “Start New Scenario”
* Recent attempts table

**Scenario View (`/scenario/<id>`)**

* Avatar (static PNG) + character name/role
* Scenario text + success criteria bullets
* “Compose Response” button

**Compose (`/attempt/new`)**

* Subject (input), Body (textarea)
* Actions: Submit, Save Draft (optional), Clear

**Result (`/result/<attempt_id>`)**

* Big total score (e.g., 85/100)
* Table of six sub-scores
* Feedback paragraph + suggestions list
* Buttons: Try Again (prefill previous), Next Scenario, View History

**History (`/history`)**

* Filter by difficulty/category; table with score, date; link to result

**Analytics (`/analytics`)**

* Trend PNG (Matplotlib): average score over time
* Radar PNG (Matplotlib): average skill breakdown
* Category/difficulty bar PNG (Matplotlib)
  *(served as `<img src="/analytics/chart/<name>.png">`)*

---

## 10) Achievements & Adaptive Learning (simple server logic)

* **Achievements**: award on thresholds (e.g., 90+ in Tone 3 times). Store as strings.
* **Weakness detection**: rolling averages; lowest two skills become “focus” in `/settings`.
* **Adaptive**: next scenario seed uses `focus_area` = weakest skill.

---

## 11) Exports

* `/export/csv` → attempts with scenario_id, subject, total, 6 subscores, submitted_at
* `/export/json` (optional)

---

## 12) Performance Targets (local)

* Evaluation round-trip target: **< 3s** with cached model
* DB: SQLite, indexed on `submitted_at`, `scenario_id`
* Image handling: static avatars to avoid gen latency (keep SD optional)

---

## 13) Security & Ops

* CSRF via Flask-WTF; secrets in `config.py` env vars
* Validation for max email size
* Basic error pages (400/404/500)
* Logging to file (RotatingFileHandler)

---

## 14) Development Roadmap

**Phase 1 — MVP**

* Scenario generate → compose → evaluate → result
* SQLite models + migrations
* History list + CSV export

**Phase 2 — Quality**

* Analytics PNGs (Matplotlib)
* Achievements + streaks
* Weakness tracking + adaptive next scenario

**Phase 3 — Polish**

* Settings (weights/model names)
* Optional avatars (static/Pillow)
* JSON API endpoints for future expansion

---

## 15) Setup & Run

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

export FLASK_APP=run.py
export FLASK_ENV=development
# configure OLLAMA_BASE_URL or LLM endpoint in config.py / env

flask db init
flask db migrate -m "init"
flask db upgrade
flask run
```

`requirements.txt` (minimal)

```
Flask
Flask-SQLAlchemy
Flask-Migrate
Flask-WTF
Flask-Login
requests
matplotlib
Pillow
```

---

## 16) Success Metrics (tracked server-side)

* Engagement (sessions/attempts), score improvement, retry rate, errors/latency, user feedback notes.

---

### Notes on “pixel art”

To stay **Flask/Python-only**, ship a small set of pre-made pixel PNGs in `static/avatars/` and map them to roles (manager, client, professor…). If you want generation later, add a background job that writes a PNG to `character_image_path`, but keep MVP static.

This gives you a clean, demo-ready Flask app you can build fast for HackCMU while preserving your full game mechanics.
