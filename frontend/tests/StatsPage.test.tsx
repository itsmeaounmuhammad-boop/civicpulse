import { render, screen } from "@testing-library/react";
import { vi } from "vitest";

import { getStats } from "../src/api/client";
import { StatsPage } from "../src/pages/StatsPage";

vi.mock("../src/api/client", async () => {
  const actual = await vi.importActual<typeof import("../src/api/client")>("../src/api/client");
  return { ...actual, getStats: vi.fn() };
});

const mockedStats = vi.mocked(getStats);

const stats = {
  total: 7,
  by_category: { water: 4, roads: 3 },
  by_priority: { high: 2, normal: 5 },
};

describe("StatsPage", () => {
  it("shows X-Cache HIT", async () => {
    mockedStats.mockResolvedValue({ stats, cacheHit: true });
    render(<StatsPage />);

    expect(await screen.findByTestId("cache-status")).toHaveTextContent("X-Cache: HIT");
    expect(screen.getByText("7")).toBeInTheDocument();
  });

  it("shows X-Cache MISS", async () => {
    mockedStats.mockResolvedValue({ stats, cacheHit: false });
    render(<StatsPage />);

    expect(await screen.findByTestId("cache-status")).toHaveTextContent("X-Cache: MISS");
  });

  it("shows an error when the request fails", async () => {
    mockedStats.mockRejectedValue(new Error("network"));
    render(<StatsPage />);

    expect(await screen.findByRole("alert")).toHaveTextContent("Could not reach the server.");
  });
});
