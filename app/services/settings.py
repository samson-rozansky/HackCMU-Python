import json
from typing import Any, Dict, Optional

from flask import current_app

from .. import db
from ..models import AppSetting


def load_settings_into_config() -> None:
    # Load persisted settings from DB into current_app.config
    for row in AppSetting.query.all():
        if row.key == 'RUBRIC_WEIGHTS':
            try:
                current_app.config['RUBRIC_WEIGHTS'] = json.loads(row.value)
            except Exception:
                pass
        elif row.key == 'LLM_MODEL_NAME':
            current_app.config['LLM_MODEL_NAME'] = row.value
        elif row.key == 'OLLAMA_BASE_URL':
            current_app.config['OLLAMA_BASE_URL'] = row.value


def get_setting(key: str, default: Optional[Any] = None) -> Any:
    rec = AppSetting.query.filter_by(key=key).first()
    if not rec:
        return default
    if key == 'RUBRIC_WEIGHTS':
        try:
            return json.loads(rec.value)
        except Exception:
            return default
    return rec.value


def set_setting(key: str, value: Any) -> None:
    if key == 'RUBRIC_WEIGHTS':
        stored = json.dumps(value)
    else:
        stored = str(value)
    rec = AppSetting.query.filter_by(key=key).first()
    if rec:
        rec.value = stored
    else:
        rec = AppSetting(key=key, value=stored)
        db.session.add(rec)
    db.session.commit()

    # Update in-memory config too
    if key == 'RUBRIC_WEIGHTS':
        current_app.config['RUBRIC_WEIGHTS'] = value
    elif key == 'LLM_MODEL_NAME':
        current_app.config['LLM_MODEL_NAME'] = value
    elif key == 'OLLAMA_BASE_URL':
        current_app.config['OLLAMA_BASE_URL'] = value
