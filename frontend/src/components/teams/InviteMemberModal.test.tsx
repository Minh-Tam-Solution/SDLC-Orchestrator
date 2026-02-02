/* eslint-disable @typescript-eslint/no-explicit-any */
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { vi, describe, it, expect, beforeEach } from "vitest";
import { InviteMemberModal } from "./InviteMemberModal";
import * as useInvitationsModule from "@/hooks/useInvitations";

// Mock the useInvitations hook
const mockSendInvitation = vi.fn();
const mockUseInvitations = vi.spyOn(useInvitationsModule, "useInvitations");

describe("InviteMemberModal", () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });

  const defaultProps = {
    isOpen: true,
    onClose: vi.fn(),
    teamId: "team-123",
    teamName: "Engineering Team",
  };

  beforeEach(() => {
    vi.clearAllMocks();
    mockUseInvitations.mockReturnValue({
      sendInvitation: mockSendInvitation,
      isSending: false,
    } as any);
  });

  const renderModal = (props = {}) => {
    return render(
      <QueryClientProvider client={queryClient}>
        <InviteMemberModal {...defaultProps} {...props} />
      </QueryClientProvider>
    );
  };

  it("should render modal when open", () => {
    renderModal();

    expect(screen.getByText("Invite Member to Engineering Team")).toBeInTheDocument();
    expect(
      screen.getByText(/Send an invitation email to add a new member/)
    ).toBeInTheDocument();
  });

  it("should not render modal when closed", () => {
    renderModal({ isOpen: false });

    expect(
      screen.queryByText("Invite Member to Engineering Team")
    ).not.toBeInTheDocument();
  });

  it("should have email input field", () => {
    renderModal();

    const emailInput = screen.getByLabelText("Email Address");
    expect(emailInput).toBeInTheDocument();
    expect(emailInput).toHaveAttribute("type", "email");
    expect(emailInput).toHaveAttribute("placeholder", "colleague@company.com");
  });

  it("should have role selection dropdown", () => {
    renderModal();

    expect(screen.getByLabelText("Role")).toBeInTheDocument();
  });

  it("should default to member role", () => {
    renderModal();

    expect(
      screen.getByText("Access team projects and contribute")
    ).toBeInTheDocument();
  });

  it("should validate email format", async () => {
    renderModal();

    const emailInput = screen.getByLabelText("Email Address");
    const submitButton = screen.getByText("Send Invitation");

    // Enter invalid email
    fireEvent.change(emailInput, { target: { value: "invalid-email" } });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(
        screen.getByText("Please enter a valid email address")
      ).toBeInTheDocument();
    });

    expect(mockSendInvitation).not.toHaveBeenCalled();
  });

  it("should send invitation with valid data", async () => {
    mockSendInvitation.mockResolvedValue({ success: true });
    renderModal();

    const emailInput = screen.getByLabelText("Email Address");
    const submitButton = screen.getByText("Send Invitation");

    // Enter valid email
    fireEvent.change(emailInput, { target: { value: "test@example.com" } });

    // Submit form
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(mockSendInvitation).toHaveBeenCalledWith({
        email: "test@example.com",
        role: "member",
      });
    });

    // Modal should close on success
    expect(defaultProps.onClose).toHaveBeenCalled();
  });

  it("should trim and lowercase email", async () => {
    mockSendInvitation.mockResolvedValue({ success: true });
    renderModal();

    const emailInput = screen.getByLabelText("Email Address");
    const submitButton = screen.getByText("Send Invitation");

    // Enter email with spaces and uppercase
    fireEvent.change(emailInput, { target: { value: "  Test@Example.COM  " } });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(mockSendInvitation).toHaveBeenCalledWith({
        email: "test@example.com",
        role: "member",
      });
    });
  });

  it("should handle role selection", async () => {
    mockSendInvitation.mockResolvedValue({ success: true });
    renderModal();

    const emailInput = screen.getByLabelText("Email Address");
    const roleSelect = screen.getByLabelText("Role");

    // Enter email
    fireEvent.change(emailInput, { target: { value: "admin@example.com" } });

    // Open role dropdown (this is a simplified version, actual implementation may differ)
    fireEvent.click(roleSelect);

    // Select admin role
    const adminOption = screen.getByText("Admin");
    fireEvent.click(adminOption);

    // Submit form
    const submitButton = screen.getByText("Send Invitation");
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(mockSendInvitation).toHaveBeenCalledWith({
        email: "admin@example.com",
        role: "admin",
      });
    });
  });

  it("should display error for already existing member", async () => {
    const error = {
      response: {
        status: 400,
        data: { detail: "User already a member of this team" },
      },
    };
    mockSendInvitation.mockRejectedValue(error);
    renderModal();

    const emailInput = screen.getByLabelText("Email Address");
    const submitButton = screen.getByText("Send Invitation");

    fireEvent.change(emailInput, { target: { value: "existing@example.com" } });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(
        screen.getByText(/existing@example.com is already a member/)
      ).toBeInTheDocument();
    });
  });

  it("should display error for pending invitation", async () => {
    const error = {
      response: {
        status: 400,
        data: { detail: "A pending invitation already exists" },
      },
    };
    mockSendInvitation.mockRejectedValue(error);
    renderModal();

    const emailInput = screen.getByLabelText("Email Address");
    const submitButton = screen.getByText("Send Invitation");

    fireEvent.change(emailInput, { target: { value: "pending@example.com" } });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(
        screen.getByText(/An invitation has already been sent/)
      ).toBeInTheDocument();
    });
  });

  it("should display rate limit error", async () => {
    const error = {
      response: {
        status: 429,
        data: { detail: "Rate limit exceeded" },
      },
    };
    mockSendInvitation.mockRejectedValue(error);
    renderModal();

    const emailInput = screen.getByLabelText("Email Address");
    const submitButton = screen.getByText("Send Invitation");

    fireEvent.change(emailInput, { target: { value: "test@example.com" } });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(
        screen.getByText(/Rate limit exceeded. Please try again in a few minutes./)
      ).toBeInTheDocument();
    });
  });

  it("should display generic error for unknown errors", async () => {
    const error = {
      response: {
        status: 500,
        data: { detail: "Internal server error" },
      },
    };
    mockSendInvitation.mockRejectedValue(error);
    renderModal();

    const emailInput = screen.getByLabelText("Email Address");
    const submitButton = screen.getByText("Send Invitation");

    fireEvent.change(emailInput, { target: { value: "test@example.com" } });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(
        screen.getByText(/Failed to send invitation. Please try again./)
      ).toBeInTheDocument();
    });
  });

  it("should disable inputs while sending", () => {
    mockUseInvitations.mockReturnValue({
      sendInvitation: mockSendInvitation,
      isSending: true,
    } as any);

    renderModal();

    const emailInput = screen.getByLabelText("Email Address");
    const submitButton = screen.getByText("Sending...");

    expect(emailInput).toBeDisabled();
    expect(submitButton).toBeDisabled();
  });

  it("should show loading spinner while sending", () => {
    mockUseInvitations.mockReturnValue({
      sendInvitation: mockSendInvitation,
      isSending: true,
    } as any);

    renderModal();

    expect(screen.getByText("Sending...")).toBeInTheDocument();
  });

  it("should reset form when closing modal", () => {
    renderModal();

    const emailInput = screen.getByLabelText("Email Address") as HTMLInputElement;
    const cancelButton = screen.getByText("Cancel");

    // Enter data
    fireEvent.change(emailInput, { target: { value: "test@example.com" } });

    // Close modal
    fireEvent.click(cancelButton);

    // Reopen modal
    renderModal({ isOpen: false });
    renderModal({ isOpen: true });

    // Form should be reset
    expect(emailInput.value).toBe("");
  });

  it("should display all role descriptions", () => {
    renderModal();

    // Owner description
    expect(
      screen.getByText("Full access including team deletion and billing")
    ).toBeInTheDocument();

    // Admin description
    expect(
      screen.getByText("Manage team members, projects, and settings")
    ).toBeInTheDocument();

    // Member description
    expect(
      screen.getByText("Access team projects and contribute")
    ).toBeInTheDocument();

    // Viewer description
    expect(
      screen.getByText("Read-only access to team projects")
    ).toBeInTheDocument();
  });

  it("should have cancel button", () => {
    renderModal();

    const cancelButton = screen.getByText("Cancel");
    expect(cancelButton).toBeInTheDocument();

    fireEvent.click(cancelButton);
    expect(defaultProps.onClose).toHaveBeenCalled();
  });

  it("should clear error when modal is closed and reopened", async () => {
    const error = {
      response: {
        status: 400,
        data: { detail: "Some error" },
      },
    };
    mockSendInvitation.mockRejectedValue(error);
    const { rerender } = renderModal();

    const emailInput = screen.getByLabelText("Email Address");
    const submitButton = screen.getByText("Send Invitation");

    // Trigger error
    fireEvent.change(emailInput, { target: { value: "test@example.com" } });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText(/Some error/)).toBeInTheDocument();
    });

    // Close modal
    rerender(
      <QueryClientProvider client={queryClient}>
        <InviteMemberModal {...defaultProps} isOpen={false} />
      </QueryClientProvider>
    );

    // Reopen modal
    rerender(
      <QueryClientProvider client={queryClient}>
        <InviteMemberModal {...defaultProps} isOpen={true} />
      </QueryClientProvider>
    );

    // Error should be cleared
    expect(screen.queryByText(/Some error/)).not.toBeInTheDocument();
  });
});
