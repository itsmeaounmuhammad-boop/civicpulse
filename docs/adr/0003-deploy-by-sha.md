# ADR-0003: Deploy by commit SHA, never by :latest

## Status
Accepted

## Decision
Every image is pushed to GHCR tagged with the commit SHA
(`ghcr.io/.../civicpulse-backend:<sha>`). `cd.yml` also pushes `:latest` for
convenience (e.g. `docker pull` without knowing a SHA), but `:latest` is
NEVER what gets deployed — `kubectl apply` always references the SHA tag,
substituted into the Kustomize prod overlay via `kustomize edit set image`.

## Consequences
- "What is production running?" has a one-word answer: `kubectl get
  deployment backend -n civicpulse -o jsonpath='{.spec.template.spec.
  containers[0].image}'` returns the exact SHA, traceable to one exact
  `git show <sha>`.
- Rollback is unambiguous: `kubectl rollout undo` returns to the previous
  SHA-tagged image, not to whatever `:latest` happened to point at when the
  rollback ran.
- The trade-off: every deploy requires knowing/passing the SHA rather than
  a human-memorable tag — mitigated by `cd.yml` doing this substitution
  automatically, so no human ever needs to type a SHA by hand.