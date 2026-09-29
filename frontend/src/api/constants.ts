import type { Category, Priority, Status } from "./types";

// Enum *values* only (used to populate dropdowns and order charts).
// Deliberately NO transition rules here: which status moves are legal is
// decided by the backend state machine and surfaced via its 409 message.
export const CATEGORIES: Category[] = [
  "water",
  "electricity",
  "sanitation",
  "roads",
  "streetlights",
  "other",
];

export const PRIORITIES: Priority[] = ["high", "normal", "low"];

export const STATUSES: Status[] = ["open", "in_progress", "resolved", "rejected"];

export const humanize = (value: string): string => value.replace(/_/g, " ");