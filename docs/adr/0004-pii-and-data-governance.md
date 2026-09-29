# ADR-0004: PII handling for hosted LLM triage

## Status
Accepted

## Context
Citizen complaints routinely contain names, addresses, and phone numbers
(`reporter_contact`). The default triage provider (Groq) is a free-tier
hosted API. Google's free Gemini tier explicitly states it may use inputs to
improve its models; Groq's terms were reviewed as of the date in this ADR
and do not currently make an equivalent claim for the tier used here, but
free-tier terms can change without notice.

## Decision
- Only `text` and `location` are sent to the triage provider.
  `reporter_contact` is NEVER included in the prompt — it plays no role in
  classification and is the single most sensitive field on the row.
- Complaint text itself (which may still contain a name or phone number a
  citizen volunteers inside the free-text body) IS sent as-is. We accept this
  exposure rather than attempting automated redaction, because naive PII
  redaction (regex-based phone/name stripping) has a well-known false
  negative rate and would give a false sense of safety without real
  guarantees — silently sending unredacted text is more honest than silently
  sending falsely-redacted text.
- The local Ollama path exists specifically as the zero-exposure alternative:
  when `TRIAGE_PROVIDER=ollama`, no complaint text leaves the machine at all.
  Teams or deployments with stricter privacy requirements should default to
  this provider.

## Consequences
- A citizen who includes personal detail inside their complaint's free text
  accepts some exposure to whichever hosted provider is active — documented
  here rather than hidden.
- `reporter_contact` never appears in any LLM provider's logs or training
  data, regardless of provider.
- If a future requirement demands zero third-party exposure, the fix is an
  environment variable change (`TRIAGE_PROVIDER=ollama`), not a code change —
  a direct consequence of ADR-0001's provider abstraction.