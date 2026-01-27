"use client";

/**
 * Create User Dialog - Next.js App Router
 * @status Sprint 68 - Admin Section Migration
 * @description Dialog for creating new users with validation
 */

import { useState } from "react";
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
import { useCreateAdminUser } from "@/hooks/useAdmin";
import { useToast } from "@/hooks/useToast";

interface CreateUserDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function CreateUserDialog({ open, onOpenChange }: CreateUserDialogProps) {
  const { toast } = useToast();
  const createUserMutation = useCreateAdminUser();

  const [formData, setFormData] = useState({
    email: "",
    password: "",
    name: "",
    is_active: true,
    is_superuser: false,
  });

  const [errors, setErrors] = useState<Record<string, string>>({});

  const validateForm = () => {
    const newErrors: Record<string, string> = {};

    if (!formData.email) {
      newErrors.email = "Email is required";
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      newErrors.email = "Invalid email format";
    }

    if (!formData.password) {
      newErrors.password = "Password is required";
    } else if (formData.password.length < 8) {
      newErrors.password = "Password must be at least 8 characters";
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateForm() || createUserMutation.isPending) {
      return;
    }

    try {
      await createUserMutation.mutateAsync({
        email: formData.email,
        password: formData.password,
        name: formData.name || undefined,
        is_active: formData.is_active,
        is_superuser: formData.is_superuser,
      });

      toast({
        title: "User Created",
        description: `User ${formData.email} has been created successfully`,
      });

      setFormData({
        email: "",
        password: "",
        name: "",
        is_active: true,
        is_superuser: false,
      });
      setErrors({});
      onOpenChange(false);
    } catch (error: unknown) {
      const message = error instanceof Error ? error.message : "Failed to create user";
      toast({
        title: "Error",
        description: message,
        variant: "destructive",
      });
    }
  };

  const handleCancel = () => {
    setFormData({
      email: "",
      password: "",
      name: "",
      is_active: true,
      is_superuser: false,
    });
    setErrors({});
    onOpenChange(false);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[500px]">
        <form onSubmit={handleSubmit}>
          <DialogHeader>
            <DialogTitle>Create New User</DialogTitle>
            <DialogDescription>
              Create a new user account. The user will be able to login with the
              email and password provided.
            </DialogDescription>
          </DialogHeader>

          <div className="grid gap-4 py-4">
            <div className="grid gap-2">
              <Label htmlFor="email">
                Email <span className="text-red-500">*</span>
              </Label>
              <Input
                id="email"
                type="text"
                autoComplete="email"
                placeholder="user@example.com"
                value={formData.email}
                onChange={(e) => {
                  setFormData({ ...formData, email: e.target.value });
                  setErrors({ ...errors, email: "" });
                }}
                className={errors.email ? "border-red-500" : ""}
              />
              {errors.email && (
                <p className="text-sm text-red-500">{errors.email}</p>
              )}
            </div>

            <div className="grid gap-2">
              <Label htmlFor="password">
                Password <span className="text-red-500">*</span>
              </Label>
              <Input
                id="password"
                type="password"
                placeholder="Min 12 characters"
                value={formData.password}
                onChange={(e) => {
                  setFormData({ ...formData, password: e.target.value });
                  setErrors({ ...errors, password: "" });
                }}
                className={errors.password ? "border-red-500" : ""}
              />
              {errors.password && (
                <p className="text-sm text-red-500">{errors.password}</p>
              )}
              <p className="text-sm text-muted-foreground">
                Password must be at least 8 characters long
              </p>
            </div>

            <div className="grid gap-2">
              <Label htmlFor="name">Full Name (Optional)</Label>
              <Input
                id="name"
                type="text"
                placeholder="John Doe"
                value={formData.name}
                onChange={(e) =>
                  setFormData({ ...formData, name: e.target.value })
                }
              />
            </div>

            <div className="flex items-center space-x-2">
              <Checkbox
                id="is_active"
                checked={formData.is_active}
                onCheckedChange={(checked) =>
                  setFormData({ ...formData, is_active: checked === true })
                }
              />
              <Label htmlFor="is_active" className="cursor-pointer font-normal">
                Active (user can login)
              </Label>
            </div>

            <div className="flex items-center space-x-2">
              <Checkbox
                id="is_superuser"
                checked={formData.is_superuser}
                onCheckedChange={(checked) =>
                  setFormData({ ...formData, is_superuser: checked === true })
                }
              />
              <Label htmlFor="is_superuser" className="cursor-pointer font-normal">
                <span>Administrator (full platform access)</span>
                <p className="text-sm text-muted-foreground font-normal">
                  Admins can manage all users and system settings
                </p>
              </Label>
            </div>
          </div>

          <DialogFooter>
            <Button type="button" variant="outline" onClick={handleCancel}>
              Cancel
            </Button>
            <Button
              type="submit"
              disabled={createUserMutation.isPending}
              className="min-w-[120px]"
            >
              {createUserMutation.isPending ? "Creating..." : "Create User"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
