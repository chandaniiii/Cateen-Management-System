

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "campus-canteen-super-secret-key-2024")

    # PostgreSQL database configuration
    db_user = os.getenv("DB_USER", "chandani")
    db_pass = os.getenv("DB_PASSWORD", "")
    db_host = os.getenv("DB_HOST", "localhost")
    db_port = os.getenv("DB_PORT", "5432")
    db_name = os.getenv("DB_NAME", "canteen_management")

    SQLALCHEMY_DATABASE_URI = (
        f"postgresql+psycopg://"
        f"{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False    
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
    }
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "static", "images", "uploads")
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5MB
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp", "svg"}
