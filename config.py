import os
from pathlib import Path


class Config:
    BASE_DIR = Path(__file__).resolve().parent
    SECRET_KEY = os.environ.get("SECRET_KEY", "change-me-super-secret")
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        f"sqlite:///{(BASE_DIR / 'instance' / 'events.db').resolve()}",
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
