/**
 * Runtime configuration (see ADR-0002).
 *
 * There is deliberately NO absolute backend URL here. The browser always calls
 * a relative "/api", and whatever serves the page (Vite proxy in dev, nginx in
 * Compose/Kubernetes) forwards it to the backend. Nothing in this bundle is
 * environment-specific, so the same image runs in any environment.
 */
export const API_BASE = "/api";