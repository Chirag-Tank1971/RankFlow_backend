from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.config import settings


class TransactionCreate(BaseModel):
    model_config = ConfigDict(populate_by_name=True, str_strip_whitespace=True)

    transaction_id: str = Field(..., alias="transactionId", min_length=1, max_length=255)
    user_id: str = Field(..., alias="userId", min_length=1, max_length=255)
    amount: float = Field(..., gt=0)
    type: str = Field(..., min_length=1, max_length=100)

    @field_validator("transaction_id", "user_id", "type", mode="before")
    @classmethod
    def strip_strings(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip()
        return value

    @field_validator("amount")
    @classmethod
    def validate_max_amount(cls, value: float) -> float:
        if value > settings.max_transaction_amount:
            raise ValueError(
                f"Amount cannot exceed maximum of {settings.max_transaction_amount}"
            )
        return value


class TransactionResponse(BaseModel):
    success: bool = True
    message: str = "Transaction processed successfully"
