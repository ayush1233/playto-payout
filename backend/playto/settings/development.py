import os

os.environ.setdefault("SECRET_KEY", "dev-secret-key-only-for-local-use")
os.environ.setdefault("DEBUG", "True")
os.environ.setdefault("POSTGRES_DB", "playto")
os.environ.setdefault("POSTGRES_USER", "playto")
os.environ.setdefault("POSTGRES_PASSWORD", "playto")
os.environ.setdefault("POSTGRES_HOST", "localhost")
os.environ.setdefault("POSTGRES_PORT", "5432")

from .base import *  # noqa: E402,F401,F403
