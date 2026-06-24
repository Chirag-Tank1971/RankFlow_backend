from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import DuplicateTransactionError
from app.core.logging import get_logger
from app.repositories.transaction_repository import TransactionRepository
from app.repositories.user_repository import UserRepository
from app.schemas.transaction import TransactionCreate

logger = get_logger(__name__)


class TransactionService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.user_repo = UserRepository(db)
        self.transaction_repo = TransactionRepository(db)

    def create_transaction(self, payload: TransactionCreate) -> None:
        try:
            with self.db.begin():
                user = self.user_repo.get_or_create(payload.user_id)
                self.transaction_repo.create(
                    transaction_id=payload.transaction_id,
                    user=user,
                    amount=payload.amount,
                    transaction_type=payload.type,
                )
            logger.info(
                "Transaction processed: txn=%s user=%s amount=%s",
                payload.transaction_id,
                payload.user_id,
                payload.amount,
            )
        except IntegrityError as exc:
            self.db.rollback()
            logger.warning(
                "Duplicate transaction rejected: txn=%s user=%s",
                payload.transaction_id,
                payload.user_id,
            )
            raise DuplicateTransactionError() from exc
        except DuplicateTransactionError:
            raise
        except Exception:
            self.db.rollback()
            logger.exception(
                "Database error while creating transaction: txn=%s",
                payload.transaction_id,
            )
            raise
