/**
 * Workspace Context - SDLC Orchestrator Dashboard
 *
 * @module frontend/src/contexts/WorkspaceContext
 * @description Context for managing selected organization and team across dashboard
 * @sdlc SDLC 5.1.3 Framework - Sprint 91 (Teams & Organizations UI)
 * @status Sprint 91 - Team/Org Switcher Implementation
 */

"use client";

import {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
  type ReactNode,
} from "react";
import { useOrganizations, type Organization } from "@/hooks/useOrganizations";
import { useTeams, type Team } from "@/hooks/useTeams";
import { useAuth } from "@/hooks/useAuth";

// Storage keys for persistence
const STORAGE_KEY_ORG = "sdlc_selected_org_id";
const STORAGE_KEY_TEAM = "sdlc_selected_team_id";

interface WorkspaceContextValue {
  // Selected entities
  selectedOrganization: Organization | null;
  selectedTeam: Team | null;

  // Available entities
  organizations: Organization[];
  teams: Team[];

  // Loading states
  isLoadingOrganizations: boolean;
  isLoadingTeams: boolean;

  // Actions
  selectOrganization: (orgId: string | null) => void;
  selectTeam: (teamId: string | null) => void;

  // Computed
  hasOrganizations: boolean;
  hasTeams: boolean;
}

const WorkspaceContext = createContext<WorkspaceContextValue | null>(null);

export function WorkspaceProvider({ children }: { children: ReactNode }) {
  const { isAuthenticated, isLoading: authLoading } = useAuth();

  // Selected IDs (stored in localStorage)
  const [selectedOrgId, setSelectedOrgId] = useState<string | null>(null);
  const [selectedTeamId, setSelectedTeamId] = useState<string | null>(null);

  // Fetch organizations
  const {
    data: orgsData,
    isLoading: isLoadingOrgs,
  } = useOrganizations();

  // Fetch teams filtered by selected organization
  const {
    data: teamsData,
    isLoading: isLoadingTeams,
  } = useTeams(selectedOrgId ? { organization_id: selectedOrgId } : undefined);

  const organizations = orgsData?.items ?? [];
  const teams = teamsData?.items ?? [];

  // Find selected entities
  const selectedOrganization = organizations.find((o: Organization) => o.id === selectedOrgId) ?? null;
  const selectedTeam = teams.find((t: Team) => t.id === selectedTeamId) ?? null;

  // Load from localStorage on mount
  useEffect(() => {
    if (typeof window !== "undefined" && isAuthenticated && !authLoading) {
      const storedOrgId = localStorage.getItem(STORAGE_KEY_ORG);
      const storedTeamId = localStorage.getItem(STORAGE_KEY_TEAM);

      if (storedOrgId) {
        setSelectedOrgId(storedOrgId);
      }
      if (storedTeamId) {
        setSelectedTeamId(storedTeamId);
      }
    }
  }, [isAuthenticated, authLoading]);

  // Auto-select first organization if none selected and organizations loaded
  useEffect(() => {
    if (!selectedOrgId && organizations.length > 0 && !isLoadingOrgs) {
      const firstOrg = organizations[0];
      setSelectedOrgId(firstOrg.id);
      if (typeof window !== "undefined") {
        localStorage.setItem(STORAGE_KEY_ORG, firstOrg.id);
      }
    }
  }, [organizations, selectedOrgId, isLoadingOrgs]);

  // Auto-select first team when organization changes
  useEffect(() => {
    if (selectedOrgId && teams.length > 0 && !isLoadingTeams) {
      // Check if current selected team belongs to selected org
      const teamInOrg = teams.find((t) => t.id === selectedTeamId);
      if (!teamInOrg) {
        const firstTeam = teams[0];
        setSelectedTeamId(firstTeam.id);
        if (typeof window !== "undefined") {
          localStorage.setItem(STORAGE_KEY_TEAM, firstTeam.id);
        }
      }
    }
  }, [selectedOrgId, teams, selectedTeamId, isLoadingTeams]);

  // Clear team selection if no teams in org
  useEffect(() => {
    if (selectedOrgId && teams.length === 0 && !isLoadingTeams && selectedTeamId) {
      setSelectedTeamId(null);
      if (typeof window !== "undefined") {
        localStorage.removeItem(STORAGE_KEY_TEAM);
      }
    }
  }, [selectedOrgId, teams, selectedTeamId, isLoadingTeams]);

  const selectOrganization = useCallback((orgId: string | null) => {
    setSelectedOrgId(orgId);
    // Clear team when org changes
    setSelectedTeamId(null);

    if (typeof window !== "undefined") {
      if (orgId) {
        localStorage.setItem(STORAGE_KEY_ORG, orgId);
      } else {
        localStorage.removeItem(STORAGE_KEY_ORG);
      }
      localStorage.removeItem(STORAGE_KEY_TEAM);
    }
  }, []);

  const selectTeam = useCallback((teamId: string | null) => {
    setSelectedTeamId(teamId);

    if (typeof window !== "undefined") {
      if (teamId) {
        localStorage.setItem(STORAGE_KEY_TEAM, teamId);
      } else {
        localStorage.removeItem(STORAGE_KEY_TEAM);
      }
    }
  }, []);

  const value: WorkspaceContextValue = {
    selectedOrganization,
    selectedTeam,
    organizations,
    teams,
    isLoadingOrganizations: isLoadingOrgs,
    isLoadingTeams,
    selectOrganization,
    selectTeam,
    hasOrganizations: organizations.length > 0,
    hasTeams: teams.length > 0,
  };

  return (
    <WorkspaceContext.Provider value={value}>
      {children}
    </WorkspaceContext.Provider>
  );
}

export function useWorkspace() {
  const context = useContext(WorkspaceContext);
  if (!context) {
    throw new Error("useWorkspace must be used within a WorkspaceProvider");
  }
  return context;
}

// Export types
export type { WorkspaceContextValue };
