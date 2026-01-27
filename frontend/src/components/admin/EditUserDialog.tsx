"use client";

/**
 * Edit User Dialog - Next.js App Router
 * @status Sprint 68 - Admin Section Migration
 * @description Dialog for editing existing users
 */

import { useState, useEffect } from "react";
import { Copy, Check } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Checkbox } from "@/components/ui/checkbox";
import { useUpdateAdminUserFull } from "@/hooks/useAdmin";
import { useToast } from "@/hooks/useToast";
import type { AdminUser } from "@/lib/types/admin";

interface EditUserDialogProps {
  user: AdminUser | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function EditUserDialog({ user, open, onOpenChange }: EditUserDialogProps) {
  const { toast } = useToast();
  const updateUserMutation = useUpdateAdminUserFull();

  const [formData, setFormData] = useState({
    email: "",
    name: "",
    new_password: "",
    is_active: true,
    is_superuser: false,
  });

  const [errors, setErrors] = useState<Record<string, string>>({});
  const [copied, setCopied] = useState(false);

  const handleCopyUUID = async () => {
    if (user?.id) {
      await navigator.clipboard.writeText(user.id);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  useEffect(() => {
    if (user && open) {
      setFormData({
        email: user.email,
        name: user.name || "",
        new_password: "",
        is_active: user.is_active,
        is_superuser: user.is_superuser,
      });
      setErrors({});
      setCopied(false);
    }
  }, [user, open]);

  const validateForm = () => {
    const newErrors: Record<string, string> = {};

    if (!formData.email) {
      newErrors.email = "Email is required";
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      newErrors.email = "Invalid email format";
    }

    if (formData.new_password && formData.new_password.length < 8) {
      newErrors.new_password = "Password must be at least 8 characters";
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!user || !validateForm() || updateUserMutation.isPending) {
      return;
    }

    try {
      const updatePayload: Record<string, unknown> = {};

      if (formData.email !== user.email) {
        updatePayload.email = formData.email;
      }
      if (formData.name !== user.name) {
        updatePayload.name = formData.name;
      }
      if (formData.new_password) {
        updatePayload.new_password = formData.new_password;
      }
      if (formData.is_active !== user.is_active) {
        updatePayload.is_active = formData.is_active;
      }
      if (formData.is_superuser !== user.is_superuser) {
        updatePayload.is_superuser = formData.is_superuser;
      }

      await updateUserMutation.mutateAsync({
        userId: user.id,
        data: updatePayload,
      });

      toast({
        title: "User Updated",
        description: `User ${formData.email} has been updated successfully`,
      });

      onOpenChange(false);
    } catch (error: unknown) {
      const message = error instanceof Error ? error.message : "Failed to update user";
      toast({
        title: "Error",
        description: message,
        variant: "destructive",
      });
    }
  };

  const handleChange = (field: string, value: string | boolean) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
    if (errors[field]) {
      setErrors((prev) => {
        const newErrors = { ...prev };
        delete newErrors[field];
        return newErrors;
      });
    }
  };

  if (!user) return null;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[500px]">
        <form onSubmit={handleSubmit}>
          <DialogHeader>
            <DialogTitle>Edit User</DialogTitle>
            <DialogDescription>
              Update user information. Leave password empty to keep current
              password.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4 py-4">
            {/* UUID Display - Read Only (Sprint 105) */}
            <div className="space-y-2">
              <Label htmlFor="uuid">User ID (UUID)</Label>
              <div className="flex items-center gap-2">
                <Input
                  id="uuid"
                  type="text"
                  value={user.id}
                  readOnly
                  className="bg-gray-50 text-gray-600 font-mono text-sm"
                />
                <Button
                  type="button"
                  variant="outline"
                  size="icon"
                  onClick={handleCopyUUID}
                  className="shrink-0"
                  title="Copy UUID"
                >
                  {copied ? (
                    <Check className="h-4 w-4 text-green-600" />
                  ) : (
                    <Copy className="h-4 w-4" />
                  )}
                </Button>
              </div>
              <p className="text-xs text-gray-500">
                Unique identifier for this user (read-only)
              </p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="email">
                Email <span className="text-red-500">*</span>
              </Label>
              <Input
                id="email"
                type="text"
                autoComplete="email"
                value={formData.email}
                onChange={(e) => handleChange("email", e.target.value)}
                placeholder="user@example.com"
                className={errors.email ? "border-red-500" : ""}
              />
              {errors.email && (
                <p className="text-sm text-red-500">{errors.email}</p>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="new_password">
                New Password <span className="text-gray-400">(Optional)</span>
              </Label>
              <Input
                id="new_password"
                type="password"
                value={formData.new_password}
                onChange={(e) => handleChange("new_password", e.target.value)}
                placeholder="Leave empty to keep current password"
                className={errors.new_password ? "border-red-500" : ""}
              />
              {errors.new_password && (
                <p className="text-sm text-red-500">{errors.new_password}</p>
              )}
              <p className="text-xs text-gray-500">
                Password must be at least 8 characters (if changing)
              </p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="name">Full Name</Label>
              <Input
                id="name"
                type="text"
                value={formData.name}
                onChange={(e) => handleChange("name", e.target.value)}
                placeholder="John Doe"
              />
            </div>

            <div className="flex items-center space-x-2">
              <Checkbox
                id="is_active"
                checked={formData.is_active}
                onCheckedChange={(checked) =>
                  handleChange("is_active", !!checked)
                }
              />
              <Label htmlFor="is_active" className="text-sm font-medium leading-none">
                Active (user can login to the system)
              </Label>
            </div>

            <div className="flex items-center space-x-2">
              <Checkbox
                id="is_superuser"
                checked={formData.is_superuser}
                onCheckedChange={(checked) =>
                  handleChange("is_superuser", !!checked)
                }
              />
              <Label htmlFor="is_superuser" className="text-sm font-medium leading-none">
                Administrator (full platform access)
              </Label>
            </div>
          </div>

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
              disabled={updateUserMutation.isPending}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              disabled={updateUserMutation.isPending}
              className="min-w-[120px]"
            >
              {updateUserMutation.isPending ? "Updating..." : "Update User"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
