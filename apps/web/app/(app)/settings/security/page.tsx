import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";

export default function SecuritySettings() {
  return (
    <div className="space-y-4">
      <Card className="p-5">
        <h2 className="text-sm font-semibold">Approval gates</h2>
        <p className="mt-1 text-xs text-muted-foreground">
          These cannot be turned off. Aether will not send, schedule, or pay without you.
        </p>
        <ul className="mt-4 space-y-2 text-sm">
          <li className="flex items-center justify-between">Send email <Switch defaultChecked disabled /></li>
          <li className="flex items-center justify-between">Create calendar event <Switch defaultChecked disabled /></li>
          <li className="flex items-center justify-between">Execute payment <Switch defaultChecked disabled /></li>
        </ul>
      </Card>

      <Card className="p-5">
        <h2 className="text-sm font-semibold">Session</h2>
        <div className="mt-3 space-y-2 text-sm">
          <div className="flex items-center justify-between">
            <span>Current device — Chrome on macOS</span>
            <span className="text-xs text-muted-foreground">Active now</span>
          </div>
          <div className="flex items-center justify-between">
            <span>iPhone — Safari</span>
            <Button size="sm" variant="ghost" className="text-destructive">Revoke</Button>
          </div>
        </div>
      </Card>

      <Card className="p-5">
        <h2 className="text-sm font-semibold">Danger zone</h2>
        <div className="mt-3 flex gap-2">
          <Button variant="outline">Export data</Button>
          <Button variant="destructive">Delete workspace</Button>
        </div>
      </Card>
    </div>
  );
}
