from __future__ import annotations

from typing import List

import requests
from flask import current_app

from .settings import set_setting


def list_installed_models() -> List[str]:
    base_url = current_app.config.get("OLLAMA_BASE_URL")
    try:
        resp = requests.get(f"{base_url}/api/tags", timeout=3)
        resp.raise_for_status()
        data = resp.json()
        models = data.get("models") or data.get("data") or []
        names: List[str] = []
        for m in models:
            name = m.get("name") or m.get("model") or m.get("tag")
            if name:
                names.append(name)
        return names
    except Exception:
        return []


def autodetect_and_apply_model_preference() -> None:
    names = list_installed_models()
    if not names:
        return

    preferred = None
    # Prefer exact gemma3:1b if available
    if any(n == "gemma3:1b" for n in names):
        preferred = "gemma3:1b"
    # Otherwise prefer a known small llama if available
    elif any(n == "llama3.2:3b" for n in names):
        preferred = "llama3.2:3b"
    # Otherwise try any :1b or :3b tag
    else:
        for tag in (":1b", ":3b"):
            match = next((n for n in names if n.endswith(tag)), None)
            if match:
                preferred = match
                break

    if preferred:
        set_setting("LLM_MODEL_NAME", preferred)
        set_setting("OLLAMA_SMALL_MODEL", preferred)
