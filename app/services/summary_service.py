from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.repositories.transaction_repository import TransactionRepository
from app.repositories.user_repository import UserRepository
from app.schemas.summary import UserListItem, UserSummaryResponse
from app.utils.ranking import (
    UserRankingMetrics,
    calculate_ranking_score,
    count_distinct_days,
    count_recent_transactions,
    count_spam_clusters,
)


class SummaryService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.user_repo = UserRepository(db)
        self.transaction_repo = TransactionRepository(db)

    def get_user_summary(self, user_id: str) -> UserSummaryResponse:
        user = self.user_repo.get_by_user_id(user_id)
        if not user:
            raise NotFoundError("User not found")

        count, total, average, last_at = self.transaction_repo.get_user_summary(user)
        timestamps = self.transaction_repo.get_user_timestamps(user)

        metrics = UserRankingMetrics(
            user_id=user.user_id,
            total_amount=total,
            total_transactions=count,
            distinct_days=count_distinct_days(timestamps),
            recent_transaction_count=count_recent_transactions(timestamps),
            spam_cluster_count=count_spam_clusters(timestamps),
        )
        score = calculate_ranking_score(metrics)

        return UserSummaryResponse(
            userId=user.user_id,
            totalTransactions=count,
            totalAmount=round(total, 2),
            averageAmount=round(average, 2),
            rankingScore=score,
            lastTransaction=last_at,
        )

    def list_users(self) -> list[UserListItem]:
        users = self.user_repo.get_all()
        items: list[UserListItem] = []

        for user in users:
            count, total, _, _ = self.transaction_repo.get_user_summary(user)
            timestamps = self.transaction_repo.get_user_timestamps(user)

            metrics = UserRankingMetrics(
                user_id=user.user_id,
                total_amount=total,
                total_transactions=count,
                distinct_days=count_distinct_days(timestamps),
                recent_transaction_count=count_recent_transactions(timestamps),
                spam_cluster_count=count_spam_clusters(timestamps),
            )
            score = calculate_ranking_score(metrics)

            items.append(
                UserListItem(
                    userId=user.user_id,
                    totalTransactions=count,
                    totalAmount=round(total, 2),
                    rankingScore=score,
                )
            )

        return items
