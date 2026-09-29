# AI Usage Disclosure

Per course policy, honest attribution carries no penalty.

## Tool used
Claude (Anthropic), via chat.

## What it wrote or shaped
Nearly all backend code (FastAPI app, models, triage providers, services,
routes, tests), the frontend skeleton and API client, Dockerfiles,
docker-compose files, Kubernetes manifests, and CI/CD workflows were
drafted by Claude in response to our step-by-step instructions, then
reviewed, tested, and in several cases debugged and corrected by us
against real running infrastructure (Postgres, Redis, Docker, and a local
Kubernetes cluster).

## What we changed and why
- Fixed a `ModuleNotFoundError: greenlet` by adding the `sqlalchemy[asyncio]`
  extra to `pyproject.toml` — the async engine failed at import time without
  it, discovered when running `alembic upgrade head` for the first time.
- Fixed `app/models.py` where the `Complaint.text` column attribute shadowed
  SQLAlchemy's `text()` helper function used elsewhere in the same class body.
- Changed the API's validation error response from FastAPI's default 422 to
  the assignment-required 400 with a field-level error body.
- Fixed `Retry-After` header being silently dropped when raised via
  `HTTPException` instead of set on a `Response` object directly.
- [Add: any further fixes either of you made while working through later
  phases — Kubernetes manifest corrections, CI workflow debugging, etc.]

## Verification
Every backend/data-layer claim was verified against a real running
docker-compose stack (Postgres 16, Redis 7) before being merged — migrations
were actually run, the seed script's idempotency was actually tested twice,
and the full pytest suite was actually executed (20+ tests, ≥65% coverage
confirmed via `pytest --cov`), not merely written.

## What we can defend at viva
Both of us can explain any file in this repository, including code
initially drafted by the other partner, per the pair-programming and PR
review process documented in our commit/PR history.