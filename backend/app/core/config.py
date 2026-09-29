import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


load_dotenv(Path(__file__).resolve().parents[2] / ".env")


@dataclass(frozen=True)
class Settings:
    kopokopo_client_id: str = os.getenv("KOPOKOPO_CLIENT_ID", "")
    kopokopo_client_secret: str = os.getenv("KOPOKOPO_CLIENT_SECRET", "")
    kopokopo_base_url: str = os.getenv("KOPOKOPO_BASE_URL", "https://api.kopokopo.com")
    payment_callback_url: str = os.getenv("PAYMENT_CALLBACK_URL", "")
    kopokopo_api_version: str = os.getenv("KOPOKOPO_API_VERSION", "v2")
    kopokopo_webhook_secret: str = os.getenv("KOPOKOPO_WEBHOOK_SECRET", "")


settings = Settings()