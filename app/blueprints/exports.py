import csv
from io import StringIO
from flask import Blueprint, make_response

from ..models import Attempt

exports_bp = Blueprint("exports", __name__)


@exports_bp.route("/export/csv")
def export_csv():
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "attempt_id",
        "scenario_id",
        "subject",
        "total",
        "clarity",
        "conciseness",
        "tone",
        "grammar",
        "completeness",
        "politeness",
        "submitted_at",
    ])

    for a in Attempt.query.order_by(Attempt.submitted_at.asc()).all():
        writer.writerow([
            a.id,
            a.scenario_id,
            a.email_subject or "",
            a.score_total or 0,
            a.score_clarity or 0,
            a.score_conciseness or 0,
            a.score_tone or 0,
            a.score_grammar or 0,
            a.score_completeness or 0,
            a.score_politeness or 0,
            a.submitted_at.isoformat() if a.submitted_at else "",
        ])

    response = make_response(output.getvalue())
    response.headers["Content-Disposition"] = "attachment; filename=attempts.csv"
    response.headers["Content-Type"] = "text/csv"
    return response
