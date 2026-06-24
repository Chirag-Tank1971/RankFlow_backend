from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.transaction import TransactionCreate, TransactionResponse
from app.services.transaction_service import TransactionService

router = APIRouter(tags=["transactions"])


@router.post(
    "/transaction",
    response_model=TransactionResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_transaction(
    payload: TransactionCreate,
    db: Session = Depends(get_db),
) -> TransactionResponse:
    service = TransactionService(db)
    service.create_transaction(payload)
    return TransactionResponse()
