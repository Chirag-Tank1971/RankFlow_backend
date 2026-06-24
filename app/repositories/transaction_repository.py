from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Transaction, User


class TransactionRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(
        self,
        *,
        transaction_id: str,
        user: User,
        amount: float,
        transaction_type: str,
    ) -> Transaction:
        transaction = Transaction(
            transaction_id=transaction_id,
            user_id=user.id,
            amount=amount,
            type=transaction_type,
        )
        self.db.add(transaction)
        self.db.flush()
        return transaction

    def get_user_summary(self, user: User) -> tuple[int, float, float, datetime | None]:
        stmt = select(
            func.count(Transaction.id),
            func.coalesce(func.sum(Transaction.amount), 0),
            func.max(Transaction.created_at),
        ).where(Transaction.user_id == user.id)

        count, total, last_at = self.db.execute(stmt).one()
        count = int(count or 0)
        total = float(total or 0)
        average = total / count if count else 0.0
        return count, total, average, last_at

    def get_user_timestamps(self, user: User) -> list[datetime]:
        stmt = (
            select(Transaction.created_at)
            .where(Transaction.user_id == user.id)
            .order_by(Transaction.created_at.asc())
        )
        return list(self.db.scalars(stmt).all())

    def count_all(self) -> int:
        stmt = select(func.count()).select_from(Transaction)
        return int(self.db.scalar(stmt) or 0)

    def total_volume(self) -> float:
        stmt = select(func.coalesce(func.sum(Transaction.amount), 0))
        return float(self.db.scalar(stmt) or 0)

    def get_all_user_aggregates(self) -> list[tuple[User, list[datetime], float, int]]:
        users = self.db.scalars(select(User)).all()
        results: list[tuple[User, list[datetime], float, int]] = []

        for user in users:
            agg_stmt = select(
                func.coalesce(func.sum(Transaction.amount), 0),
                func.count(Transaction.id),
            ).where(Transaction.user_id == user.id)
            total, count = self.db.execute(agg_stmt).one()
            timestamps = self.get_user_timestamps(user)
            results.append((user, timestamps, float(total or 0), int(count or 0)))

        return results
