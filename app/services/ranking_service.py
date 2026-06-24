from sqlalchemy.orm import Session

from app.repositories.transaction_repository import TransactionRepository
from app.repositories.user_repository import UserRepository
from app.schemas.ranking import DashboardStats, LeaderboardEntry, RankingEntry
from app.utils.ranking import (
    UserRankingMetrics,
    calculate_ranking_score,
    count_distinct_days,
    count_recent_transactions,
    count_spam_clusters,
)


class RankingService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.user_repo = UserRepository(db)
        self.transaction_repo = TransactionRepository(db)

    def _build_metrics(
        self, user_id: str, total: float, count: int, timestamps: list
    ) -> UserRankingMetrics:
        return UserRankingMetrics(
            user_id=user_id,
            total_amount=total,
            total_transactions=count,
            distinct_days=count_distinct_days(timestamps),
            recent_transaction_count=count_recent_transactions(timestamps),
            spam_cluster_count=count_spam_clusters(timestamps),
        )

    def get_ranking(self) -> list[RankingEntry]:
        aggregates = self.transaction_repo.get_all_user_aggregates()
        scored: list[tuple[str, float]] = []

        for user, timestamps, total, count in aggregates:
            if count == 0:
                continue
            metrics = self._build_metrics(user.user_id, total, count, timestamps)
            scored.append((user.user_id, calculate_ranking_score(metrics)))

        scored.sort(key=lambda item: item[1], reverse=True)

        return [
            RankingEntry(rank=index, userId=user_id, score=score)
            for index, (user_id, score) in enumerate(scored, start=1)
        ]

    def get_leaderboard(self) -> list[LeaderboardEntry]:
        aggregates = self.transaction_repo.get_all_user_aggregates()
        scored: list[tuple[str, float, int, float]] = []

        for user, timestamps, total, count in aggregates:
            if count == 0:
                continue
            metrics = self._build_metrics(user.user_id, total, count, timestamps)
            scored.append(
                (user.user_id, calculate_ranking_score(metrics), count, total)
            )

        scored.sort(key=lambda item: item[1], reverse=True)

        return [
            LeaderboardEntry(
                rank=index,
                userId=user_id,
                score=score,
                totalTransactions=count,
                totalAmount=round(total, 2),
            )
            for index, (user_id, score, count, total) in enumerate(scored, start=1)
        ]

    def get_dashboard_stats(self) -> DashboardStats:
        ranking = self.get_ranking()
        top_user = ranking[0].user_id if ranking else None
        top_score = ranking[0].score if ranking else None

        return DashboardStats(
            totalUsers=self.user_repo.count_all(),
            totalTransactions=self.transaction_repo.count_all(),
            totalVolume=round(self.transaction_repo.total_volume(), 2),
            topRankedUser=top_user,
            topRankedScore=top_score,
        )
