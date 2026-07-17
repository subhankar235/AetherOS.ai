import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

const integrations = [
  { name: "Gmail", desc: "Read + label via Pub/Sub webhook", connected: true },
  { name: "Google Calendar", desc: "Create events with approval", connected: true },
  { name: "Google Meet", desc: "Attach Meet links to events", connected: true },
  { name: "ElevenLabs", desc: "STT + TTS for voice mode", connected: true },
  { name: "Qdrant", desc: "Vector store for knowledge RAG", connected: true },
  { name: "Slack", desc: "Notifications + future multi-channel", connected: false },
  { name: "Stripe", desc: "Payment execution (scaffold, disabled)", connected: false },
  { name: "Notion", desc: "Knowledge source", connected: false },
];

export default function IntegrationsPage() {
  return (
    <div className="grid gap-3 md:grid-cols-2">
      {integrations.map((i) => (
        <Card key={i.name} className="flex items-start justify-between p-4">
          <div>
            <div className="flex items-center gap-2">
              <span className="font-medium">{i.name}</span>
              {i.connected ? (
                <Badge variant="secondary">Connected</Badge>
              ) : (
                <Badge variant="outline">Not connected</Badge>
              )}
            </div>
            <div className="mt-1 text-xs text-muted-foreground">{i.desc}</div>
          </div>
          <Button size="sm" variant={i.connected ? "outline" : "default"}>
            {i.connected ? "Manage" : "Connect"}
          </Button>
        </Card>
      ))}
    </div>
  );
}
