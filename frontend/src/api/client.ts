import { API_BASE } from "../config";
import type {
  Complaint,
  ComplaintCreate,
  ComplaintFilters,
  ComplaintList,
  FieldError,
  ProvidersMeta,
  Status,
  Stats,
  StatsResult,
} from "./types";

/**
 * Error thrown for any non-2xx response. `message` is the server's own
 * `detail` string, unmodified, so the UI can show e.g. the 409 transition
 * message verbatim instead of a generic "something went wrong".
 */
export class ApiError extends Error {
  readonly status: number;
  readonly fieldErrors: FieldError[];
  readonly retryAfterSeconds: number | null;

  constructor(
    status: number,
    message: string,
    fieldErrors: FieldError[] = [],
    retryAfterSeconds: number | null = null,
  ) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.fieldErrors = fieldErrors;
    this.retryAfterSeconds = retryAfterSeconds;
  }
}

async function request<T>(
  path: string,
  init?: RequestInit,
): Promise<{ data: T; headers: Headers }> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
  });

  if (!response.ok) {
    let message = `Request failed (${response.status})`;
    let fieldErrors: FieldError[] = [];
    try {
      const body = await response.json();
      if (typeof body.detail === "string") {
        message = body.detail;
      }
      if (Array.isArray(body.errors)) {
        fieldErrors = body.errors as FieldError[];
      }
    } catch {
      // Response had no JSON body; keep the generic message.
    }
    const retryAfterHeader = response.headers.get("Retry-After");
    throw new ApiError(
      response.status,
      message,
      fieldErrors,
      retryAfterHeader ? Number(retryAfterHeader) : null,
    );
  }

  const data = (await response.json()) as T;
  return { data, headers: response.headers };
}

export async function createComplaint(payload: ComplaintCreate): Promise<Complaint> {
  const { data } = await request<Complaint>("/complaints", {
    method: "POST",
    body: JSON.stringify(payload),
  });
  return data;
}

export async function getComplaint(id: string): Promise<Complaint> {
  const { data } = await request<Complaint>(`/complaints/${id}`);
  return data;
}

export async function listComplaints(filters: ComplaintFilters = {}): Promise<ComplaintList> {
  const params = new URLSearchParams();
  for (const [key, value] of Object.entries(filters)) {
    if (value !== undefined && value !== "") {
      params.set(key, String(value));
    }
  }
  const query = params.toString();
  const { data } = await request<ComplaintList>(`/complaints${query ? `?${query}` : ""}`);
  return data;
}

export async function updateComplaintStatus(id: string, status: Status): Promise<Complaint> {
  const { data } = await request<Complaint>(`/complaints/${id}/status`, {
    method: "PATCH",
    body: JSON.stringify({ status }),
  });
  return data;
}

export async function getStats(): Promise<StatsResult> {
  const { data, headers } = await request<Stats>("/stats");
  return { stats: data, cacheHit: headers.get("X-Cache") === "HIT" };
}

export async function getProvidersMeta(): Promise<ProvidersMeta> {
  const { data } = await request<ProvidersMeta>("/meta/providers");
  return data;
}