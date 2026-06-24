from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.ranking import DashboardStats, LeaderboardEntry, RankingEntry
from app.services.ranking_service import RankingService

router = APIRouter(tags=["ranking"])


@router.get("/ranking", response_model=list[RankingEntry])
def get_ranking(db: Session = Depends(get_db)) -> list[RankingEntry]:
    service = RankingService(db)
    return service.get_ranking()


@router.get("/leaderboard", response_model=list[LeaderboardEntry])
def get_leaderboard(db: Session = Depends(get_db)) -> list[LeaderboardEntry]:
    service = RankingService(db)
    return service.get_leaderboard()


@router.get("/dashboard", response_model=DashboardStats)
def get_dashboard(db: Session = Depends(get_db)) -> DashboardStats:
    service = RankingService(db)
    return service.get_dashboard_stats()
