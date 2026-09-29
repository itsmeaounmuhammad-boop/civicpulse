# Triage system reference

## Providers
| Provider | `TRIAGE_PROVIDER` value | Network | Notes |
|---|---|---|---|
| Groq (LLM) | `llm` | Yes (Groq API) | Structured JSON, 10s timeout |
| Ollama | `ollama` | No (local container) | Slower, weaker classification |
| Rules | `rules` | No | Deterministic keyword match |
| Simulated | `simulated` | No | CI only — deterministic hash-based fake |

## Resilience pipeline (`TriageService`)
1. Content-hash lookup in Redis (24h TTL) — duplicate complaints cost one
   inference, not nine.
2. On a miss: call the active provider with a 10s timeout.
3. On timeout/429/5xx: one retry with jitter (0.1–0.5s).
4. On exhausted retries or any non-retryable failure: fall back to
   `RuleBasedTriage`, record `triaged_by = "rules:fallback"`.
5. Only genuine provider output is cached — fallback results are never
   cached, so a duplicate complaint arriving after the provider recovers
   gets a real answer, not a stale degraded one.

## Prompt-injection guardrail
Complaint text is wrapped in `<complaint>` tags in the LLM prompt and the
system prompt explicitly instructs the model to treat that content as data,
never instructions. The output is still constrained to the `TriageResult`
Pydantic schema regardless of what the model returns — an out-of-enum
category is rejected outright. See `backend/tests/test_complaints_api.py::
test_prompt_injection_does_not_bypass_schema`.