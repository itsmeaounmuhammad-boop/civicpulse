export type Category =
  | "water"
  | "electricity"
  | "sanitation"
  | "roads"
  | "streetlights"
  | "other";

export type Priority = "high" | "normal" | "low";

export type Status = "open" | "in_progress" | "resolved" | "rejected";

export interface Complaint {
  id: string;
  text: string;
  location: string;
  reporter_contact: string | null;
  category: Category;
  priority: Priority;
  status: Status;
  ai_summary: string | null;
  triaged_by: string;
  triage_latency_ms: number;
  created_at: string;
  updated_at: string;
}

export interface ComplaintCreate {
  text: string;
  location: string;
  reporter_contact?: string | null;
}

export interface ComplaintList {
  items: Complaint[];
  total: number;
  page: number;
  page_size: number;
}

export interface ComplaintFilters {
  category?: Category;
  priority?: Priority;
  status?: Status;
  page?: number;
  page_size?: number;
}

export interface Stats {
  by_category: Record<string, number>;
  by_priority: Record<string, number>;
  total: number;
}

export interface StatsResult {
  stats: Stats;
  cacheHit: boolean;
}

export interface TriageOutcome {
  provider: string;
  latency_ms: number;
  fallback: boolean;
  timestamp: string;
}

export interface ProvidersMeta {
  active_provider: string;
  recent_outcomes: TriageOutcome[];
}

export interface FieldError {
  field: string;
  message: string;
}