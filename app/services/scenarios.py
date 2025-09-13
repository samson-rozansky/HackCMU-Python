import json
from typing import Optional

from .. import db
from ..models import Scenario
from .llm import generate_scenario


def create_scenario(difficulty: str = "beginner", category: str = "academic", focus_area: str = "clarity") -> Scenario:
    data = generate_scenario(difficulty=difficulty, category=category, focus_area=focus_area)
    scenario = Scenario(
        character_name=data.get("character_name"),
        character_role=data.get("character_role"),
        character_image_path=None,
        scenario_text=data.get("scenario_text", ""),
        difficulty=difficulty,
        category=category,
        success_criteria=json.dumps(data.get("success_criteria", [])),
    )
    db.session.add(scenario)
    db.session.commit()
    return scenario


def get_scenario(scenario_id: int) -> Optional[Scenario]:
    return Scenario.query.get(scenario_id)
