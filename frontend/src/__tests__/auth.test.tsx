/**
 * Auth Flow Tests — Sprint 212 Track A2a
 *
 * Tests the login page form rendering, validation, token storage,
 * and redirect behavior after successful login.
 *
 * @module frontend/src/__tests__/auth.test
 * @sprint 212
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";

// Mock next/navigation
const mockPush = vi.fn();
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: mockPush }),
  useSearchParams: () => new URLSearchParams(),
}));

// Mock next/link
vi.mock("next/link", () => ({
  default: ({ children, href }: { children: React.ReactNode; href: string }) => (
    <a href={href}>{children}</a>
  ),
}));

// Mock next-intl — return the key as the translation value
vi.mock("next-intl", () => ({
  useTranslations: () => (key: string) => key,
}));

// Mock landing components to keep tests focused on form logic
vi.mock("@/components/landing", () => ({
  Header: () => <div data-testid="header" />,
  Footer: () => <div data-testid="footer" />,
}));

// Mock API — controlled per test
const mockLogin = vi.fn();
const mockGetCurrentUser = vi.fn();
vi.mock("@/lib/api", () => ({
  login: (...args: unknown[]) => mockLogin(...args),
  getCurrentUser: (...args: unknown[]) => mockGetCurrentUser(...args),
  getOAuthAuthorizeUrl: vi.fn(),
  APIError: class APIError extends Error {
    status: number;
    detail: string;
    constructor(msg: string, status: number) {
      super(msg);
      this.status = status;
      this.detail = msg;
    }
  },
}));

import LoginPage from "@/app/login/page";

describe("LoginPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    (window.localStorage.setItem as ReturnType<typeof vi.fn>).mockClear();
  });

  it("renders email and password inputs", () => {
    render(<LoginPage />);

    const emailInput = screen.getByPlaceholderText("emailPlaceholder");
    const passwordInput = screen.getByPlaceholderText("passwordPlaceholder");

    expect(emailInput).toBeInTheDocument();
    expect(emailInput).toHaveAttribute("type", "email");
    expect(passwordInput).toBeInTheDocument();
    expect(passwordInput).toHaveAttribute("type", "password");
  });

  it("shows validation error when email is empty on submit", async () => {
    render(<LoginPage />);

    const submitButton = screen.getByRole("button", { name: "submit" });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText("validation.emailRequired")).toBeInTheDocument();
    });
    // login API should NOT have been called
    expect(mockLogin).not.toHaveBeenCalled();
  });

  it("stores tokens in localStorage on successful login", async () => {
    mockLogin.mockResolvedValueOnce({
      access_token: "test-access-token",
      refresh_token: "test-refresh-token",
    });
    mockGetCurrentUser.mockResolvedValueOnce({
      id: "user-1",
      email: "test@example.com",
      is_platform_admin: false,
    });

    render(<LoginPage />);

    fireEvent.change(screen.getByPlaceholderText("emailPlaceholder"), {
      target: { value: "test@example.com" },
    });
    fireEvent.change(screen.getByPlaceholderText("passwordPlaceholder"), {
      target: { value: "SecurePass123!" },
    });
    fireEvent.click(screen.getByRole("button", { name: "submit" }));

    await waitFor(() => {
      expect(window.localStorage.setItem).toHaveBeenCalledWith(
        "access_token",
        "test-access-token"
      );
      expect(window.localStorage.setItem).toHaveBeenCalledWith(
        "refresh_token",
        "test-refresh-token"
      );
    });
  });

  it("redirects to /app after successful login for regular user", async () => {
    mockLogin.mockResolvedValueOnce({
      access_token: "tok",
      refresh_token: "ref",
    });
    mockGetCurrentUser.mockResolvedValueOnce({
      id: "user-1",
      email: "user@example.com",
      is_platform_admin: false,
    });

    render(<LoginPage />);

    fireEvent.change(screen.getByPlaceholderText("emailPlaceholder"), {
      target: { value: "user@example.com" },
    });
    fireEvent.change(screen.getByPlaceholderText("passwordPlaceholder"), {
      target: { value: "SecurePass123!" },
    });
    fireEvent.click(screen.getByRole("button", { name: "submit" }));

    await waitFor(() => {
      expect(mockPush).toHaveBeenCalledWith("/app");
    });
  });
});
