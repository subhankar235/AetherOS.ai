import { Card } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";

export default function VoiceSettings() {
  return (
    <div className="space-y-4">
      <Card className="p-5">
        <h2 className="text-sm font-semibold">Voice</h2>
        <div className="mt-4 grid gap-4 md:grid-cols-2">
          <div>
            <Label>ElevenLabs voice ID</Label>
            <Input defaultValue="aria-natural-v2" className="mt-1.5" />
          </div>
          <div>
            <Label>Wake word</Label>
            <Input defaultValue="Hey Aether" className="mt-1.5" />
          </div>
        </div>
      </Card>

      <Card className="p-5">
        <h2 className="text-sm font-semibold">Tone profile</h2>
        <p className="mt-1 text-xs text-muted-foreground">
          Aether uses this profile in the conversational rewrite step before speaking.
        </p>
        <Textarea
          className="mt-3 min-h-[140px]"
          defaultValue="Warm but concise. Prefer contractions. Never sound robotic. Use founder-to-founder language when talking about investors and product."
        />
      </Card>

      <div>
        <Button>Save voice profile</Button>
      </div>
    </div>
  );
}
