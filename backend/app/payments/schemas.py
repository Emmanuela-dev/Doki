from decimal import Decimal
from typing import Any

from pydantic import BaseModel, Field, field_validator


class PaymentInitiation(BaseModel):
    transaction_id: str = Field(min_length=1, max_length=100)
    amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    phone_number: str = Field(min_length=9, max_length=15)
    description: str | None = Field(default=None, max_length=255)

    @field_validator("phone_number")
    @classmethod
    def normalize_phone_number(cls, value: str) -> str:
        digits = "".join(character for character in value if character.isdigit())
        if digits.startswith("0"):
            digits = "254" + digits[1:]
        elif digits.startswith("7") or digits.startswith("1"):
            digits = "254" + digits
        if not digits.startswith("254") or len(digits) != 12:
            raise ValueError("phone_number must be a valid Kenyan number")
        return digits


class PaymentInitiated(BaseModel):
    id: str
    status: str
    transaction_id: str
    amount: Decimal
    phone_number: str
    provider: str
    provider_reference: str | None = None
    provider_response: dict[str, Any] | None = None


class PaymentStatus(BaseModel):
    id: str
    transaction_id: str
    status: str
    amount: Decimal
    phone_number: str
    provider: str
    provider_reference: str | None = None
    callback: dict[str, Any] | None = None