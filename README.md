# RankFlow — Backend

Production-ready REST API for RankFlow: processing financial transactions, preventing duplicate requests, computing fair user rankings, and exposing analytics endpoints. Built with FastAPI, SQLAlchemy 2.0, and Supabase PostgreSQL.

---

## Table of Contents

- [Project Overview](#project-overview)
- [Tech Stack](#tech-stack)
- [Architecture](#architecture)
- [Folder Structure](#folder-structure)
- [Prerequisites](#prerequisites)
- [Installation & Setup](#installation--setup)
- [Environment Variables](#environment-variables)
- [Supabase Database Setup](#supabase-database-setup)
- [Running the Server](#running-the-server)
- [Database Migrations](#database-migrations)
- [API Documentation](#api-documentation)
- [Database Schema](#database-schema)
- [Ranking Algorithm](#ranking-algorithm)
- [Duplicate Prevention](#duplicate-prevention)
- [Concurrency & Data Consistency](#concurrency--data-consistency)
- [Error Handling & Logging](#error-handling--logging)
- [Testing](#testing)
- [Deployment](#deployment)
- [Troubleshooting](#troubleshooting)
- [Future Improvements](#future-improvements)

---

## Project Overview

This backend is the core of RankFlow. It:

- Accepts transaction submissions via REST API with strict validation
- Stores data in PostgreSQL (Supabase) using SQLAlchemy ORM
- Prevents duplicate transaction processing using database-level uniqueness
- Computes weighted ranking scores that reward volume, consistency, and activity
- Penalizes spam-like transaction bursts
- Handles concurrent requests safely with explicit SQLAlchemy transactions
- Returns consistent JSON error responses across all endpoints

The API is consumed by the React frontend and can also be used directly via Swagger UI or any HTTP client.

---

## Tech Stack

| Technology | Purpose |
|------------|---------|
| Python 3.12+ | Runtime (3.14 supported for local dev) |
| FastAPI | Web framework and OpenAPI docs |
| SQLAlchemy 2.0 | ORM and database access |
| Pydantic v2 | Request/response validation |
| Alembic | Database migrations |
| Uvicorn | ASGI server |
| psycopg 3 | PostgreSQL driver |
| Supabase PostgreSQL | Hosted database |
| pytest | Test suite |
| Python logging | Structured request and error logs |

**Not used:** Docker, Redis, Supabase JS client (connection is via raw PostgreSQL URL only).

---

## Architecture

The backend follows **Repository + Service** pattern with thin route handlers:

```
HTTP Request
    ↓
API Routes (app/api/)          ← validation, status codes, dependency injection
    ↓
Services (app/services/)       ← business logic, orchestration, ranking
    ↓
Repositories (app/repositories/) ← database queries
    ↓
Models (app/models/)           ← SQLAlchemy ORM entities
    ↓
PostgreSQL (Supabase)
```

**Design principles:**

- Routes do not contain business logic
- Services do not know about HTTP
- Repositories handle only data access
- Ranking math lives in `app/utils/ranking.py`
- Configuration is centralized in `app/config.py`

---

## Folder Structure

```
backend/
├── app/
│   ├── api/
│   │   ├── transaction.py    # POST /transaction
│   │   ├── summary.py        # GET /users, GET /summary/{userId}
│   │   └── ranking.py        # GET /ranking, /leaderboard, /dashboard
│   ├── core/
│   │   ├── exceptions.py     # AppException, NotFoundError, DuplicateTransactionError
│   │   └── logging.py        # Logger setup
│   ├── database/
│   │   ├── base.py           # SQLAlchemy DeclarativeBase
│   │   └── session.py        # Engine, SessionLocal, get_db()
│   ├── middleware/
│   │   └── logging_middleware.py  # Request/response logging
│   ├── models/
│   │   └── __init__.py       # User, Transaction ORM models
│   ├── repositories/
│   │   ├── user_repository.py
│   │   └── transaction_repository.py
│   ├── schemas/
│   │   ├── common.py         # ErrorResponse, SuccessResponse
│   │   ├── transaction.py    # TransactionCreate, TransactionResponse
│   │   ├── summary.py        # UserSummaryResponse, UserListItem
│   │   └── ranking.py        # RankingEntry, LeaderboardEntry, DashboardStats
│   ├── services/
│   │   ├── transaction_service.py
│   │   ├── summary_service.py
│   │   └── ranking_service.py
│   ├── utils/
│   │   └── ranking.py        # Score calculation utilities
│   ├── config.py             # Pydantic Settings (.env loading)
│   └── main.py               # FastAPI app, CORS, exception handlers
├── alembic/
│   ├── env.py
│   └── versions/
│       └── 001_initial_schema.py
├── tests/
│   ├── test_api.py           # Integration tests for all endpoints
│   └── test_ranking.py       # Unit tests for ranking algorithm
├── alembic.ini
├── pytest.ini
├── requirements.txt
├── .env.example
└── README.md
```

---

## Prerequisites

- Python 3.12 or newer
- pip and venv
- A Supabase account (free tier works)
- Git (optional)

---

## Installation & Setup

### 1. Clone and enter the backend directory

```bash
cd backend
```

### 2. Create and activate virtual environment

**Windows (PowerShell):**

```powershell
python -m venv venv
venv\Scripts\activate
```

**macOS / Linux:**

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment

```bash
# Windows
copy .env.example .env

# macOS / Linux
cp .env.example .env
```

Edit `.env` with your real Supabase connection string (see [Supabase Database Setup](#supabase-database-setup)).

### 5. Run migrations

```bash
alembic upgrade head
```

### 6. Start the server

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**Interactive API docs:** http://localhost:8000/docs  
**OpenAPI JSON:** http://localhost:8000/openapi.json

---

## Environment Variables

Create a `.env` file in the `backend/` directory:

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DATABASE_URL` | Yes* | — | Full PostgreSQL connection URI from Supabase |
| `SUPABASE_DB_PASSWORD` | No | — | Reference only; must be embedded in `DATABASE_URL` |
| `PORT` | No | `8000` | HTTP server port |
| `MAX_TRANSACTION_AMOUNT` | No | `1000000` | Maximum allowed transaction amount |
| `APP_ENV` | No | `development` | `development`, `production`, or `test` |

\* If `DATABASE_URL` is empty, the app falls back to SQLite (`sqlite:///./test.db`) for local testing only.

**Example `.env`:**

```env
DATABASE_URL=postgresql://postgres.abcdefghijklmnop:YourPassword@aws-0-ap-south-1.pooler.supabase.com:5432/postgres
SUPABASE_DB_PASSWORD=YourPassword
PORT=8000
MAX_TRANSACTION_AMOUNT=1000000
APP_ENV=development
```

**Password special characters:** URL-encode them in `DATABASE_URL` (e.g. `@` → `%40`, `#` → `%23`).

The app automatically converts `postgresql://` to `postgresql+psycopg://` for the psycopg driver.

---

## Supabase Database Setup

### Step 1: Create a project

1. Go to [https://supabase.com](https://supabase.com) and sign in
2. Click **New Project**
3. Set organization, name, database password, and region
4. Wait for provisioning to complete

### Step 2: Get connection string

1. Open your project → **Project Settings** → **Database**
2. Under **Connection string**, select **URI**
3. Choose **Session pooler** (recommended) or **Direct connection**
4. Copy the string and replace `[YOUR-PASSWORD]` with your database password

Example format:

```
postgresql://postgres.<project-ref>:<password>@aws-0-<region>.pooler.supabase.com:5432/postgres
```

### Step 3: Apply schema

From the `backend/` directory with venv activated:

```bash
alembic upgrade head
```

### Step 4: Verify in Supabase

Open **Table Editor** in the Supabase dashboard. You should see:

- `users`
- `transactions`

---

## Running the Server

**Development (auto-reload):**

```bash
uvicorn app.main:app --reload --port 8000
```

**Production-style:**

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

**Health check:**

```bash
curl http://localhost:8000/dashboard
```

---

## Database Migrations

**Apply all migrations:**

```bash
alembic upgrade head
```

**Create a new migration (after model changes):**

```bash
alembic revision --autogenerate -m "describe change"
alembic upgrade head
```

**Rollback one revision:**

```bash
alembic downgrade -1
```

---

## API Documentation

All endpoints return JSON. Assignment-required endpoints are marked with ★.

### ★ POST `/transaction`

Create a new transaction. Auto-creates the user if they do not exist.

**Request body:**

```json
{
  "transactionId": "txn_1001",
  "userId": "user_1",
  "amount": 500,
  "type": "purchase"
}
```

**Validation rules:**

| Field | Rules |
|-------|-------|
| `transactionId` | Required, trimmed, max 255 chars |
| `userId` | Required, trimmed, max 255 chars |
| `amount` | Required, must be > 0, must not exceed `MAX_TRANSACTION_AMOUNT` |
| `type` | Required, trimmed, max 100 chars |

**Success — `201 Created`:**

```json
{
  "success": true,
  "message": "Transaction processed successfully"
}
```

**Duplicate — `409 Conflict`:**

```json
{
  "success": false,
  "message": "Duplicate transaction"
}
```

**Validation error — `422 Unprocessable Entity`:**

```json
{
  "success": false,
  "message": "amount: Amount must be greater than zero"
}
```

---

### ★ GET `/summary/{userId}`

Returns transaction aggregates and ranking score for a user.

**Success — `200 OK`:**

```json
{
  "userId": "user_1",
  "totalTransactions": 12,
  "totalAmount": 12000,
  "averageAmount": 1000,
  "rankingScore": 860,
  "lastTransaction": "2026-06-24T14:30:00"
}
```

**Not found — `404`:**

```json
{
  "success": false,
  "message": "User not found"
}
```

---

### ★ GET `/ranking`

Returns the leaderboard sorted by score (descending).

**Success — `200 OK`:**

```json
[
  { "rank": 1, "userId": "user_5", "score": 1230 },
  { "rank": 2, "userId": "user_2", "score": 1180 }
]
```

---

### GET `/users`

Lists all registered users with summary stats (used by frontend).

**Success — `200 OK`:**

```json
[
  {
    "userId": "user_1",
    "totalTransactions": 5,
    "totalAmount": 2500,
    "rankingScore": 425
  }
]
```

---

### GET `/leaderboard`

Extended leaderboard with transaction count and total amount (frontend table).

**Success — `200 OK`:**

```json
[
  {
    "rank": 1,
    "userId": "user_5",
    "score": 1230,
    "totalTransactions": 10,
    "totalAmount": 5000
  }
]
```

---

### GET `/dashboard`

Platform-wide statistics for the dashboard page.

**Success — `200 OK`:**

```json
{
  "totalUsers": 5,
  "totalTransactions": 42,
  "totalVolume": 125000,
  "topRankedUser": "user_5",
  "topRankedScore": 1230
}
```

---

## Database Schema

### `users`

| Column | Type | Constraints |
|--------|------|-------------|
| `id` | INTEGER | Primary key, auto-increment |
| `user_id` | VARCHAR(255) | UNIQUE, NOT NULL, indexed |
| `created_at` | TIMESTAMPTZ | NOT NULL, default `now()` |

### `transactions`

| Column | Type | Constraints |
|--------|------|-------------|
| `id` | INTEGER | Primary key, auto-increment |
| `transaction_id` | VARCHAR(255) | UNIQUE, NOT NULL |
| `user_id` | INTEGER | FK → `users.id`, ON DELETE CASCADE |
| `amount` | NUMERIC(18,2) | NOT NULL |
| `type` | VARCHAR(100) | NOT NULL |
| `created_at` | TIMESTAMPTZ | NOT NULL, default `now()` |

**Indexes:**

- `ix_users_user_id` on `users.user_id`
- `ix_transactions_user_id` on `transactions.user_id`
- `ix_transactions_created_at` on `transactions.created_at`
- `ix_transactions_user_created` on `(user_id, created_at)`

---

## Ranking Algorithm

Users are **not** ranked by raw transaction amount alone. A weighted score balances multiple factors.

### Formula

```
Score = (total_amount × 0.50)
      + (total_transactions × 25)
      + (consistency_bonus × 100)
      + (activity_bonus × 50)
      − spam_penalty
```

Final score is floored at `0` and rounded to 2 decimal places.

### Components

| Component | Calculation | Purpose |
|-----------|-------------|---------|
| **Amount weight** | `total_amount × 0.50` | Rewards higher transaction volume |
| **Transaction count** | `total_transactions × 25` | Rewards engagement frequency |
| **Consistency bonus** | `min(1.0, (distinct_days / total_transactions) × 2)` | Rewards spreading activity across multiple calendar days |
| **Activity bonus** | `min(1.0, (recent_7d_count / total_transactions) × 1.5)` | Rewards recent activity (last 7 days) |
| **Spam penalty** | `75 × spam_cluster_count` | Penalizes bursts of 5+ transactions within 60 seconds |

### Example

User with $500 total, 1 transaction, 1 distinct day, 1 recent transaction, no spam:

```
Score = (500 × 0.50) + (1 × 25) + (1.0 × 100) + (1.0 × 50) - 0 = 425
```

Implementation: `app/utils/ranking.py`

---

## Duplicate Prevention

Duplicate transactions are blocked **only using PostgreSQL** — no Redis or external cache.

### Strategy

1. `transaction_id` column has a **UNIQUE** constraint at the database level
2. Each insert runs inside `session.begin()` (explicit transaction)
3. If the same `transactionId` is submitted twice, PostgreSQL raises `IntegrityError`
4. `TransactionService` catches the error, rolls back, logs a warning, and returns **HTTP 409**
5. The duplicate is never processed twice

### Concurrent duplicate requests

Two simultaneous requests with the same `transactionId` race safely: only one insert succeeds; the other gets **409**.

---

## Concurrency & Data Consistency

- One SQLAlchemy `Session` per HTTP request (via FastAPI `Depends(get_db)`)
- Explicit transaction boundaries: `begin()` → work → `commit()` or `rollback()`
- Aggregates (`SUM`, `COUNT`, `AVG`) are computed in SQL — never stored in application memory
- User creation and transaction insert happen in the same transaction (atomic)
- Ranking scores are computed on read from live transaction data

---

## Error Handling & Logging

### Error response format

All API errors return consistent JSON:

```json
{
  "success": false,
  "message": "Human-readable error description"
}
```

### Status codes

| Code | When |
|------|------|
| `400` | Bad request |
| `404` | User not found |
| `409` | Duplicate transaction |
| `422` | Validation failure (Pydantic) |
| `500` | Internal server error (no stack traces exposed) |

### Logging

Configured in `app/core/logging.py` and `app/middleware/logging_middleware.py`.

**Logged events:**

- Incoming requests (method, path)
- Completed requests (status, duration in ms)
- Validation failures
- Duplicate transaction rejections
- Database errors
- Unhandled exceptions (full traceback server-side only)

**Log format:**

```
2026-06-24 12:00:00 | INFO | app.middleware.logging_middleware | Incoming request: GET /dashboard
```

---

## Testing

Tests use SQLite in-memory/file database — no Supabase connection required.

```bash
cd backend
venv\Scripts\activate   # Windows
pytest -v
```

### Test coverage

| Test | Description |
|------|-------------|
| `test_create_transaction_success` | Happy path transaction creation |
| `test_duplicate_transaction_returns_409` | Duplicate prevention |
| `test_validation_rejects_zero_amount` | Zero amount rejected |
| `test_validation_rejects_negative_amount` | Negative amount rejected |
| `test_validation_rejects_missing_fields` | Missing fields rejected |
| `test_summary_not_found` | Unknown user returns 404 |
| `test_summary_returns_aggregates` | Summary aggregates correct |
| `test_list_users` | User list endpoint |
| `test_ranking_sorted_descending` | Ranking order correct |
| `test_dashboard_stats` | Dashboard stats endpoint |
| `test_higher_amount_yields_higher_score` | Ranking unit test |
| `test_spam_penalty_reduces_score` | Spam penalty unit test |
| `test_distinct_days` | Consistency calculation |
| `test_spam_cluster_detection` | Spam cluster detection |

---

## Deployment

### Render / Railway (Backend)

1. Connect your Git repository
2. Set root directory to `backend`
3. **Build command:** `pip install -r requirements.txt`
4. **Start command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. **Release command:** `alembic upgrade head`
6. **Environment variables:**
   - `DATABASE_URL` — Supabase connection string
   - `PORT` — provided by platform
   - `MAX_TRANSACTION_AMOUNT` — e.g. `1000000`
   - `APP_ENV` — `production`

### Notes

- Use Supabase **Session pooler** URL for serverless/cloud deployments
- Ensure CORS allows your frontend domain (currently `allow_origins=["*"]` for development)
- Never commit `.env` to version control

---

## Troubleshooting

| Error | Cause | Fix |
|-------|-------|-----|
| `failed to resolve host 'aws-0-[region]...'` | Placeholder values in `.env` | Replace with real Supabase URL |
| `password authentication failed` | Wrong password or special chars | Fix password; URL-encode special characters |
| `relation "users" does not exist` | Migrations not run | Run `alembic upgrade head` |
| `uvicorn is not recognized` | venv not activated or deps missing | `venv\Scripts\activate` then `pip install -r requirements.txt` |
| Port already in use | Another process on 8000 | Use `--port 8001` or stop the other process |
| `psycopg2` build errors on Windows | Missing MSVC build tools | Project uses `psycopg` v3 which has prebuilt wheels |

---

## Future Improvements

- JWT authentication and role-based access control
- Rate limiting per user/IP
- Pagination for `/users` and `/leaderboard`
- Webhook notifications for high-value transactions
- Materialized views or cached scores for scale
- Background jobs for periodic score recalculation
- API versioning (`/v1/...`)
- Structured JSON logging for production observability

---

## Related Documentation

- Frontend README: `../frontend/README.md`
- Root project README: `../README.md`
- Interactive API docs: http://localhost:8000/docs (when server is running)
#   R a n k F l o w _ b a c k e n d  
 