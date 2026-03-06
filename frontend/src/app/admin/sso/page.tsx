"use client";

/**
 * SSO Configuration Page - Next.js App Router
 * @route /admin/sso
 * @status Sprint 212 - Track E
 * @description Enterprise SSO (SAML 2.0 / Azure AD) configuration for admin users
 * @security Requires is_superuser=true
 */

import { useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ArrowLeft, Shield, CheckCircle, XCircle, Loader2 } from "lucide-react";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

type SsoStatus = "enabled" | "disabled" | "not_configured";
type SsoProvider = "saml" | "azure_ad";
type TestResult = "success" | "failure" | null;

interface SsoConfig {
  provider: SsoProvider;
  idp_metadata_url: string;
  entity_id: string;
  certificate: string;
  status: SsoStatus;
}

const EMPTY_CONFIG: SsoConfig = {
  provider: "saml",
  idp_metadata_url: "",
  entity_id: "",
  certificate: "",
  status: "not_configured",
};

const IDP_HELP: Record<string, { label: string; metadataHint: string; entityHint: string }> = {
  okta: {
    label: "Okta",
    metadataHint: "https://your-org.okta.com/app/exk.../sso/saml/metadata",
    entityHint: "http://www.okta.com/exk...",
  },
  azure: {
    label: "Azure AD",
    metadataHint: "https://login.microsoftonline.com/{tenant}/federationmetadata/2007-06/federationmetadata.xml",
    entityHint: "https://sts.windows.net/{tenant-id}/",
  },
  google: {
    label: "Google Workspace",
    metadataHint: "https://accounts.google.com/o/saml2?idpid=...",
    entityHint: "https://accounts.google.com/o/saml2?idpid=...",
  },
};

function getAuthHeaders(): Record<string, string> {
  const token =
    typeof window !== "undefined"
      ? localStorage.getItem("access_token")
      : null;
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }
  return headers;
}

function StatusBadge({ status }: { status: SsoStatus }) {
  switch (status) {
    case "enabled":
      return <Badge className="bg-green-100 text-green-700 hover:bg-green-100">Enabled</Badge>;
    case "disabled":
      return <Badge variant="secondary">Disabled</Badge>;
    default:
      return <Badge variant="outline">Not Configured</Badge>;
  }
}

export default function SsoConfigPage() {
  const router = useRouter();
  const [config, setConfig] = useState<SsoConfig>(EMPTY_CONFIG);
  const [activeTab, setActiveTab] = useState<SsoProvider>("saml");
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState<TestResult>(null);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // Load current SSO configuration on mount
  const loadConfig = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/enterprise/sso/config`, {
        headers: getAuthHeaders(),
      });
      if (response.ok) {
        const data = await response.json();
        setConfig({
          provider: data.provider || "saml",
          idp_metadata_url: data.idp_metadata_url || "",
          entity_id: data.entity_id || "",
          certificate: data.certificate || "",
          status: data.status || "not_configured",
        });
        setActiveTab(data.provider || "saml");
      }
    } catch {
      // Config not yet created, use defaults
    }
  }, []);

  useEffect(() => {
    loadConfig();
  }, [loadConfig]);

  const handleSave = async () => {
    setError(null);
    setSuccessMsg(null);
    setSaving(true);

    try {
      if (!config.idp_metadata_url.trim()) {
        setError("IdP Metadata URL is required");
        return;
      }
      if (!config.entity_id.trim()) {
        setError("Entity ID is required");
        return;
      }

      const response = await fetch(
        `${API_BASE_URL}/enterprise/sso/configure`,
        {
          method: "POST",
          headers: getAuthHeaders(),
          body: JSON.stringify({
            provider: activeTab,
            idp_metadata_url: config.idp_metadata_url.trim(),
            entity_id: config.entity_id.trim(),
            certificate: config.certificate.trim(),
          }),
        }
      );

      if (!response.ok) {
        const data = await response.json().catch(() => null);
        throw new Error(
          data?.detail || `Save failed with status ${response.status}`
        );
      }

      const data = await response.json();
      setConfig((prev) => ({
        ...prev,
        provider: activeTab,
        status: data.status || "disabled",
      }));
      setSuccessMsg("SSO configuration saved successfully");
      setTestResult(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save configuration");
    } finally {
      setSaving(false);
    }
  };

  const handleTest = async () => {
    setTesting(true);
    setTestResult(null);
    setError(null);

    try {
      const response = await fetch(
        `${API_BASE_URL}/enterprise/sso/test`,
        {
          method: "POST",
          headers: getAuthHeaders(),
        }
      );

      if (response.ok) {
        setTestResult("success");
      } else {
        setTestResult("failure");
        const data = await response.json().catch(() => null);
        setError(data?.detail || "Connection test failed");
      }
    } catch {
      setTestResult("failure");
      setError("Unable to reach SSO endpoint. Check your configuration.");
    } finally {
      setTesting(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Page header */}
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => router.push("/admin")}
              className="h-8 w-8 p-0"
            >
              <ArrowLeft className="h-4 w-4" />
            </Button>
            <h1 className="text-3xl font-bold tracking-tight">
              SSO Configuration
            </h1>
          </div>
          <p className="text-muted-foreground">
            Configure Single Sign-On for enterprise identity providers
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Shield className="h-5 w-5 text-muted-foreground" />
          <StatusBadge status={config.status} />
        </div>
      </div>

      {/* Error / Success messages */}
      {error && (
        <Card className="border-red-200 bg-red-50">
          <CardContent className="py-3">
            <p className="text-sm text-red-700">{error}</p>
          </CardContent>
        </Card>
      )}
      {successMsg && (
        <Card className="border-green-200 bg-green-50">
          <CardContent className="py-3">
            <p className="text-sm text-green-700">{successMsg}</p>
          </CardContent>
        </Card>
      )}

      {/* Provider selector */}
      <Tabs
        value={activeTab}
        onValueChange={(v) => setActiveTab(v as SsoProvider)}
      >
        <TabsList>
          <TabsTrigger value="saml">SAML 2.0</TabsTrigger>
          <TabsTrigger value="azure_ad">Azure AD</TabsTrigger>
        </TabsList>

        {/* SAML 2.0 tab */}
        <TabsContent value="saml" className="space-y-4 mt-4">
          <Card>
            <CardHeader>
              <CardTitle>SAML 2.0 Configuration</CardTitle>
              <CardDescription>
                Connect to any SAML 2.0 compatible identity provider (Okta,
                OneLogin, PingFederate, etc.)
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="saml-metadata-url">
                  IdP Metadata URL <span className="text-red-500">*</span>
                </Label>
                <Input
                  id="saml-metadata-url"
                  placeholder="https://your-idp.example.com/saml/metadata"
                  value={config.idp_metadata_url}
                  onChange={(e) =>
                    setConfig((prev) => ({
                      ...prev,
                      idp_metadata_url: e.target.value,
                    }))
                  }
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="saml-entity-id">
                  Entity ID <span className="text-red-500">*</span>
                </Label>
                <Input
                  id="saml-entity-id"
                  placeholder="https://your-idp.example.com/entity"
                  value={config.entity_id}
                  onChange={(e) =>
                    setConfig((prev) => ({
                      ...prev,
                      entity_id: e.target.value,
                    }))
                  }
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="saml-cert">
                  X.509 Certificate (PEM format)
                </Label>
                <textarea
                  id="saml-cert"
                  rows={6}
                  placeholder={"-----BEGIN CERTIFICATE-----\nMIIC...\n-----END CERTIFICATE-----"}
                  value={config.certificate}
                  onChange={(e) =>
                    setConfig((prev) => ({
                      ...prev,
                      certificate: e.target.value,
                    }))
                  }
                  className="flex w-full rounded-md border border-input bg-background px-3 py-2 text-sm font-mono ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                />
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Azure AD tab */}
        <TabsContent value="azure_ad" className="space-y-4 mt-4">
          <Card>
            <CardHeader>
              <CardTitle>Azure AD Configuration</CardTitle>
              <CardDescription>
                Connect via Microsoft Entra ID (formerly Azure Active Directory)
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="azure-metadata-url">
                  Federation Metadata URL <span className="text-red-500">*</span>
                </Label>
                <Input
                  id="azure-metadata-url"
                  placeholder="https://login.microsoftonline.com/{tenant-id}/federationmetadata/2007-06/federationmetadata.xml"
                  value={config.idp_metadata_url}
                  onChange={(e) =>
                    setConfig((prev) => ({
                      ...prev,
                      idp_metadata_url: e.target.value,
                    }))
                  }
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="azure-entity-id">
                  Entity ID (Identifier) <span className="text-red-500">*</span>
                </Label>
                <Input
                  id="azure-entity-id"
                  placeholder="https://sts.windows.net/{tenant-id}/"
                  value={config.entity_id}
                  onChange={(e) =>
                    setConfig((prev) => ({
                      ...prev,
                      entity_id: e.target.value,
                    }))
                  }
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="azure-cert">
                  X.509 Certificate (PEM format)
                </Label>
                <textarea
                  id="azure-cert"
                  rows={6}
                  placeholder={"-----BEGIN CERTIFICATE-----\nMIIC...\n-----END CERTIFICATE-----"}
                  value={config.certificate}
                  onChange={(e) =>
                    setConfig((prev) => ({
                      ...prev,
                      certificate: e.target.value,
                    }))
                  }
                  className="flex w-full rounded-md border border-input bg-background px-3 py-2 text-sm font-mono ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                />
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Actions */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Button onClick={handleSave} disabled={saving}>
                {saving && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
                {saving ? "Saving..." : "Save Configuration"}
              </Button>
              <Button
                variant="outline"
                onClick={handleTest}
                disabled={
                  testing || config.status === "not_configured"
                }
              >
                {testing && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
                {testing ? "Testing..." : "Test Connection"}
              </Button>
              {testResult === "success" && (
                <div className="flex items-center gap-1 text-green-600 text-sm">
                  <CheckCircle className="h-4 w-4" />
                  Connection successful
                </div>
              )}
              {testResult === "failure" && (
                <div className="flex items-center gap-1 text-red-600 text-sm">
                  <XCircle className="h-4 w-4" />
                  Connection failed
                </div>
              )}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* IdP Help section */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">
            Common Identity Provider Setup
          </CardTitle>
          <CardDescription>
            Reference URLs for popular identity providers
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {Object.entries(IDP_HELP).map(([key, idp]) => (
              <div key={key} className="rounded-lg border p-4">
                <h4 className="font-medium text-sm mb-2">{idp.label}</h4>
                <div className="space-y-1">
                  <p className="text-xs text-muted-foreground">
                    <span className="font-medium">Metadata URL: </span>
                    <code className="bg-muted px-1 py-0.5 rounded text-xs">
                      {idp.metadataHint}
                    </code>
                  </p>
                  <p className="text-xs text-muted-foreground">
                    <span className="font-medium">Entity ID: </span>
                    <code className="bg-muted px-1 py-0.5 rounded text-xs">
                      {idp.entityHint}
                    </code>
                  </p>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
