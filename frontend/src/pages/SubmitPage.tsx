import { useEffect, useState, type FormEvent } from "react";

import { ApiError, createComplaint } from "../api/client";
import type { Complaint } from "../api/types";
import { Badge } from "../components/Badge";

// Mirrors the backend's ComplaintCreate rules. The server stays the authority;
// this only saves the user a round trip.
const LIMITS = {
  text: { min: 10, max: 2000 },
  location: { min: 3, max: 200 },
  contact: { max: 100 },
};

type FieldErrors = Partial<Record<"text" | "location" | "reporter_contact", string>>;

function validate(text: string, location: string, contact: string): FieldErrors {
  const errors: FieldErrors = {};
  if (text.length < LIMITS.text.min || text.length > LIMITS.text.max) {
    errors.text = `Description must be ${LIMITS.text.min}–${LIMITS.text.max} characters.`;
  }
  if (location.length < LIMITS.location.min || location.length > LIMITS.location.max) {
    errors.location = `Location must be ${LIMITS.location.min}–${LIMITS.location.max} characters.`;
  }
  if (contact.length > LIMITS.contact.max) {
    errors.reporter_contact = `Contact must be at most ${LIMITS.contact.max} characters.`;
  }
  return errors;
}

export function SubmitPage() {
  const [text, setText] = useState("");
  const [location, setLocation] = useState("");
  const [contact, setContact] = useState("");

  const [fieldErrors, setFieldErrors] = useState<FieldErrors>({});
  const [formError, setFormError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [elapsed, setElapsed] = useState(0);
  const [result, setResult] = useState<Complaint | null>(null);

  // Honest loading state: AI triage takes seconds, so show a running timer.
  useEffect(() => {
    if (!submitting) return;
    setElapsed(0);
    const timer = setInterval(() => setElapsed((s) => s + 1), 1000);
    return () => clearInterval(timer);
  }, [submitting]);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setFormError(null);
    setResult(null);

    const cleanText = text.trim();
    const cleanLocation = location.trim();
    const cleanContact = contact.trim();

    const errors = validate(cleanText, cleanLocation, cleanContact);
    setFieldErrors(errors);
    if (Object.keys(errors).length > 0) return;

    setSubmitting(true);
    try {
      const created = await createComplaint({
        text: cleanText,
        location: cleanLocation,
        reporter_contact: cleanContact || null,
      });
      setResult(created);
      setText("");
      setLocation("");
      setContact("");
    } catch (err) {
      if (err instanceof ApiError) {
        // Field-level errors from the server's 400 body.
        if (err.fieldErrors.length > 0) {
          const serverErrors: FieldErrors = {};
          for (const fe of err.fieldErrors) {
            if (fe.field === "text" || fe.field === "location" || fe.field === "reporter_contact") {
              serverErrors[fe.field] = fe.message;
            }
          }
          setFieldErrors(serverErrors);
        }
        if (err.status === 429) {
          const wait = err.retryAfterSeconds ? ` Try again in ${err.retryAfterSeconds}s.` : "";
          setFormError(`Too many submissions.${wait}`);
        } else {
          setFormError(err.message);
        }
      } else {
        setFormError("Could not reach the server. Check your connection and try again.");
      }
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <section>
      <h2>Submit a complaint</h2>

      <form className="card form" onSubmit={handleSubmit} noValidate>
        <label>
          What is the problem?
          <textarea
            rows={5}
            value={text}
            onChange={(e) => setText(e.target.value)}
            disabled={submitting}
            aria-invalid={Boolean(fieldErrors.text)}
            placeholder="e.g. Burst water main flooding Street 12 since fajr, water entering ground floors"
          />
          <span className="hint">{text.trim().length} / {LIMITS.text.max}</span>
          {fieldErrors.text && <span className="field-error">{fieldErrors.text}</span>}
        </label>

        <label>
          Location
          <input
            type="text"
            value={location}
            onChange={(e) => setLocation(e.target.value)}
            disabled={submitting}
            aria-invalid={Boolean(fieldErrors.location)}
            placeholder="e.g. Street 12, Sector G-10/2"
          />
          {fieldErrors.location && <span className="field-error">{fieldErrors.location}</span>}
        </label>

        <label>
          Contact (optional)
          <input
            type="text"
            value={contact}
            onChange={(e) => setContact(e.target.value)}
            disabled={submitting}
            aria-invalid={Boolean(fieldErrors.reporter_contact)}
            placeholder="Phone or email"
          />
          {fieldErrors.reporter_contact && (
            <span className="field-error">{fieldErrors.reporter_contact}</span>
          )}
        </label>

        {formError && (
          <div role="alert" className="alert alert-error">
            {formError}
          </div>
        )}

        <button type="submit" disabled={submitting}>
          {submitting ? "Triaging…" : "Submit complaint"}
        </button>

        {submitting && (
          <p className="hint" role="status">
            Analysing your complaint with AI triage… {elapsed}s. This can take several seconds.
          </p>
        )}
      </form>

      {result && (
        <div className="card result" role="status">
          <h3>Complaint received</h3>
          <p className="summary">{result.ai_summary ?? "No summary available."}</p>
          <dl className="result-grid">
            <dt>Category</dt>
            <dd><Badge value={result.category} /></dd>
            <dt>Priority</dt>
            <dd><Badge value={result.priority} /></dd>
            <dt>Triaged by</dt>
            <dd><code>{result.triaged_by}</code> ({result.triage_latency_ms} ms)</dd>
            <dt>Reference</dt>
            <dd><code>{result.id}</code></dd>
          </dl>
        </div>
      )}
    </section>
  );
}