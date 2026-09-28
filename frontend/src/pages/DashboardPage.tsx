import { useEffect, useState } from "react";

import { ApiError, listComplaints, updateComplaintStatus } from "../api/client";
import { CATEGORIES, PRIORITIES, STATUSES, humanize } from "../api/constants";
import type { Category, ComplaintList, Priority, Status } from "../api/types";
import { Badge } from "../components/Badge";

const PAGE_SIZE = 10;

export function DashboardPage() {
  const [category, setCategory] = useState<Category | "">("");
  const [priority, setPriority] = useState<Priority | "">("");
  const [status, setStatus] = useState<Status | "">("");
  const [page, setPage] = useState(1);

  const [data, setData] = useState<ComplaintList | null>(null);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);

  const [busyId, setBusyId] = useState<string | null>(null);
  const [rowErrors, setRowErrors] = useState<Record<string, string>>({});
  const [reloadKey, setReloadKey] = useState(0);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setLoadError(null);

    listComplaints({
      category: category || undefined,
      priority: priority || undefined,
      status: status || undefined,
      page,
      page_size: PAGE_SIZE,
    })
      .then((result) => {
        if (!cancelled) setData(result);
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setLoadError(err instanceof ApiError ? err.message : "Could not reach the server.");
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    // Ignore responses from stale requests (fast filter changes).
    return () => {
      cancelled = true;
    };
  }, [category, priority, status, page, reloadKey]);

  async function handleStatusChange(id: string, next: Status) {
    setBusyId(id);
    setRowErrors((prev) => {
      const copy = { ...prev };
      delete copy[id];
      return copy;
    });
    try {
      await updateComplaintStatus(id, next);
      setReloadKey((k) => k + 1);
    } catch (err) {
      // The server's own message (e.g. the 409 transition text) is shown verbatim.
      const message = err instanceof ApiError ? err.message : "Could not reach the server.";
      setRowErrors((prev) => ({ ...prev, [id]: message }));
    } finally {
      setBusyId(null);
    }
  }

  const totalPages = data ? Math.max(1, Math.ceil(data.total / data.page_size)) : 1;

  return (
    <section>
      <h2>Operations dashboard</h2>

      <div className="card filters">
        <label>
          Category
          <select
            value={category}
            onChange={(e) => {
              setCategory(e.target.value as Category | "");
              setPage(1);
            }}
          >
            <option value="">All</option>
            {CATEGORIES.map((c) => (
              <option key={c} value={c}>{humanize(c)}</option>
            ))}
          </select>
        </label>
        <label>
          Priority
          <select
            value={priority}
            onChange={(e) => {
              setPriority(e.target.value as Priority | "");
              setPage(1);
            }}
          >
            <option value="">All</option>
            {PRIORITIES.map((p) => (
              <option key={p} value={p}>{humanize(p)}</option>
            ))}
          </select>
        </label>
        <label>
          Status
          <select
            value={status}
            onChange={(e) => {
              setStatus(e.target.value as Status | "");
              setPage(1);
            }}
          >
            <option value="">All</option>
            {STATUSES.map((s) => (
              <option key={s} value={s}>{humanize(s)}</option>
            ))}
          </select>
        </label>
      </div>

      {loadError && (
        <div role="alert" className="alert alert-error">{loadError}</div>
      )}
      {loading && <p className="hint" role="status">Loading…</p>}

      {data && data.items.length === 0 && !loading && (
        <p className="hint">No complaints match these filters.</p>
      )}

      <ul className="complaint-list">
        {data?.items.map((c) => (
          <li key={c.id} className="card complaint">
            <div className="complaint-head">
              <Badge value={c.category} />
              <Badge value={c.priority} />
              <Badge value={c.status} />
              <span className="hint">{new Date(c.created_at).toLocaleString()}</span>
            </div>
            <p className="summary">{c.ai_summary ?? c.text}</p>
            <p className="hint">
              {c.location} · triaged by <code>{c.triaged_by}</code> ({c.triage_latency_ms} ms)
            </p>

            <div className="complaint-actions">
              <select
                aria-label={`Change status of complaint ${c.id}`}
                value=""
                disabled={busyId === c.id}
                onChange={(e) => {
                  if (e.target.value) void handleStatusChange(c.id, e.target.value as Status);
                }}
              >
                <option value="">Move to…</option>
                {STATUSES.filter((s) => s !== c.status).map((s) => (
                  <option key={s} value={s}>{humanize(s)}</option>
                ))}
              </select>
            </div>

            {rowErrors[c.id] && (
              <div role="alert" className="alert alert-error">{rowErrors[c.id]}</div>
            )}
          </li>
        ))}
      </ul>

      {data && (
        <div className="pager">
          <button type="button" disabled={page <= 1 || loading} onClick={() => setPage((p) => p - 1)}>
            Previous
          </button>
          <span>
            Page {data.page} of {totalPages} · {data.total} total
          </span>
          <button
            type="button"
            disabled={page >= totalPages || loading}
            onClick={() => setPage((p) => p + 1)}
          >
            Next
          </button>
        </div>
      )}
    </section>
  );
}