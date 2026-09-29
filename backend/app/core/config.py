import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    kopokopo_client_id: str = os.getenv("KOPOKOPO_CLIENT_ID", "")
    kopokopo_client_secret: str = os.getenv("KOPOKOPO_CLIENT_SECRET", "")
    kopokopo_base_url: str = os.getenv("KOPOKOPO_BASE_URL", "https://api.kopokopo.com")
    kopokopo_till_number: str = os.getenv("KOPOKOPO_TILL_NUMBER", "")
    payment_callback_url: str = os.getenv("PAYMENT_CALLBACK_URL", "")
    kopokopo_api_version: str = os.getenv("KOPOKOPO_API_VERSION", "v4")


settings = Settings()