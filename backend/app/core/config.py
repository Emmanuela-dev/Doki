from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://postgres:password@localhost:5432/doki_db"

    SECRET_KEY: str = "changeme-use-a-real-secret-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 43200

    GOOGLE_MAPS_API_KEY: str = ""

    STORAGE_BACKEND: str = "local"
    LOCAL_UPLOAD_DIR: str = "uploads"
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    AWS_S3_BUCKET: str = "doki-uploads"
    AWS_REGION: str = "eu-west-1"

    APP_ENV: str = "development"
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost:3001"

    kopokopo_client_id: str = Field(default="", validation_alias="KOPOKOPO_CLIENT_ID")
    kopokopo_client_secret: str = Field(default="", validation_alias="KOPOKOPO_CLIENT_SECRET")
    kopokopo_base_url: str = Field(default="https://api.kopokopo.com", validation_alias="KOPOKOPO_BASE_URL")
    payment_callback_url: str = Field(default="", validation_alias="PAYMENT_CALLBACK_URL")
    kopokopo_api_version: str = Field(default="v2", validation_alias="KOPOKOPO_API_VERSION")
    kopokopo_webhook_secret: str = Field(default="", validation_alias="KOPOKOPO_WEBHOOK_SECRET")

    @property
    def origins(self) -> list[str]:
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]

    model_config = {
        "env_file": Path(__file__).resolve().parents[2] / ".env",
        "extra": "ignore",
    }


settings = Settings()

SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES
