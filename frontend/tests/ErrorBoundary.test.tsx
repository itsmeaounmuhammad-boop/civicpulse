import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi } from "vitest";

import { ErrorBoundary } from "../src/components/ErrorBoundary";

let shouldThrow = true;

function Broken() {
  if (shouldThrow) throw new Error("boom");
  return <p>recovered</p>;
}

describe("ErrorBoundary", () => {
  it("shows the error message and recovers on retry", async () => {
    vi.spyOn(console, "error").mockImplementation(() => {});
    shouldThrow = true;

    render(
      <ErrorBoundary>
        <Broken />
      </ErrorBoundary>,
    );

    expect(screen.getByRole("alert")).toHaveTextContent("boom");

    shouldThrow = false;
    await userEvent.click(screen.getByRole("button", { name: "Try again" }));
    expect(screen.getByText("recovered")).toBeInTheDocument();
  });
});