import { render, screen } from "@testing-library/react";

import { Badge } from "../src/components/Badge";

describe("Badge", () => {
  it("replaces underscores with spaces", () => {
    render(<Badge value="in_progress" />);
    expect(screen.getByText("in progress")).toBeInTheDocument();
  });

  it("adds a class based on the value", () => {
    render(<Badge value="high" />);
    expect(screen.getByText("high")).toHaveClass("badge-high");
  });
});