"use client"

import { useEffect, useState } from "react";
import { useAuth } from "@clerk/nextjs";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Loader2, CheckCircle2, XCircle, RefreshCw } from "lucide-react";

interface GoogleStatus {
  connected: boolean;
  scopes: string[];
  is_expired?: boolean;
  revoked?: boolean;
  expires_at?: string;
}

export default function IntegrationsPage() {
  const { getToken } = useAuth();
  const [googleStatus, setGoogleStatus] = useState<GoogleStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);

  const fetchStatus = async () => {
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const token = await getToken();
      const headers: Record<string, string> = {};
      if (token) {
        headers["Authorization"] = `Bearer ${token}`;
      }

      const res = await fetch(`${apiUrl}/integrations/google/status`, { headers });
      if (res.ok) {
        const data = await res.json();
        setGoogleStatus(data);
      }
    } catch (err) {
      console.error("Failed to fetch Google integration status:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStatus();
  }, []);

  const handleConnectGoogle = async (extraScopes?: string) => {
    setActionLoading(true);
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const token = await getToken();
      
      let connectUrl = `${apiUrl}/integrations/google/connect?redirect=false`;
      if (extraScopes) {
        connectUrl += `&scopes=${encodeURIComponent(extraScopes)}`;
      }

      const headers: Record<string, string> = { Accept: "application/json" };
      if (token) {
        headers["Authorization"] = `Bearer ${token}`;
      }

      const res = await fetch(connectUrl, { headers });
      if (!res.ok) {
        throw new Error(`Failed to initiate Google connection: ${res.statusText}`);
      }

      const data = await res.json();
      if (data.url) {
        window.location.href = data.url;
      }
    } catch (err) {
      console.error("Failed to connect Google:", err);
      setActionLoading(false);
    }
  };

  const handleDisconnectGoogle = async () => {
    setActionLoading(true);
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const token = await getToken();
      const headers: Record<string, string> = {};
      if (token) {
        headers["Authorization"] = `Bearer ${token}`;
      }

      const res = await fetch(`${apiUrl}/integrations/google`, {
        method: "DELETE",
        headers,
      });

      if (res.ok) {
        setGoogleStatus({ connected: false, scopes: [] });
      }
    } catch (err) {
      console.error("Failed to disconnect Google:", err);
    } finally {
      setActionLoading(false);
    }
  };

  const isGoogleConnected = googleStatus?.connected ?? false;

  const staticIntegrations = [
    { name: "ElevenLabs", desc: "STT + TTS for human voice mode", connected: true, system: true },
    { name: "Qdrant", desc: "Vector store for Knowledge Base RAG", connected: true, system: true },
    { name: "Slack", desc: "Notifications + multi-channel (Future)", connected: false, system: false },
    { name: "Stripe", desc: "Payment execution (Scaffold, disabled)", connected: false, system: false },
  ];

  return (
    <div className="mx-auto max-w-5xl space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Integrations & Connections</h1>
        <p className="text-sm text-muted-foreground">
          Manage per-user OAuth connections and system service integrations.
        </p>
      </div>

      {loading ? (
        <div className="flex items-center justify-center p-12">
          <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
        </div>
      ) : (
        <div className="space-y-4">
          {/* Google Workspace Core Connection Card */}
          <Card className="p-5 border-primary/30">
            <div className="flex items-start justify-between">
              <div>
                <div className="flex items-center gap-2">
                  <span className="font-semibold text-base">Google Workspace (Gmail & Calendar)</span>
                  {isGoogleConnected ? (
                    <Badge variant="secondary" className="bg-emerald-500/10 text-emerald-500 hover:bg-emerald-500/20">
                      <CheckCircle2 className="mr-1 h-3 w-3" /> Connected
                    </Badge>
                  ) : (
                    <Badge variant="outline" className="text-muted-foreground">
                      <XCircle className="mr-1 h-3 w-3" /> Not Connected
                    </Badge>
                  )}
                </div>
                <p className="mt-1 text-xs text-muted-foreground">
                  Connect your Google Account to grant Aether access to read/sync Gmail, schedule Calendar events, and generate Google Meet links.
                </p>

                {isGoogleConnected && googleStatus?.scopes && (
                  <div className="mt-3 flex flex-wrap gap-1.5">
                    <span className="text-[11px] font-medium text-muted-foreground">Granted Scopes:</span>
                    {googleStatus.scopes.map((scope) => (
                      <Badge key={scope} variant="outline" className="text-[10px]">
                        {scope.split("/").pop()}
                      </Badge>
                    ))}
                  </div>
                )}
              </div>

              <div className="flex gap-2">
                {isGoogleConnected ? (
                  <>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => handleConnectGoogle("https://www.googleapis.com/auth/calendar")}
                      disabled={actionLoading}
                    >
                      <RefreshCw className="mr-1.5 h-3.5 w-3.5" /> Re-consent / Grant Scopes
                    </Button>
                    <Button
                      size="sm"
                      variant="destructive"
                      onClick={handleDisconnectGoogle}
                      disabled={actionLoading}
                    >
                      Disconnect
                    </Button>
                  </>
                ) : (
                  <Button
                    size="sm"
                    onClick={() => handleConnectGoogle()}
                    disabled={actionLoading}
                  >
                    {actionLoading ? <Loader2 className="mr-1.5 h-3.5 w-3.5 animate-spin" /> : null}
                    Connect Google Account
                  </Button>
                )}
              </div>
            </div>
          </Card>

          {/* System & Other Integrations */}
          <div className="grid gap-3 md:grid-cols-2">
            {staticIntegrations.map((i) => (
              <Card key={i.name} className="flex items-start justify-between p-4">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-medium">{i.name}</span>
                    {i.connected ? (
                      <Badge variant="secondary">Active</Badge>
                    ) : (
                      <Badge variant="outline">Disabled</Badge>
                    )}
                  </div>
                  <div className="mt-1 text-xs text-muted-foreground">{i.desc}</div>
                </div>
                <Button size="sm" variant={i.connected ? "outline" : "default"} disabled={i.system}>
                  {i.connected ? "Active" : "Connect"}
                </Button>
              </Card>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
