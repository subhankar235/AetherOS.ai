"use client"

import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Button } from "@/components/ui/button";

export default function GeneralSettings() {
  return (
    <div className="space-y-4">
      <Card className="p-5">
        <h2 className="text-sm font-semibold">Profile</h2>
        <div className="mt-4 grid gap-4 md:grid-cols-2">
          <div>
            <Label>Name</Label>
            <Input defaultValue="Alex Kim" className="mt-1.5" />
          </div>
          <div>
            <Label>Email</Label>
            <Input defaultValue="alex@company.com" className="mt-1.5" />
          </div>
        </div>
      </Card>

      <Card className="p-5">
        <h2 className="text-sm font-semibold">Automatic pipeline</h2>
        <p className="mt-1 text-xs text-muted-foreground">
          Only silent work runs automatically. Sending, scheduling, and payments are always gated.
        </p>
        <div className="mt-4 space-y-3">
          {([
            ["Auto-summarize new email", true],
            ["Auto-categorize (investor / customer / team…)", true],
            ["Auto-priority scoring", true],
            ["Auto-labeling in Gmail", true],
            ["Auto-draft replies (kept as drafts, never sent)", false],
          ] as const).map(([label, on]) => (
            <div key={label} className="flex items-center justify-between">
              <span className="text-sm">{label}</span>
              <Switch defaultChecked={on} />
            </div>
          ))}
        </div>
      </Card>

      <div>
        <Button>Save changes</Button>
      </div>
    </div>
  );
}
