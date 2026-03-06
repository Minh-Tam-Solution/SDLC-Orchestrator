/**
 * NotificationCenter Tests — Sprint 212 Track A2
 *
 * Tests notification list rendering, empty state,
 * mark-as-read interaction, and unread count badge.
 *
 * @module frontend/src/__tests__/components/NotificationCenter.test
 * @sprint 212
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import React from "react";

// Mock @tanstack/react-query
const mockMutate = vi.fn();
const mockQueryData = vi.fn();
vi.mock("@tanstack/react-query", () => ({
  useQuery: ({ queryFn }: { queryFn?: () => unknown }) => mockQueryData(),
  useMutation: () => ({
    mutate: mockMutate,
    isPending: false,
  }),
  useQueryClient: () => ({
    invalidateQueries: vi.fn(),
  }),
}));

// Mock date-fns
vi.mock("date-fns", () => ({
  formatDistanceToNow: () => "5 minutes ago",
}));

// Mock lucide-react icons as simple spans
vi.mock("lucide-react", () => ({
  Bell: ({ className }: { className?: string }) => <span data-testid="bell-icon" className={className} />,
  Check: ({ className }: { className?: string }) => <span className={className} />,
  CheckCheck: ({ className }: { className?: string }) => <span className={className} />,
  AlertTriangle: ({ className }: { className?: string }) => <span className={className} />,
  Shield: ({ className }: { className?: string }) => <span className={className} />,
  FileCheck: ({ className }: { className?: string }) => <span className={className} />,
  Users: ({ className }: { className?: string }) => <span className={className} />,
  GitPullRequest: ({ className }: { className?: string }) => <span className={className} />,
  X: ({ className }: { className?: string }) => <span className={className} />,
}));

// Mock shadcn/ui components with minimal structure
vi.mock("@/components/ui/button", () => ({
  Button: ({ children, ...props }: React.PropsWithChildren<Record<string, unknown>>) => (
    <button {...props}>{children}</button>
  ),
}));

vi.mock("@/components/ui/popover", () => ({
  Popover: ({ children, open }: { children: React.ReactNode; open?: boolean }) => (
    <div data-testid="popover" data-open={open}>{children}</div>
  ),
  PopoverTrigger: ({ children }: { children: React.ReactNode }) => <div data-testid="popover-trigger">{children}</div>,
  PopoverContent: ({ children }: { children: React.ReactNode }) => <div data-testid="popover-content">{children}</div>,
}));

vi.mock("@/components/ui/scroll-area", () => ({
  ScrollArea: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}));

vi.mock("@/components/ui/badge", () => ({
  Badge: ({ children, ...props }: React.PropsWithChildren<Record<string, unknown>>) => (
    <span data-testid="unread-badge" {...props}>{children}</span>
  ),
}));

vi.mock("@/components/ui/separator", () => ({
  Separator: () => <hr />,
}));

vi.mock("@/lib/utils", () => ({
  cn: (...args: unknown[]) => args.filter(Boolean).join(" "),
}));

vi.mock("@/lib/api", () => ({
  api: {
    get: vi.fn(),
    put: vi.fn(),
  },
}));

vi.mock("@/hooks/useWebSocket", () => ({
  useWebSocket: () => ({ unreadCount: 0 }),
  WebSocketEventType: {
    GATE_APPROVED: "gate_approved",
    GATE_REJECTED: "gate_rejected",
    POLICY_VIOLATION: "policy_violation",
    NOTIFICATION_CREATED: "notification_created",
  },
}));

vi.mock("@/components/ui/use-toast", () => ({
  useToast: () => ({ toast: vi.fn() }),
}));

import { NotificationCenter } from "@/components/notifications/NotificationCenter";

const sampleNotifications = [
  {
    id: "n1",
    notification_type: "gate_approved",
    title: "Gate G1 Approved",
    message: "Gate G1 for Project Alpha has been approved",
    priority: "high" as const,
    is_read: false,
    created_at: "2026-02-28T10:00:00Z",
  },
  {
    id: "n2",
    notification_type: "evidence_uploaded",
    title: "Evidence Uploaded",
    message: "New test results uploaded for Project Beta",
    priority: "medium" as const,
    is_read: true,
    created_at: "2026-02-28T09:00:00Z",
  },
];

describe("NotificationCenter", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders notification list when data is available", () => {
    mockQueryData.mockReturnValue({
      data: {
        notifications: sampleNotifications,
        total: 2,
        unread_count: 1,
        page: 1,
        page_size: 20,
      },
      isLoading: false,
      refetch: vi.fn(),
    });

    render(<NotificationCenter />);

    expect(screen.getByText("Gate G1 Approved")).toBeInTheDocument();
    expect(screen.getByText("Evidence Uploaded")).toBeInTheDocument();
    expect(screen.getByText("Notifications")).toBeInTheDocument();
  });

  it("shows unread count badge when there are unread notifications", () => {
    mockQueryData.mockReturnValue({
      data: {
        notifications: sampleNotifications,
        total: 2,
        unread_count: 3,
        page: 1,
        page_size: 20,
      },
      isLoading: false,
      refetch: vi.fn(),
    });

    render(<NotificationCenter />);

    const badge = screen.getByTestId("unread-badge");
    expect(badge).toBeInTheDocument();
    expect(badge.textContent).toBe("3");
  });

  it("shows empty state message when no notifications", () => {
    mockQueryData.mockReturnValue({
      data: {
        notifications: [],
        total: 0,
        unread_count: 0,
        page: 1,
        page_size: 20,
      },
      isLoading: false,
      refetch: vi.fn(),
    });

    render(<NotificationCenter />);

    expect(screen.getByText("No notifications yet")).toBeInTheDocument();
  });

  it("shows Mark all read button when there are unread notifications", () => {
    mockQueryData.mockReturnValue({
      data: {
        notifications: sampleNotifications,
        total: 2,
        unread_count: 1,
        page: 1,
        page_size: 20,
      },
      isLoading: false,
      refetch: vi.fn(),
    });

    render(<NotificationCenter />);

    expect(screen.getByText("Mark all read")).toBeInTheDocument();
  });

  it("calls markAll mutation when Mark all read is clicked", () => {
    mockQueryData.mockReturnValue({
      data: {
        notifications: sampleNotifications,
        total: 2,
        unread_count: 1,
        page: 1,
        page_size: 20,
      },
      isLoading: false,
      refetch: vi.fn(),
    });

    render(<NotificationCenter />);

    fireEvent.click(screen.getByText("Mark all read"));
    expect(mockMutate).toHaveBeenCalled();
  });
});
