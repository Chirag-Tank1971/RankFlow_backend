from pydantic import BaseModel, ConfigDict, Field


class RankingEntry(BaseModel):
    model_config = ConfigDict(populate_by_name=True, ser_json_by_alias=True)

    rank: int
    user_id: str = Field(..., alias="userId")
    score: float


class LeaderboardEntry(RankingEntry):
    model_config = ConfigDict(populate_by_name=True, ser_json_by_alias=True)
    total_transactions: int = Field(..., alias="totalTransactions")
    total_amount: float = Field(..., alias="totalAmount")


class DashboardStats(BaseModel):
    model_config = ConfigDict(populate_by_name=True, ser_json_by_alias=True)

    total_users: int = Field(..., alias="totalUsers")
    total_transactions: int = Field(..., alias="totalTransactions")
    total_volume: float = Field(..., alias="totalVolume")
    top_ranked_user: str | None = Field(..., alias="topRankedUser")
    top_ranked_score: float | None = Field(..., alias="topRankedScore")
