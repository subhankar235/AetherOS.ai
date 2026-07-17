import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { events } from "@/lib/mock-data";
import { Calendar as CalendarIcon, Clock, ShieldCheck, Users } from "lucide-react";

export default function CalendarPage() {
  return (
    <div className="mx-auto max-w-5xl space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Calendar</h1>
        <p className="text-sm text-muted-foreground">
          Draft meetings from email context. Every event needs your approval.
        </p>
      </div>

      <div className="grid gap-3 md:grid-cols-3">
        <Card className="p-4">
          <div className="text-xs text-muted-foreground">This week</div>
          <div className="mt-2 text-2xl font-semibold">{events.length}</div>
        </Card>
        <Card className="p-4">
          <div className="text-xs text-muted-foreground">Pending approval</div>
          <div className="mt-2 text-2xl font-semibold">
            {events.filter((e) => e.status === "pending_approval").length}
          </div>
        </Card>
        <Card className="p-4">
          <div className="text-xs text-muted-foreground">Confirmed</div>
          <div className="mt-2 text-2xl font-semibold">
            {events.filter((e) => e.status === "confirmed").length}
          </div>
        </Card>
      </div>

      <div className="space-y-3">
        {events.map((e) => (
          <Card key={e.id} className="p-5">
            <div className="flex items-start justify-between gap-4">
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <CalendarIcon className="h-4 w-4 text-primary" />
                  <span className="font-medium">{e.title}</span>
                  {e.status === "pending_approval" ? (
                    <Badge variant="outline" className="border-accent/40 text-accent">
                      <ShieldCheck className="mr-1 h-3 w-3" /> Awaiting approval
                    </Badge>
                  ) : (
                    <Badge variant="secondary">Confirmed</Badge>
                  )}
                </div>
                <div className="mt-2 flex flex-wrap gap-4 text-xs text-muted-foreground">
                  <span className="inline-flex items-center gap-1">
                    <Clock className="h-3 w-3" /> {new Date(e.start).toLocaleString()} –{" "}
                    {new Date(e.end).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                  </span>
                  <span className="inline-flex items-center gap-1">
                    <Users className="h-3 w-3" /> {e.attendees.join(", ")}
                  </span>
                </div>
                <div className="mt-1 text-xs text-muted-foreground">Source: {e.source}</div>
              </div>
              {e.status === "pending_approval" && (
                <div className="flex gap-2">
                  <Button size="sm">Confirm</Button>
                  <Button size="sm" variant="outline">Edit time</Button>
                  <Button size="sm" variant="ghost">Discard</Button>
                </div>
              )}
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}
