# ADR-0002: Runtime configuration via relative /api, not a baked-in URL

## Status
Accepted

## Context
Vite bakes `import.meta.env` values into static JS at build time. If the
backend URL were baked in, the frontend image would be environment-specific,
breaking build-once-deploy-many.

## Decision
The frontend calls a relative `/api` path only — never an absolute backend
URL. Whatever serves the page resolves it:
- **Local dev**: Vite's dev server proxies `/api` to `http://localhost:8000`
  (`vite.config.ts`).
- **Docker Compose / Kubernetes**: nginx, serving the built static files,
  proxies `/api/` to the backend Service (`frontend/nginx.conf`).
- **Kubernetes specifically**: the Ingress additionally routes `/api` to the
  backend Service directly, bypassing the in-container nginx proxy for that
  path (nginx still serves everything under `/`).

## Consequences
- The exact same frontend image runs unmodified in dev, Compose, and any
  Kubernetes environment — no rebuild, no environment-specific tag.
- No backend URL, port, or hostname ever appears in the browser bundle.
- The trade-off: the frontend cannot be deployed as static files on a CDN
  with no reverse proxy in front of it, since it has no way to reach a
  backend without one. This is an acceptable constraint for this system.