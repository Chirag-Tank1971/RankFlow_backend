from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class UserListItem(BaseModel):
    model_config = ConfigDict(populate_by_name=True, ser_json_by_alias=True)

    user_id: str = Field(..., alias="userId")
    total_transactions: int = Field(..., alias="totalTransactions")
    total_amount: float = Field(..., alias="totalAmount")
    ranking_score: float = Field(..., alias="rankingScore")


class UserSummaryResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True, ser_json_by_alias=True)

    user_id: str = Field(..., alias="userId")
    total_transactions: int = Field(..., alias="totalTransactions")
    total_amount: float = Field(..., alias="totalAmount")
    average_amount: float = Field(..., alias="averageAmount")
    ranking_score: float = Field(..., alias="rankingScore")
    last_transaction: datetime | None = Field(..., alias="lastTransaction")
