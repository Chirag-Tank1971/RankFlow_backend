import os
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import settings
from app.database.base import Base
from app.database.session import get_db
from app.main import app

TEST_DATABASE_URL = "sqlite:///./test_app.db"


@pytest.fixture(scope="session", autouse=True)
def setup_test_database() -> Generator[None, None, None]:
    settings.database_url = TEST_DATABASE_URL
    settings.app_env = "test"

    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
    )
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    testing_session_local = sessionmaker(bind=engine, autocommit=False, autoflush=False)

    def override_get_db() -> Generator[Session, None, None]:
        db = testing_session_local()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    yield

    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)
    engine.dispose()
    if os.path.exists("test_app.db"):
        try:
            os.remove("test_app.db")
        except PermissionError:
            pass


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_create_transaction_success(client: TestClient) -> None:
    payload = {
        "transactionId": "txn_1001",
        "userId": "user_1",
        "amount": 500,
        "type": "purchase",
    }
    response = client.post("/transaction", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    assert data["message"] == "Transaction processed successfully"


def test_duplicate_transaction_returns_409(client: TestClient) -> None:
    payload = {
        "transactionId": "txn_dup",
        "userId": "user_dup",
        "amount": 100,
        "type": "purchase",
    }
    first = client.post("/transaction", json=payload)
    second = client.post("/transaction", json=payload)

    assert first.status_code == 201
    assert second.status_code == 409
    assert second.json()["success"] is False
    assert second.json()["message"] == "Duplicate transaction"


def test_validation_rejects_zero_amount(client: TestClient) -> None:
    payload = {
        "transactionId": "txn_zero",
        "userId": "user_1",
        "amount": 0,
        "type": "purchase",
    }
    response = client.post("/transaction", json=payload)
    assert response.status_code == 422
    assert response.json()["success"] is False


def test_validation_rejects_negative_amount(client: TestClient) -> None:
    payload = {
        "transactionId": "txn_neg",
        "userId": "user_1",
        "amount": -50,
        "type": "purchase",
    }
    response = client.post("/transaction", json=payload)
    assert response.status_code == 422


def test_validation_rejects_missing_fields(client: TestClient) -> None:
    response = client.post("/transaction", json={"amount": 100})
    assert response.status_code == 422


def test_summary_not_found(client: TestClient) -> None:
    response = client.get("/summary/unknown_user")
    assert response.status_code == 404
    assert response.json()["message"] == "User not found"


def test_summary_returns_aggregates(client: TestClient) -> None:
    client.post(
        "/transaction",
        json={
            "transactionId": "txn_s1",
            "userId": "user_summary",
            "amount": 200,
            "type": "purchase",
        },
    )
    client.post(
        "/transaction",
        json={
            "transactionId": "txn_s2",
            "userId": "user_summary",
            "amount": 400,
            "type": "purchase",
        },
    )

    response = client.get("/summary/user_summary")
    assert response.status_code == 200
    data = response.json()
    assert data["userId"] == "user_summary"
    assert data["totalTransactions"] == 2
    assert data["totalAmount"] == 600
    assert data["averageAmount"] == 300
    assert "rankingScore" in data
    assert data["lastTransaction"] is not None


def test_list_users(client: TestClient) -> None:
    client.post(
        "/transaction",
        json={
            "transactionId": "txn_u1",
            "userId": "user_list_a",
            "amount": 100,
            "type": "purchase",
        },
    )
    client.post(
        "/transaction",
        json={
            "transactionId": "txn_u2",
            "userId": "user_list_b",
            "amount": 300,
            "type": "purchase",
        },
    )

    response = client.get("/users")
    assert response.status_code == 200
    data = response.json()
    user_ids = {item["userId"] for item in data}
    assert "user_list_a" in user_ids
    assert "user_list_b" in user_ids


def test_ranking_sorted_descending(client: TestClient) -> None:
    client.post(
        "/transaction",
        json={
            "transactionId": "txn_r1",
            "userId": "user_low",
            "amount": 100,
            "type": "purchase",
        },
    )
    client.post(
        "/transaction",
        json={
            "transactionId": "txn_r2",
            "userId": "user_high",
            "amount": 5000,
            "type": "purchase",
        },
    )

    response = client.get("/ranking")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2
    assert data[0]["rank"] == 1
    assert data[0]["score"] >= data[1]["score"]


def test_dashboard_stats(client: TestClient) -> None:
    response = client.get("/dashboard")
    assert response.status_code == 200
    data = response.json()
    assert "totalUsers" in data
    assert "totalTransactions" in data
    assert "totalVolume" in data
