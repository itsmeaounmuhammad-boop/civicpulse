import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi } from "vitest";

import { ApiError, createComplaint } from "../src/api/client";
import type { Complaint } from "../src/api/types";
import { SubmitPage } from "../src/pages/SubmitPage";

vi.mock("../src/api/client", async () => {
  const actual = await vi.importActual<typeof import("../src/api/client")>("../src/api/client");
  return { ...actual, createComplaint: vi.fn() };
});

const mockedCreate = vi.mocked(createComplaint);

const complaint: Complaint = {
  id: "abc-123",
  text: "Burst water main flooding Street 12",
  location: "Street 12",
  reporter_contact: null,
  category: "water",
  priority: "high",
  status: "open",
  ai_summary: "Burst water main on Street 12",
  triaged_by: "rules",
  triage_latency_ms: 4,
  created_at: "2026-01-01T00:00:00Z",
  updated_at: "2026-01-01T00:00:00Z",
};

async function fillForm(text: string, location: string) {
  await userEvent.type(screen.getByLabelText(/what is the problem/i), text);
  await userEvent.type(screen.getByLabelText(/^location/i), location);
}

describe("SubmitPage", () => {
  beforeEach(() => {
    mockedCreate.mockReset();
  });

  it("shows validation errors and does not call the API", async () => {
    render(<SubmitPage />);
    await fillForm("short", "ab");
    await userEvent.click(screen.getByRole("button", { name: "Submit complaint" }));

    expect(screen.getByText(/description must be 10/i)).toBeInTheDocument();
    expect(screen.getByText(/location must be 3/i)).toBeInTheDocument();
    expect(mockedCreate).not.toHaveBeenCalled();
  });

  it("renders category, priority, summary and provider after success", async () => {
    mockedCreate.mockResolvedValue(complaint);
    render(<SubmitPage />);
    await fillForm("Burst water main flooding Street 12", "Street 12");
    await userEvent.click(screen.getByRole("button", { name: "Submit complaint" }));

    expect(await screen.findByText("Complaint received")).toBeInTheDocument();
    expect(screen.getByText("Burst water main on Street 12")).toBeInTheDocument();
    expect(screen.getByText("water")).toBeInTheDocument();
    expect(screen.getByText("high")).toBeInTheDocument();
    expect(screen.getByText("rules")).toBeInTheDocument();
  });

  it("shows the retry time when rate limited", async () => {
    mockedCreate.mockRejectedValue(new ApiError(429, "Rate limit exceeded", [], 30));
    render(<SubmitPage />);
    await fillForm("Burst water main flooding Street 12", "Street 12");
    await userEvent.click(screen.getByRole("button", { name: "Submit complaint" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("Try again in 30s");
  });
});