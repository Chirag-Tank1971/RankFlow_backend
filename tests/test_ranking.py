from app.utils.ranking import (
    UserRankingMetrics,
    calculate_ranking_score,
    count_distinct_days,
    count_spam_clusters,
)


def test_higher_amount_yields_higher_score() -> None:
    low = UserRankingMetrics("u1", 100, 1, 1, 1, 0)
    high = UserRankingMetrics("u2", 1000, 1, 1, 1, 0)
    assert calculate_ranking_score(high) > calculate_ranking_score(low)


def test_spam_penalty_reduces_score() -> None:
    clean = UserRankingMetrics("u1", 500, 5, 3, 2, 0)
    spammy = UserRankingMetrics("u1", 500, 5, 3, 2, 2)
    assert calculate_ranking_score(clean) > calculate_ranking_score(spammy)


def test_distinct_days() -> None:
    from datetime import datetime, timezone

    timestamps = [
        datetime(2026, 6, 1, tzinfo=timezone.utc),
        datetime(2026, 6, 1, 12, tzinfo=timezone.utc),
        datetime(2026, 6, 2, tzinfo=timezone.utc),
    ]
    assert count_distinct_days(timestamps) == 2


def test_spam_cluster_detection() -> None:
    from datetime import datetime, timedelta, timezone

    base = datetime(2026, 6, 24, 12, 0, tzinfo=timezone.utc)
    timestamps = [base + timedelta(seconds=i * 10) for i in range(6)]
    assert count_spam_clusters(timestamps) == 1
