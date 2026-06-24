from dataclasses import dataclass
from datetime import datetime, timedelta, timezone


@dataclass
class UserRankingMetrics:
    user_id: str
    total_amount: float
    total_transactions: int
    distinct_days: int
    recent_transaction_count: int
    spam_cluster_count: int


def _ensure_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def calculate_consistency_bonus(distinct_days: int, total_transactions: int) -> float:
    if total_transactions == 0:
        return 0.0
    ratio = distinct_days / total_transactions
    return min(1.0, ratio * 2.0)


def calculate_activity_bonus(recent_count: int, total_transactions: int) -> float:
    if total_transactions == 0:
        return 0.0
    ratio = recent_count / total_transactions
    return min(1.0, ratio * 1.5)


def calculate_spam_penalty(spam_cluster_count: int) -> float:
    return float(spam_cluster_count * 75)


def calculate_ranking_score(metrics: UserRankingMetrics) -> float:
    consistency = calculate_consistency_bonus(
        metrics.distinct_days, metrics.total_transactions
    )
    activity = calculate_activity_bonus(
        metrics.recent_transaction_count, metrics.total_transactions
    )
    spam = calculate_spam_penalty(metrics.spam_cluster_count)

    score = (
        (metrics.total_amount * 0.50)
        + (metrics.total_transactions * 25)
        + (consistency * 100)
        + (activity * 50)
        - spam
    )
    return round(max(0.0, score), 2)


def count_spam_clusters(timestamps: list[datetime], window_seconds: int = 60, threshold: int = 5) -> int:
    if len(timestamps) < threshold:
        return 0

    sorted_ts = sorted(_ensure_utc(ts) for ts in timestamps)
    clusters = 0
    start = 0

    for end in range(len(sorted_ts)):
        while sorted_ts[end] - sorted_ts[start] > timedelta(seconds=window_seconds):
            start += 1
        if end - start + 1 >= threshold:
            clusters += 1
            start = end + 1

    return clusters


def count_recent_transactions(timestamps: list[datetime], days: int = 7) -> int:
    if not timestamps:
        return 0
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    return sum(1 for ts in timestamps if _ensure_utc(ts) >= cutoff)


def count_distinct_days(timestamps: list[datetime]) -> int:
    if not timestamps:
        return 0
    return len({_ensure_utc(ts).date() for ts in timestamps})
