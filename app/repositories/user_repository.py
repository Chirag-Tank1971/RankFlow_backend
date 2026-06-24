from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import User


class UserRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_user_id(self, user_id: str) -> User | None:
        stmt = select(User).where(User.user_id == user_id)
        return self.db.scalar(stmt)

    def get_or_create(self, user_id: str) -> User:
        user = self.get_by_user_id(user_id)
        if user:
            return user

        user = User(user_id=user_id)
        self.db.add(user)
        self.db.flush()
        return user

    def count_all(self) -> int:
        stmt = select(func.count()).select_from(User)
        return int(self.db.scalar(stmt) or 0)

    def get_all(self) -> list[User]:
        stmt = select(User).order_by(User.created_at.asc())
        return list(self.db.scalars(stmt).all())
