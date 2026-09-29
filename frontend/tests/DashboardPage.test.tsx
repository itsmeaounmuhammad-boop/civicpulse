import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi } from "vitest";

import { ApiError, listComplaints, updateComplaintStatus } from "../src/api/client";
import type { Complaint, ComplaintList } from "../src/api/types";
import { DashboardPage } from "../src/pages/DashboardPage";

vi.mock("../src/api/client", async () => {
  const actual = await vi.importActual<typeof import("../src/api/client")>("../src/api/client");
  return { ...actual, listComplaints: vi.fn(), updateComplaintStatus: vi.fn() };
});

const mockedList = vi.mocked(listComplaints);
const mockedUpdate = vi.mocked(updateComplaintStatus);

const complaint: Complaint = {
  id: "abc-123",
  text: "Streetlight not working",
  location: "Sector G-10",
  reporter_contact: null,
  category: "streetlights",
  priority: "low",
  status: "resolved",
  ai_summary: "Streetlight out in G-10",
  triaged_by: "rules",
  triage_latency_ms: 3,
  created_at: "2026-01-01T00:00:00Z",
  updated_at: "2026-01-01T00:00:00Z",
};

const page: ComplaintList = { items: [complaint], total: 25, page: 1, page_size: 10 };

describe("DashboardPage", () => {
  beforeEach(() => {
    mockedList.mockReset();
    mockedUpdate.mockReset();
    mockedList.mockResolvedValue(page);
  });

  it("lists complaints and shows pagination info", async () => {
    render(<DashboardPage />);

    expect(await screen.findByText("Streetlight out in G-10")).toBeInTheDocument();
    expect(screen.getByText(/Page 1 of 3 · 25 total/)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Previous" })).toBeDisabled();
  });

  it("requests the next page", async () => {
    render(<DashboardPage />);
    await screen.findByText("Streetlight out in G-10");
    await userEvent.click(screen.getByRole("button", { name: "Next" }));

    expect(mockedList).toHaveBeenLastCalledWith(expect.objectContaining({ page: 2 }));
  });

  it("applies the category filter", async () => {
    render(<DashboardPage />);
    await screen.findByText("Streetlight out in G-10");
    await userEvent.selectOptions(screen.getByLabelText("Category"), "water");

    expect(mockedList).toHaveBeenLastCalledWith(
      expect.objectContaining({ category: "water", page: 1 }),
    );
  });

  it("shows the server 409 message verbatim", async () => {
    const message = "Invalid transition: resolved -> open";
    mockedUpdate.mockRejectedValue(new ApiError(409, message));
    render(<DashboardPage />);
    await screen.findByText("Streetlight out in G-10");
    await userEvent.selectOptions(
      screen.getByLabelText("Change status of complaint abc-123"),
      "open",
    );

    expect(await screen.findByRole("alert")).toHaveTextContent(message);
  });
});