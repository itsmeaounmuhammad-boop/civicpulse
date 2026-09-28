import { useCallback, useEffect, useState } from "react";

import { ApiError, getStats } from "../api/client";
import { CATEGORIES, PRIORITIES, humanize } from "../api/constants";
import type { StatsResult } from "../api/types";

interface BarsProps {
  title: string;
  keys: string[];
  counts: Record<string, number>;
}

function Bars({ title, keys, counts }: BarsProps) {
  const max = Math.max(1, ...keys.map((k) => counts[k] ?? 0));
  return (
    <div className="card">
      <h3>{title}</h3>
      <ul className="bars">
        {keys.map((k) => {
          const value = counts[k] ?? 0;
          return (
            <li key={k}>
              <span className="bar-label">{humanize(k)}</span>
              <span className="bar-track">
                <span className="bar-fill" style={{ width: `${(value / max) * 100}%` }} />
              </span>
              <span className="bar-value">{value}</span>
            </li>
          );
        })}
      </ul>
    </div>
  );
}

export function StatsPage() {
  const [result, setResult] = useState<StatsResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setResult(await getStats());
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not reach the server.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  return (
    <section>
      <div className="stats-head">
        <h2>Statistics</h2>
        <button type="button" onClick={() => void load()} disabled={loading}>
          {loading ? "Loading…" : "Refresh"}
        </button>
      </div>

      {error && <div role="alert" className="alert alert-error">{error}</div>}

      {result && (
        <>
          <p>
            <strong>{result.stats.total}</strong> complaints total ·{" "}
            <span
              className={`cache-badge ${result.cacheHit ? "cache-hit" : "cache-miss"}`}
              data-testid="cache-status"
            >
              X-Cache: {result.cacheHit ? "HIT" : "MISS"}
            </span>
          </p>
          <div className="grid-2">
            <Bars title="By category" keys={CATEGORIES} counts={result.stats.by_category} />
            <Bars title="By priority" keys={PRIORITIES} counts={result.stats.by_priority} />
          </div>
        </>
      )}
    </section>
  );
}