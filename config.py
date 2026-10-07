

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "campus-canteen-super-secret-key-2024")

    # Database configuration (PostgreSQL default, with DATABASE_URL override support)
    db_uri = os.getenv("DATABASE_URL")
    if not db_uri:
        db_user = os.getenv("DB_USER", "chandani")
        db_pass = os.getenv("DB_PASSWORD", "")
        db_host = os.getenv("DB_HOST", "localhost")
        db_port = os.getenv("DB_PORT", "5432")
        db_name = os.getenv("DB_NAME", "canteen_management")
        db_uri = f"postgresql+psycopg://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"

    SQLALCHEMY_DATABASE_URI = db_uri
    SQLALCHEMY_TRACK_MODIFICATIONS = False    
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
    } if not db_uri.startswith("sqlite") else {}

    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "static", "images", "uploads")
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5MB
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp", "svg"}

    # Delivery Settings
    DEFAULT_DELIVERY_CHARGE = float(os.getenv("DEFAULT_DELIVERY_CHARGE", "50"))
    FREE_DELIVERY_THRESHOLD = float(os.getenv("FREE_DELIVERY_THRESHOLD", "500"))

    # eSewa ePay v2 Configuration (Sandbox by default)
    ESEWA_ENV = os.getenv("ESEWA_ENV", "sandbox")  # "sandbox" or "production"
    ESEWA_PRODUCT_CODE = os.getenv("ESEWA_PRODUCT_CODE", "EPAYTEST")
    ESEWA_SECRET_KEY = os.getenv("ESEWA_SECRET_KEY", "8gBm/:&EnhH.1/q")
    ESEWA_PAYMENT_URL = os.getenv(
        "ESEWA_PAYMENT_URL",
        "https://rc-epay.esewa.com.np/api/epay/main/v2/form"
        if os.getenv("ESEWA_ENV", "sandbox") == "sandbox"
        else "https://epay.esewa.com.np/api/epay/main/v2/form",
    )
    ESEWA_STATUS_URL = os.getenv(
        "ESEWA_STATUS_URL",
        "https://rc-epay.esewa.com.np/api/epay/transaction/status"
        if os.getenv("ESEWA_ENV", "sandbox") == "sandbox"
        else "https://epay.esewa.com.np/api/epay/transaction/status",
    )

