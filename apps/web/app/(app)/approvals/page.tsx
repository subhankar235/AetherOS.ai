import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { approvals } from "@/lib/mock-data";
import { Calendar, CreditCard, MessageSquare, ShieldCheck } from "lucide-react";

const kindIcon = {
  reply: MessageSquare,
  calendar: Calendar,
  payment: CreditCard,
};

export default function ApprovalsPage() {
  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Approval Queue</h1>
        <p className="text-sm text-muted-foreground">
          The single hard gate. Nothing consequential leaves this workspace without your tap.
        </p>
      </div>

      <div className="space-y-3">
        {approvals.map((a) => {
          const Icon = kindIcon[a.kind];
          return (
            <Card key={a.id} className="p-5">
              <div className="flex items-start gap-3">
                <div className="rounded-md bg-primary/10 p-2 text-primary">
                  <Icon className="h-4 w-4" />
                </div>
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <span className="font-medium">{a.summary}</span>
                    <Badge variant="outline" className="border-accent/40 text-accent">
                      <ShieldCheck className="mr-1 h-3 w-3" /> Gate
                    </Badge>
                    <Badge variant="secondary">{a.agent}</Badge>
                  </div>
                  <div className="mt-1 text-sm text-muted-foreground">{a.detail}</div>
                  <div className="mt-1 text-xs text-muted-foreground">
                    Requested {new Date(a.requestedAt).toLocaleString()}
                  </div>
                </div>
                <div className="flex gap-2">
                  <Button size="sm">Approve</Button>
                  <Button size="sm" variant="outline">Modify</Button>
                  <Button size="sm" variant="ghost" className="text-destructive">
                    Reject
                  </Button>
                </div>
              </div>
            </Card>
          );
        })}
      </div>
    </div>
  );
}
