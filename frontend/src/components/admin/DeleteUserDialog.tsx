"use client";

/**
 * Delete User Dialog - Next.js App Router
 * @status Sprint 68 - Admin Section Migration
 * @description Confirmation dialog for soft-deleting users
 */

import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { useDeleteAdminUser } from "@/hooks/useAdmin";
import { useToast } from "@/hooks/useToast";
import { AlertTriangle } from "lucide-react";
import type { AdminUser } from "@/lib/types/admin";

interface DeleteUserDialogProps {
  user: AdminUser | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSuccess?: () => void;
}

export function DeleteUserDialog({ user, open, onOpenChange, onSuccess }: DeleteUserDialogProps) {
  const { toast } = useToast();
  const deleteUserMutation = useDeleteAdminUser();

  const handleDelete = async () => {
    if (!user || deleteUserMutation.isPending) return;

    try {
      await deleteUserMutation.mutateAsync(user.id);

      toast({
        title: "User Deleted",
        description: `User ${user.email} has been deleted successfully`,
      });

      onOpenChange(false);
      onSuccess?.();
    } catch (error: unknown) {
      const message = error instanceof Error ? error.message : "Failed to delete user";
      toast({
        title: "Error",
        description: message,
        variant: "destructive",
      });
    }
  };

  if (!user) return null;

  return (
    <AlertDialog open={open} onOpenChange={onOpenChange}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>Delete User?</AlertDialogTitle>
          <AlertDialogDescription>
            Are you sure you want to delete the user{" "}
            <strong>{user.email}</strong>?
          </AlertDialogDescription>
        </AlertDialogHeader>

        <div className="rounded-lg bg-amber-50 border border-amber-200 p-4">
          <div className="flex gap-3">
            <AlertTriangle className="h-5 w-5 text-amber-600 flex-shrink-0 mt-0.5" />
            <div className="flex-1">
              <h4 className="text-sm font-medium text-amber-800">Warning</h4>
              <div className="mt-1 text-sm text-amber-700 space-y-1">
                <p>This action will:</p>
                <ul className="list-disc list-inside ml-2">
                  <li>Deactivate the user account</li>
                  <li>Prevent the user from logging in</li>
                  <li>Preserve all audit logs and history</li>
                </ul>
                <p className="mt-2">
                  <strong>Note:</strong> This is a soft delete. User data is
                  preserved for audit purposes.
                </p>
              </div>
            </div>
          </div>
        </div>

        <AlertDialogFooter>
          <AlertDialogCancel disabled={deleteUserMutation.isPending}>
            Cancel
          </AlertDialogCancel>
          <AlertDialogAction
            onClick={(e) => {
              e.preventDefault();
              handleDelete();
            }}
            disabled={deleteUserMutation.isPending}
            className="bg-red-600 hover:bg-red-700 min-w-[120px]"
          >
            {deleteUserMutation.isPending ? "Deleting..." : "Delete User"}
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}
