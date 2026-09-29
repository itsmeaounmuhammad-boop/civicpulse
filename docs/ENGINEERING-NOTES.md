# Engineering Notes

## 1. Three things that differ between laptop and CI runner
1. **Database identity** — locally, Postgres runs as a long-lived Compose
   service (`compose.yaml` `postgres:` service, host-mapped port 5432); in
   CI it's an ephemeral GitHub Actions service container
   (`.github/workflows/ci.yml`, `jobs.test-backend.services.postgres`),
   torn down after the job. Frozen by: the `services:` block in `ci.yml`.
2. **Triage provider** — locally can be `llm`/`ollama`/`rules`/`simulated`
   via `.env`; CI is hard-pinned to `simulated`
   (`ci.yml`, `env: TRIAGE_PROVIDER: simulated` under `test-backend`), so
   test runs never depend on network availability or a real model's output.
3. **Image target** — locally the backend Dockerfile builds the `dev` stage
   (`compose.yaml`, `target: dev`, includes pytest/ruff/mypy and `--reload`);
   CI/CD build the `runtime` stage (`ci.yml`/`cd.yml`,
   `docker build ... --target runtime`), which excludes dev tooling entirely.

## 2. CI/CD maturity ladder position
_(Insert your course's Lecture 03 slide 32 ladder here and place yourself
honestly — based on what's built: automated build+test+scan+deploy on every
merge to main, no manual gate beyond PR review, ephemeral-cluster smoke test.
Likely rung: "continuous deployment" with a human-reviewed PR gate before
main, not fully autonomous. Next rung up would remove the human PR-approval
requirement and rely entirely on automated checks + progressive rollout —
name what that would need, e.g. canary analysis, automated rollback on
error-rate SLO breach.)_

## 3. Build-once-deploy-many
The exact line: `frontend/nginx.conf`, `location /api/ { proxy_pass
http://backend:8000; }` combined with `frontend/src/config.ts`,
`API_BASE = "/api"` — no absolute URL is ever compiled into the JS bundle.
Without this line, the frontend image would need a rebuild per environment
(dev/staging/prod each needing a different baked-in backend URL), which is
exactly what build-once-deploy-many forbids.

## 4. Correctness with a probabilistic component
With `TRIAGE_PROVIDER=llm`, "correct" cannot mean "produces the exact same
category every time" — it means "produces a value from the correct enum,
validated against the `TriageResult` schema, within the timeout, with a
graceful and observable degradation path when it fails." CI stays
deterministic by pinning to `SimulatedTriage`
(`backend/tests/conftest.py`, `os.environ["TRIAGE_PROVIDER"] = "simulated"`)
and testing the failure/fallback path explicitly with `SimulatedTriage(
always_fail=True)` rather than ever invoking a real network call in the
test suite.

## 5. HPA lag
_(Fill in from `docs/evidence/hpa-watch.txt` captured in Phase 15: note the
timestamp offered load crossed the scale-up threshold vs the timestamp
`kubectl get hpa -w` showed replica count actually increase. Discuss where
the gap went — metrics-server's scrape interval, the HPA controller's own
sync period (default 15s), and pod startup time before it counts as Ready.)_

## 6. Why VPA is in Off mode
HPA scales replica *count* based on CPU utilization (usage ÷ requested CPU).
An Auto-mode VPA changes the *requested* CPU value on the same pods. If both
ran live together: VPA raises a pod's CPU request → the denominator in HPA's
utilization calculation grows → computed utilization drops → HPA scales
in (fewer replicas) → remaining pods take more real load → VPA raises the
request again → loop. Recommender-only mode (`k8s/base/vpa.yaml`,
`updateMode: "Off"`) breaks this loop by requiring a human to read the
recommendation and update `resources.requests` deliberately, once.

## 7. internal: true and the hosted LLM
`compose.yaml`'s `internal` network has no route to the outside world, but
`backend` is deliberately placed on BOTH `edge` and `internal`
(`networks: [edge, internal]`) — it's the one component that legitimately
needs both: internal access to Postgres/Redis, and edge access outward to
Groq. Postgres and Redis stay `internal`-only since they have no legitimate
reason to reach the internet at all.

## 8. The failure
_(This is yours to fill in honestly — the real bug that cost real time. Two
strong candidates from what we've already hit and fixed together:
- The `greenlet` ModuleNotFoundError (Alembic import chain failing because
  `sqlalchemy[asyncio]` wasn't declared) — symptom, what was wrongly
  believed first, and the exact traceback line that revealed it.
- The `text` column shadowing SQLAlchemy's `text()` function in models.py.
Pick whichever actually cost more real time/confusion for you, and write it
in your own words with the actual command/log line.)_