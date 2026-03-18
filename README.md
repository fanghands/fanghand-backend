```
  ███████╗ █████╗ ███╗   ██╗ ██████╗ ██╗  ██╗ █████╗ ███╗   ██╗██████╗
  ██╔════╝██╔══██╗████╗  ██║██╔════╝ ██║  ██║██╔══██╗████╗  ██║██╔══██╗
  █████╗  ███████║██╔██╗ ██║██║  ███╗███████║███████║██╔██╗ ██║██║  ██║
  ██╔══╝  ██╔══██║██║╚██╗██║██║   ██║██╔══██║██╔══██║██║╚██╗██║██║  ██║
  ██║     ██║  ██║██║ ╚████║╚██████╔╝██║  ██║██║  ██║██║ ╚████║██████╔╝
  ╚═╝     ╚═╝  ╚═╝╚═╝  ╚═══╝ ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝╚═════╝
                              BACKEND
```

**FastAPI backend for the FangHand autonomous AI agent marketplace.**

[![MIT License](https://img.shields.io/badge/license-MIT-00ff88?style=flat-square)](LICENSE)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=flat-square)](https://fastapi.tiangolo.com)
[![Python 3.12](https://img.shields.io/badge/Python-3.12-3776AB?style=flat-square)](https://python.org)
[![Solana](https://img.shields.io/badge/chain-Solana-9945FF?style=flat-square)](https://solana.com)

---

> **Status: Stub Mode**
> All external integrations (Stripe, Solana, OpenFang, Resend) are stubbed with TODO markers. The API runs standalone and returns mock responses. No real payments, chain transactions, or agent spawning occurs.

---

## Tech Stack

| Layer | Choice |
|---|---|
| Framework | FastAPI 0.115 (async, auto OpenAPI docs) |
| Database | PostgreSQL 15 (via Supabase or local) |
| ORM | SQLAlchemy 2.0 async (Mapped[] style) |
| Migrations | Alembic |
| Auth | JWT (SIWS — Sign-In With Solana) |
| Payments | Stripe (subscriptions) + Solana (SOL/FGH/USDC) |
| Cache/Queue | Redis + Celery 5.4 |
| Validation | Pydantic v2 |
| Logging | Loguru (structured) |
| Monitoring | Sentry SDK |
| Deployment | Docker + Railway |

## Quick Start

### With Docker (recommended)

```bash
cd backend
cp .env.example .env
docker compose up
```

API: [http://localhost:8000](http://localhost:8000)
Docs: [http://localhost:8000/docs](http://localhost:8000/docs)
Health: [http://localhost:8000/health](http://localhost:8000/health)

### Without Docker

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env

# Start PostgreSQL and Redis locally, then:
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

### Celery Workers (separate terminals)

```bash
celery -A app.workers.celery_app worker -l info -c 4
celery -A app.workers.celery_app beat -l info
```

## API Routes

### Auth — `/api/v1/auth`

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/auth/wallet-connect` | No | Sign-In With Solana |
| POST | `/auth/refresh` | Refresh | Refresh JWT |
| GET | `/auth/me` | JWT | Current user profile |
| PATCH | `/auth/me` | JWT | Update profile |

### Hands — `/api/v1/hands`

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| GET | `/hands` | No | List with filters + pagination |
| GET | `/hands/{slug}` | No | Hand detail |
| GET | `/hands/{slug}/reviews` | No | User reviews |
| POST | `/hands/{slug}/review` | JWT | Submit review |

### Activations — `/api/v1/activations`

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| GET | `/activations` | JWT | List user's activations |
| POST | `/activations` | JWT | Create activation |
| GET | `/activations/{id}` | JWT | Activation detail |
| POST | `/activations/{id}/pause` | JWT | Pause hand |
| POST | `/activations/{id}/resume` | JWT | Resume hand |
| DELETE | `/activations/{id}` | JWT | Cancel |
| GET | `/activations/{id}/status/stream` | JWT | SSE live status |

### Runs — `/api/v1/runs`

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/runs` | JWT | Trigger pay-per-run |
| GET | `/runs/{id}` | JWT | Run detail |
| GET | `/runs/{id}/output` | JWT | SSE output stream |
| GET | `/runs/history` | JWT | Run history |

### Payments — `/api/v1/payments`

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/payments/stripe/create-session` | JWT | Stripe checkout |
| POST | `/payments/credit/deposit` | JWT | SOL credit deposit |
| GET | `/payments/credit/balance` | JWT | Credit balance |
| GET | `/payments/burns` | No | FGH burn history |
| GET | `/payments/burns/stats` | No | Burn aggregate stats |
| GET | `/payments/burns/stream` | No | SSE burn ticker |

### Builders — `/api/v1/builders`

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/builders/register` | JWT | Register as builder |
| GET | `/builders/me` | Builder | Profile + stats |
| POST | `/builders/hands/submit` | Builder | Submit new hand |
| GET | `/builders/me/earnings` | Builder | Revenue history |

### Webhooks — `/webhooks`

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/webhooks/stripe` | Stripe-Sig | Stripe events |
| POST | `/webhooks/solana` | HMAC | Helius tx confirmation |

## Project Structure

```
backend/
├── app/
│   ├── main.py                     # FastAPI app + lifespan + CORS
│   ├── config.py                   # Pydantic Settings (all env vars)
│   ├── database.py                 # Async SQLAlchemy engine + sessions
│   │
│   ├── api/
│   │   ├── deps.py                 # get_db, get_current_user, require_builder, rate_limit
│   │   └── v1/
│   │       ├── router.py           # Aggregated /api/v1 router
│   │       ├── auth.py             # SIWS, JWT, profile
│   │       ├── hands.py            # Marketplace listing + detail
│   │       ├── activations.py      # CRUD + SSE status stream
│   │       ├── runs.py             # Pay-per-run + SSE output
│   │       ├── payments.py         # Stripe, credit wallet, burns
│   │       ├── builders.py         # Builder portal
│   │       ├── dashboard.py        # Overview + stats
│   │       └── webhooks.py         # Stripe + Solana
│   │
│   ├── models/                     # SQLAlchemy 2.0 models
│   │   ├── base.py                 # DeclarativeBase + TimestampMixin
│   │   ├── user.py, hand.py, activation.py, run.py
│   │   ├── payment.py, subscription.py, builder.py
│   │   ├── hand_review.py, builder_stake.py
│   │   ├── fgh_burn.py, hand_metric.py, credit_transaction.py
│   │   └── __init__.py             # Exports all for Alembic
│   │
│   ├── schemas/                    # Pydantic v2 schemas
│   │   ├── auth.py, hand.py, activation.py, run.py
│   │   ├── payment.py, builder.py, common.py
│   │   └── __init__.py
│   │
│   ├── services/                   # Business logic
│   │   ├── openfang_client.py      # OpenFang REST + SSE client
│   │   ├── activation_service.py   # Spawn, pause, resume, cancel
│   │   ├── payment_service.py      # Stripe checkout + webhooks
│   │   ├── solana_service.py       # On-chain verification
│   │   ├── burn_service.py         # FGH token burns (50%)
│   │   ├── credit_service.py       # Prepaid SOL wallet
│   │   ├── builder_service.py      # Staking, review, payouts
│   │   └── email_service.py        # Transactional emails
│   │
│   ├── workers/                    # Celery background tasks
│   │   ├── celery_app.py           # Celery instance + beat schedule
│   │   └── tasks/
│   │       ├── hand_tasks.py       # activate_hand, trigger_run
│   │       ├── burn_tasks.py       # execute_fgh_burn, batch_burn
│   │       ├── payout_tasks.py     # Monthly builder payouts
│   │       └── sync_tasks.py       # FGH balances, agent health
│   │
│   ├── middleware/                  # Request pipeline
│   │   ├── auth.py                 # JWT decode middleware
│   │   ├── rate_limit.py           # Redis GCRA rate limiter
│   │   └── logging.py              # Structured request logging
│   │
│   └── utils/
│       ├── crypto.py               # Solana signature verification
│       ├── toml_validator.py       # HAND.toml schema validation
│       ├── pagination.py           # Cursor-based pagination
│       └── constants.py            # Fee %, burn %, page sizes
│
├── alembic/                        # Database migrations
│   ├── env.py                      # Async migration runner
│   └── versions/
│       └── 001_initial_schema.py   # Full initial migration (12 tables)
│
├── tests/                          # pytest + httpx
│   ├── conftest.py                 # Fixtures (async_client, mock_user)
│   ├── test_health.py
│   ├── test_auth.py
│   ├── test_hands.py
│   ├── test_activations.py
│   ├── test_runs.py
│   ├── test_payments.py
│   └── test_builders.py
│
├── Dockerfile
├── docker-compose.yml              # api + worker + beat + redis + postgres
├── railway.toml                    # Railway deployment config
├── requirements.txt
├── alembic.ini
├── .env.example
└── .gitignore
```

## Database Schema

12 tables with Row Level Security:

```
users ──┬── activations ──── runs
        │        │
        │        └── hand_metrics
        │
        ├── payments
        ├── credit_transactions
        │
        ├── builders ──┬── hand_reviews
        │              └── builder_stakes
        │
        └── subscriptions

hands ──── fgh_burns
```

## Stub Services

All external integrations return mock data. Replace with real implementations:

| Service | File | What to implement |
|---|---|---|
| OpenFang | `services/openfang_client.py` | REST calls to OpenFang daemon |
| Stripe | `services/payment_service.py` | Checkout sessions, webhook handlers |
| Solana | `services/solana_service.py` | On-chain tx verification, balance checks |
| Burns | `services/burn_service.py` | SPL token burn transactions |
| Email | `services/email_service.py` | Resend transactional emails |

## Testing

```bash
pip install pytest pytest-asyncio httpx
pytest tests/ -v
```

## Deployment (Railway)

1. Push to GitHub
2. Connect repo to Railway
3. Add Redis plugin
4. Set all env vars from `.env.example`
5. Add Celery worker service: `celery -A app.workers.celery_app worker -l info`
6. Add Celery beat service: `celery -A app.workers.celery_app beat -l info`
7. Run migrations: `alembic upgrade head`

## License

[MIT](LICENSE)

---

<sub>Built with FastAPI, SQLAlchemy, Celery, and Solana. Powered by OpenFang.</sub>
