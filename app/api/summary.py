from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.summary import UserListItem, UserSummaryResponse
from app.services.summary_service import SummaryService

router = APIRouter(tags=["summary"])


@router.get("/users", response_model=list[UserListItem])
def list_users(db: Session = Depends(get_db)) -> list[UserListItem]:
    service = SummaryService(db)
    return service.list_users()


@router.get("/summary/{user_id}", response_model=UserSummaryResponse)
def get_user_summary(
    user_id: str,
    db: Session = Depends(get_db),
) -> UserSummaryResponse:
    service = SummaryService(db)
    return service.get_user_summary(user_id.strip())
