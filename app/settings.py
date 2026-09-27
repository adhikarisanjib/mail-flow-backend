import os


class Settings:
    # Database
    DATABASE_URL: str = os.environ.get("DATABASE_URL", "")

    # SMTP Configuration
    SMTP_HOST: str = os.environ.get("SMTP_HOST", "smtp.example.com")
    SMTP_PORT: int = int(os.environ.get("SMTP_PORT", "587"))
    SMTP_USERNAME: str = os.environ.get("SMTP_USERNAME", "")
    SMTP_PASSWORD: str = os.environ.get("SMTP_PASSWORD", "")
    SMTP_FROM_EMAIL: str = os.environ.get("SMTP_FROM_EMAIL", "")
    SMTP_FROM_NAME: str = os.environ.get("SMTP_FROM_NAME", "Email Service")
    SMTP_TIMEOUT: int = int(os.environ.get("SMTP_TIMEOUT", "10"))
    SMTP_USE_TLS: bool = os.environ.get("SMTP_USE_TLS", "True") == "True"

    # Redis Configuration
    REDIS_URL: str = os.environ.get("REDIS_URL", "redis://localhost:6379/0")

    # Celery Configuration
    CELERY_BROKER_URL: str = os.environ.get(
        "CELERY_BROKER_URL", "redis://localhost:6379/0"
    )
    CELERY_RESULT_BACKEND: str = os.environ.get(
        "CELERY_RESULT_BACKEND", "redis://localhost:6379/0"
    )

    # Email Configuration
    MAX_RETRIES: int = int(os.environ.get("MAX_RETRIES", "3"))
    BATCH_SIZE: int = int(os.environ.get("BATCH_SIZE", "100"))

    # Application
    APP_NAME: str = os.environ.get("APP_NAME", "Email Service")
    DEBUG: bool = os.environ.get("DEBUG", "True") == "True"
    SECERET_KEY: str = os.environ.get("SECRET_KEY", "supersecretkey")
    ALLOWED_HOSTS: list = os.environ.get("ALLOWED_HOSTS", "*").split(",")


settings = Settings()
