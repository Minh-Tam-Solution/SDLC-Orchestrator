"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { InvitationCard } from "./InvitationCard";
import { InviteMemberModal } from "./InviteMemberModal";
import { useInvitations } from "@/hooks/useInvitations";

interface InvitationListProps {
  teamId: string;
  teamName: string;
  canInvite?: boolean;
}

export function InvitationList({
  teamId,
  teamName,
  canInvite = true,
}: InvitationListProps) {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [activeTab, setActiveTab] = useState("pending");

  const {
    pendingInvitations,
    expiredInvitations,
    acceptedInvitations,
    declinedInvitations,
    isLoading,
    cancelInvitation,
    resendInvitation,
    isCanceling,
    isResending,
  } = useInvitations(teamId);

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Team Invitations</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center py-8">
            <svg
              className="h-8 w-8 animate-spin text-muted-foreground"
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
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <>
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle>Team Invitations</CardTitle>
          {canInvite && (
            <Button onClick={() => setIsModalOpen(true)}>
              <svg
                className="mr-2 h-4 w-4"
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
                strokeWidth={1.5}
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M12 4.5v15m7.5-7.5h-15"
                />
              </svg>
              Invite Member
            </Button>
          )}
        </CardHeader>
        <CardContent>
          <Tabs value={activeTab} onValueChange={setActiveTab}>
            <TabsList className="grid w-full grid-cols-4">
              <TabsTrigger value="pending" className="relative">
                Pending
                {pendingInvitations.length > 0 && (
                  <Badge variant="secondary" className="ml-2">
                    {pendingInvitations.length}
                  </Badge>
                )}
              </TabsTrigger>
              <TabsTrigger value="accepted">
                Accepted
                {acceptedInvitations.length > 0 && (
                  <Badge variant="secondary" className="ml-2">
                    {acceptedInvitations.length}
                  </Badge>
                )}
              </TabsTrigger>
              <TabsTrigger value="expired">
                Expired
                {expiredInvitations.length > 0 && (
                  <Badge variant="secondary" className="ml-2">
                    {expiredInvitations.length}
                  </Badge>
                )}
              </TabsTrigger>
              <TabsTrigger value="declined">
                Declined
                {declinedInvitations.length > 0 && (
                  <Badge variant="secondary" className="ml-2">
                    {declinedInvitations.length}
                  </Badge>
                )}
              </TabsTrigger>
            </TabsList>

            <TabsContent value="pending" className="space-y-4 mt-4">
              {pendingInvitations.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground">
                  <svg
                    className="mx-auto h-12 w-12 text-muted-foreground/50"
                    xmlns="http://www.w3.org/2000/svg"
                    fill="none"
                    viewBox="0 0 24 24"
                    strokeWidth={1.5}
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      d="M21.75 6.75v10.5a2.25 2.25 0 01-2.25 2.25h-15a2.25 2.25 0 01-2.25-2.25V6.75m19.5 0A2.25 2.25 0 0019.5 4.5h-15a2.25 2.25 0 00-2.25 2.25m19.5 0v.243a2.25 2.25 0 01-1.07 1.916l-7.5 4.615a2.25 2.25 0 01-2.36 0L3.32 8.91a2.25 2.25 0 01-1.07-1.916V6.75"
                    />
                  </svg>
                  <p className="mt-4">No pending invitations</p>
                  <p className="text-sm">
                    Invite members to collaborate on your team
                  </p>
                </div>
              ) : (
                pendingInvitations.map((invitation) => (
                  <InvitationCard
                    key={invitation.id}
                    invitation={invitation}
                    onCancel={() => cancelInvitation(invitation.id)}
                    onResend={() => resendInvitation(invitation.id)}
                    isCanceling={isCanceling}
                    isResending={isResending}
                  />
                ))
              )}
            </TabsContent>

            <TabsContent value="accepted" className="space-y-4 mt-4">
              {acceptedInvitations.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground">
                  <p>No accepted invitations</p>
                </div>
              ) : (
                acceptedInvitations.map((invitation) => (
                  <InvitationCard
                    key={invitation.id}
                    invitation={invitation}
                    isCanceling={false}
                    isResending={false}
                  />
                ))
              )}
            </TabsContent>

            <TabsContent value="expired" className="space-y-4 mt-4">
              {expiredInvitations.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground">
                  <p>No expired invitations</p>
                </div>
              ) : (
                expiredInvitations.map((invitation) => (
                  <InvitationCard
                    key={invitation.id}
                    invitation={invitation}
                    onResend={() => resendInvitation(invitation.id)}
                    isCanceling={false}
                    isResending={isResending}
                  />
                ))
              )}
            </TabsContent>

            <TabsContent value="declined" className="space-y-4 mt-4">
              {declinedInvitations.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground">
                  <p>No declined invitations</p>
                </div>
              ) : (
                declinedInvitations.map((invitation) => (
                  <InvitationCard
                    key={invitation.id}
                    invitation={invitation}
                    isCanceling={false}
                    isResending={false}
                  />
                ))
              )}
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>

      <InviteMemberModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        teamId={teamId}
        teamName={teamName}
      />
    </>
  );
}
