# ADR-0001: TriageProvider as a Protocol, not an abstract base class

## Status
Accepted

## Context
The AI layer must support four interchangeable classifiers (LLM via Groq,
Ollama, rule-based, simulated), selected at runtime by an environment
variable, with none of the calling code aware of which one is active.

## Decision
`TriageProvider` is a `typing.Protocol`, not an ABC. Each implementation
(`LLMTriage`, `OllamaTriage`, `RuleBasedTriage`, `SimulatedTriage`) satisfies
the interface structurally — same method signature, no inheritance required.
A factory (`app/providers/triage/factory.py`) is the single place that reads
`TRIAGE_PROVIDER` and constructs the right one.

Every provider does exactly one honest attempt at classification and either
returns a valid `TriageResult` or raises. Timeout, retry, fallback and
content-hash caching are NOT the provider's job — they live one layer up, in
`TriageService`, so the resilience logic is written once and applies
identically no matter which provider is active.

## Consequences
- Adding a fifth provider (e.g. OpenRouter) means writing one class with a
  `triage()` method — no interface registration, no base-class boilerplate.
- Tests can inject `SimulatedTriage(always_fail=True)` directly into
  `TriageService` without touching the factory or any environment variable.
- The trade-off: Protocol gives no runtime enforcement that a class actually
  implements `triage()` correctly — a typo in the method name fails silently
  at the type-checker level (mypy) rather than at import time. We accept this
  since it's caught by CI's mypy job and by the interface conformance the
  test suite exercises against every real implementation.