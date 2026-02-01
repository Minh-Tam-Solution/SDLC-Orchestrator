"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { useInvitations } from "@/hooks/useInvitations";

interface InviteMemberModalProps {
  isOpen: boolean;
  onClose: () => void;
  teamId: string;
  teamName: string;
}

type TeamRole = "owner" | "admin" | "member" | "viewer";

const ROLE_DESCRIPTIONS: Record<TeamRole, string> = {
  owner: "Full access including team deletion and billing",
  admin: "Manage team members, projects, and settings",
  member: "Access team projects and contribute",
  viewer: "Read-only access to team projects",
};

export function InviteMemberModal({
  isOpen,
  onClose,
  teamId,
  teamName,
}: InviteMemberModalProps) {
  const [email, setEmail] = useState("");
  const [role, setRole] = useState<TeamRole>("member");
  const [error, setError] = useState<string | null>(null);
  const { sendInvitation, isSending } = useInvitations(teamId);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    // Email validation
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!email || !emailRegex.test(email)) {
      setError("Please enter a valid email address");
      return;
    }

    try {
      await sendInvitation({
        email: email.trim().toLowerCase(),
        role,
      });

      // Success - close modal and reset form
      setEmail("");
      setRole("member");
      onClose();
    } catch (err: any) {
      // Handle specific error cases
      if (err.response?.status === 400) {
        const detail = err.response?.data?.detail;
        if (detail?.includes("already a member")) {
          setError(`${email} is already a member of ${teamName}`);
        } else if (detail?.includes("pending invitation")) {
          setError(`An invitation has already been sent to ${email}`);
        } else {
          setError(detail || "Failed to send invitation");
        }
      } else if (err.response?.status === 429) {
        setError("Rate limit exceeded. Please try again in a few minutes.");
      } else {
        setError("Failed to send invitation. Please try again.");
      }
    }
  };

  const handleClose = () => {
    setEmail("");
    setRole("member");
    setError(null);
    onClose();
  };

  return (
    <Dialog open={isOpen} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>Invite Member to {teamName}</DialogTitle>
          <DialogDescription>
            Send an invitation email to add a new member to your team. They'll
            receive a link to accept the invitation.
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit}>
          <div className="grid gap-4 py-4">
            {/* Email Input */}
            <div className="grid gap-2">
              <Label htmlFor="email">Email Address</Label>
              <Input
                id="email"
                type="email"
                placeholder="colleague@company.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                disabled={isSending}
                autoFocus
                required
              />
            </div>

            {/* Role Selection */}
            <div className="grid gap-2">
              <Label htmlFor="role">Role</Label>
              <Select
                value={role}
                onValueChange={(value) => setRole(value as TeamRole)}
                disabled={isSending}
              >
                <SelectTrigger id="role">
                  <SelectValue placeholder="Select a role" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="owner">
                    <div className="flex flex-col items-start">
                      <div className="font-medium">Owner</div>
                      <div className="text-xs text-muted-foreground">
                        {ROLE_DESCRIPTIONS.owner}
                      </div>
                    </div>
                  </SelectItem>
                  <SelectItem value="admin">
                    <div className="flex flex-col items-start">
                      <div className="font-medium">Admin</div>
                      <div className="text-xs text-muted-foreground">
                        {ROLE_DESCRIPTIONS.admin}
                      </div>
                    </div>
                  </SelectItem>
                  <SelectItem value="member">
                    <div className="flex flex-col items-start">
                      <div className="font-medium">Member</div>
                      <div className="text-xs text-muted-foreground">
                        {ROLE_DESCRIPTIONS.member}
                      </div>
                    </div>
                  </SelectItem>
                  <SelectItem value="viewer">
                    <div className="flex flex-col items-start">
                      <div className="font-medium">Viewer</div>
                      <div className="text-xs text-muted-foreground">
                        {ROLE_DESCRIPTIONS.viewer}
                      </div>
                    </div>
                  </SelectItem>
                </SelectContent>
              </Select>
              <p className="text-sm text-muted-foreground">
                {ROLE_DESCRIPTIONS[role]}
              </p>
            </div>

            {/* Error Alert */}
            {error && (
              <Alert variant="destructive">
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}
          </div>

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={handleClose}
              disabled={isSending}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={isSending}>
              {isSending ? (
                <>
                  <svg
                    className="mr-2 h-4 w-4 animate-spin"
                    xmlns="http://www.w3.org/2000/svg"
                    fill="none"
                    viewBox="0 0 24 24"
                  >
                    <circle
                      className="opacity-25"
                      cx="12"
                      cy="12"
                      r="10"
                      stroke="currentColor"
                      strokeWidth="4"
                    />
                    <path
                      className="opacity-75"
                      fill="currentColor"
                      d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                    />
                  </svg>
                  Sending...
                </>
              ) : (
                "Send Invitation"
              )}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
