import os

BASEDIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key")
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        "sqlite:///" + os.path.join(BASEDIR, "email_game.db"),
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # LLM settings
    OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
    LLM_MODEL_NAME = os.environ.get("LLM_MODEL_NAME", "llama3.1")
    OLLAMA_SMALL_MODEL = os.environ.get("OLLAMA_SMALL_MODEL", "llama3.2:3b")

    # Default rubric weights
    RUBRIC_WEIGHTS = {
        "clarity": 0.20,
        "conciseness": 0.15,
        "tone": 0.20,
        "grammar": 0.15,
        "completeness": 0.15,
        "politeness": 0.15,
    }
