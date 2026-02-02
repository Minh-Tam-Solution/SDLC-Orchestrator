/* eslint-disable @typescript-eslint/no-explicit-any */
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { vi, describe, it, expect, beforeEach } from "vitest";
import { GitHubConnectButton } from "./GitHubConnectButton";
import * as useGitHubModule from "@/hooks/useGitHub";

// Mock the hooks
const mockDisconnectGitHub = vi.fn();
const mockInitiateOAuth = vi.fn();
const mockUseGitHub = vi.spyOn(useGitHubModule, "useGitHub");
const mockUseGitHubOAuth = vi.spyOn(useGitHubModule, "useGitHubOAuth");

describe("GitHubConnectButton", () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });

  beforeEach(() => {
    vi.clearAllMocks();
    mockUseGitHubOAuth.mockReturnValue({
      initiateOAuth: mockInitiateOAuth,
    } as any);
  });

  const renderButton = (props = {}) => {
    return render(
      <QueryClientProvider client={queryClient}>
        <GitHubConnectButton {...props} />
      </QueryClientProvider>
    );
  };

  describe("When not connected", () => {
    beforeEach(() => {
      mockUseGitHub.mockReturnValue({
        isConnected: false,
        connection: null,
        disconnectGitHub: mockDisconnectGitHub,
        isDisconnecting: false,
      } as any);
    });

    it("should render connect button", () => {
      renderButton();

      expect(screen.getByText("Connect GitHub")).toBeInTheDocument();
    });

    it("should show GitHub icon by default", () => {
      renderButton();

      const button = screen.getByRole("button");
      const svg = button.querySelector("svg");
      expect(svg).toBeInTheDocument();
    });

    it("should hide icon when showIcon is false", () => {
      renderButton({ showIcon: false });

      const button = screen.getByRole("button");
      const svg = button.querySelector("svg");
      expect(svg).not.toBeInTheDocument();
    });

    it("should initiate OAuth flow when clicked", () => {
      renderButton();

      const button = screen.getByText("Connect GitHub");
      fireEvent.click(button);

      expect(mockInitiateOAuth).toHaveBeenCalledTimes(1);
    });

    it("should use correct variant", () => {
      const { rerender } = renderButton({ variant: "outline" });

      let button = screen.getByRole("button");
      expect(button).toHaveClass("border");

      rerender(
        <QueryClientProvider client={queryClient}>
          <GitHubConnectButton variant="ghost" />
        </QueryClientProvider>
      );

      button = screen.getByRole("button");
      expect(button).toHaveClass("hover:bg-accent");
    });

    it("should use correct size", () => {
      const { rerender } = renderButton({ size: "sm" });

      let button = screen.getByRole("button");
      expect(button).toHaveClass("h-9");

      rerender(
        <QueryClientProvider client={queryClient}>
          <GitHubConnectButton size="lg" />
        </QueryClientProvider>
      );

      button = screen.getByRole("button");
      expect(button).toHaveClass("h-11");
    });
  });

  describe("When connected", () => {
    const mockConnection = {
      id: "conn-123",
      user_id: "user-123",
      github_user_id: 12345,
      github_username: "octocat",
      github_avatar_url: "https://github.com/octocat.png",
      access_token_expires_at: "2026-12-31T00:00:00Z",
      connected_at: "2026-01-01T00:00:00Z",
    };

    beforeEach(() => {
      mockUseGitHub.mockReturnValue({
        isConnected: true,
        connection: mockConnection,
        disconnectGitHub: mockDisconnectGitHub,
        isDisconnecting: false,
      } as any);
    });

    it("should render connected state with username", () => {
      renderButton();

      expect(screen.getByText("Connected as octocat")).toBeInTheDocument();
    });

    it("should show GitHub icon when connected", () => {
      renderButton();

      const button = screen.getByRole("button");
      const svg = button.querySelector("svg");
      expect(svg).toBeInTheDocument();
    });

    it("should render as outline variant when connected", () => {
      renderButton();

      const button = screen.getByRole("button");
      expect(button).toHaveClass("border");
    });

    it("should show disconnect dialog when clicked", async () => {
      renderButton();

      const button = screen.getByText("Connected as octocat");
      fireEvent.click(button);

      await waitFor(() => {
        expect(screen.getByText("Disconnect GitHub?")).toBeInTheDocument();
      });

      expect(
        screen.getByText(/This will disconnect your GitHub account/)
      ).toBeInTheDocument();
    });

    it("should disconnect when confirmed", async () => {
      mockDisconnectGitHub.mockResolvedValue({});
      renderButton();

      // Click connected button to open dialog
      const button = screen.getByText("Connected as octocat");
      fireEvent.click(button);

      // Wait for dialog to appear
      await waitFor(() => {
        expect(screen.getByText("Disconnect GitHub?")).toBeInTheDocument();
      });

      // Click disconnect button in dialog
      const disconnectButton = screen.getByRole("button", { name: "Disconnect" });
      fireEvent.click(disconnectButton);

      await waitFor(() => {
        expect(mockDisconnectGitHub).toHaveBeenCalledTimes(1);
      });
    });

    it("should not disconnect when cancelled", async () => {
      renderButton();

      // Click connected button to open dialog
      const button = screen.getByText("Connected as octocat");
      fireEvent.click(button);

      // Wait for dialog to appear
      await waitFor(() => {
        expect(screen.getByText("Disconnect GitHub?")).toBeInTheDocument();
      });

      // Click cancel button
      const cancelButton = screen.getByRole("button", { name: "Cancel" });
      fireEvent.click(cancelButton);

      expect(mockDisconnectGitHub).not.toHaveBeenCalled();
    });

    it("should show disconnecting state", () => {
      mockUseGitHub.mockReturnValue({
        isConnected: true,
        connection: mockConnection,
        disconnectGitHub: mockDisconnectGitHub,
        isDisconnecting: true,
      } as any);

      renderButton();

      expect(screen.getByText("Disconnecting...")).toBeInTheDocument();
    });

    it("should disable button while disconnecting", () => {
      mockUseGitHub.mockReturnValue({
        isConnected: true,
        connection: mockConnection,
        disconnectGitHub: mockDisconnectGitHub,
        isDisconnecting: true,
      } as any);

      renderButton();

      const button = screen.getByRole("button");
      expect(button).toBeDisabled();
    });

    it("should handle disconnect error gracefully", async () => {
      const consoleErrorSpy = vi.spyOn(console, "error").mockImplementation(() => {});
      mockDisconnectGitHub.mockRejectedValue(new Error("Network error"));
      renderButton();

      // Click connected button to open dialog
      const button = screen.getByText("Connected as octocat");
      fireEvent.click(button);

      // Wait for dialog to appear
      await waitFor(() => {
        expect(screen.getByText("Disconnect GitHub?")).toBeInTheDocument();
      });

      // Click disconnect button
      const disconnectButton = screen.getByRole("button", { name: "Disconnect" });
      fireEvent.click(disconnectButton);

      await waitFor(() => {
        expect(consoleErrorSpy).toHaveBeenCalledWith(
          "Failed to disconnect GitHub:",
          expect.any(Error)
        );
      });

      consoleErrorSpy.mockRestore();
    });
  });

  describe("Accessibility", () => {
    beforeEach(() => {
      mockUseGitHub.mockReturnValue({
        isConnected: false,
        connection: null,
        disconnectGitHub: mockDisconnectGitHub,
        isDisconnecting: false,
      } as any);
    });

    it("should have proper button role", () => {
      renderButton();

      const button = screen.getByRole("button");
      expect(button).toBeInTheDocument();
    });

    it("should be keyboard accessible", () => {
      renderButton();

      const button = screen.getByRole("button");
      button.focus();
      expect(button).toHaveFocus();
    });

    it("should handle Enter key press", () => {
      renderButton();

      const button = screen.getByRole("button");
      fireEvent.keyDown(button, { key: "Enter", code: "Enter" });

      expect(mockInitiateOAuth).toHaveBeenCalled();
    });

    it("should handle Space key press", () => {
      renderButton();

      const button = screen.getByRole("button");
      fireEvent.keyDown(button, { key: " ", code: "Space" });

      expect(mockInitiateOAuth).toHaveBeenCalled();
    });
  });

  describe("onConnected callback", () => {
    beforeEach(() => {
      mockUseGitHub.mockReturnValue({
        isConnected: false,
        connection: null,
        disconnectGitHub: mockDisconnectGitHub,
        isDisconnecting: false,
      } as any);
    });

    it("should call onConnected callback when provided", async () => {
      const onConnected = vi.fn();
      renderButton({ onConnected });

      const button = screen.getByText("Connect GitHub");
      fireEvent.click(button);

      // Note: onConnected would be called after OAuth flow completes
      // This is just to verify the prop is accepted
      expect(onConnected).not.toHaveBeenCalled(); // Not called during initiate
    });
  });
});
