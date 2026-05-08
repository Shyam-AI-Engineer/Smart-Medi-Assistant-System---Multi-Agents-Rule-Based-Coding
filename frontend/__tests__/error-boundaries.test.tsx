import React from "react";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { ErrorBoundaryFallback } from "@/components/error/ErrorBoundaryFallback";

describe("Error Boundaries", () => {
  it("displays error fallback UI with error message", () => {
    const mockReset = jest.fn();
    const testError = new Error("Test error message");

    render(
      <ErrorBoundaryFallback
        error={testError}
        reset={mockReset}
        title="Test Error"
        description="This is a test error"
        showDetails={true}
      />
    );

    expect(screen.getByText("Test Error")).toBeInTheDocument();
    expect(screen.getByText("This is a test error")).toBeInTheDocument();
    expect(screen.getByText(/Test error message/)).toBeInTheDocument();
  });

  it("calls reset function when Try Again button is clicked", async () => {
    const mockReset = jest.fn();
    const testError = new Error("Test error");
    const user = userEvent.setup();

    render(
      <ErrorBoundaryFallback
        error={testError}
        reset={mockReset}
        showDetails={false}
      />
    );

    const tryAgainButton = screen.getByRole("button", { name: /Try Again/i });
    await user.click(tryAgainButton);

    expect(mockReset).toHaveBeenCalled();
  });

  it("navigates to home when Home button is clicked", async () => {
    const mockReset = jest.fn();
    const testError = new Error("Test error");
    const user = userEvent.setup();

    // Mock window.location.href
    delete (window as any).location;
    window.location = { href: "" } as any;

    render(
      <ErrorBoundaryFallback
        error={testError}
        reset={mockReset}
        showDetails={false}
      />
    );

    const homeButton = screen.getByRole("button", { name: /Home/i });
    await user.click(homeButton);

    expect(window.location.href).toBe("/");
  });

  it("hides error details when showDetails is false", () => {
    const mockReset = jest.fn();
    const testError = new Error("Sensitive error details");

    render(
      <ErrorBoundaryFallback
        error={testError}
        reset={mockReset}
        showDetails={false}
      />
    );

    expect(
      screen.queryByText(/Sensitive error details/)
    ).not.toBeInTheDocument();
  });

  it("shows error ID digest when available", () => {
    const mockReset = jest.fn();
    const testError = new Error("Test error");
    testError.digest = "abc123xyz";

    render(
      <ErrorBoundaryFallback
        error={testError}
        reset={mockReset}
        showDetails={true}
      />
    );

    expect(screen.getByText(/Error ID: abc123xyz/)).toBeInTheDocument();
  });
});
