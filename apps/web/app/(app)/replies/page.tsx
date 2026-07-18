import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { drafts, emails } from "@/lib/mock-data";
import { Sparkles, ShieldCheck } from "lucide-react";

export default function RepliesPage() {
  return (
    <div className="mx-auto max-w-5xl space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Reply Drafts</h1>
        <p className="text-sm text-muted-foreground">
          Every draft waits behind an approval gate. Aether never sends on its own.
        </p>
      </div>

      <div className="space-y-4">
        {drafts.map((d) => {
          const src = emails.find((e) => e.id === d.emailId);
          return (
            <Card key={d.id} className="p-5">
              <div className="flex items-start justify-between">
                <div>
                  <div className="flex items-center gap-2">
                    <Sparkles className="h-4 w-4 text-primary" />
                    <span className="text-sm font-medium">Draft to {d.to}</span>
                    <Badge variant="outline">{d.tone}</Badge>
                    <Badge variant="outline" className="border-accent/40 text-accent">
                      <ShieldCheck className="mr-1 h-3 w-3" /> Awaiting approval
                    </Badge>
                  </div>
                  <div className="mt-1 text-xs text-muted-foreground">
                    In reply to: <span className="text-foreground">{src?.subject}</span>
                  </div>
                </div>
                <div className="text-xs text-muted-foreground">
                  {new Date(d.createdAt).toLocaleString()}
                </div>
              </div>

              <Textarea defaultValue={d.body} rows={8} className="mt-4 font-sans text-sm" />

              <div className="mt-3 flex flex-wrap gap-2">
                <Button size="sm">Approve & send</Button>
                <Button size="sm" variant="outline">Shorten</Button>
                <Button size="sm" variant="outline">Make warmer</Button>
                <Button size="sm" variant="outline">Make formal</Button>
                <Button size="sm" variant="ghost">Regenerate</Button>
                <Button size="sm" variant="ghost" className="ml-auto text-destructive">
                  Discard
                </Button>
              </div>
            </Card>
          );
        })}
      </div>
    </div>
  );
}
