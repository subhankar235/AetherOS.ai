import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { reports } from "@/lib/mock-data";
import { Search, Loader2, CheckCircle2 } from "lucide-react";

export default function ResearchPage() {
  return (
    <div className="mx-auto max-w-5xl space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Market Research Agent</h1>
        <p className="text-sm text-muted-foreground">
          Pull a company briefing before you reply — Aether synthesizes web + private notes.
        </p>
      </div>

      <Card className="p-4">
        <div className="flex gap-2">
          <Input placeholder="Research a company, e.g. 'BigCo Inc.'" />
          <Button>
            <Search className="mr-1.5 h-4 w-4" /> Run report
          </Button>
        </div>
      </Card>

      <div className="space-y-3">
        {reports.map((r) => (
          <Card key={r.id} className="p-5">
            <div className="flex items-start justify-between">
              <div>
                <div className="flex items-center gap-2">
                  <span className="font-medium">{r.company}</span>
                  {r.status === "completed" ? (
                    <Badge variant="secondary">
                      <CheckCircle2 className="mr-1 h-3 w-3" /> Completed
                    </Badge>
                  ) : (
                    <Badge variant="outline">
                      <Loader2 className="mr-1 h-3 w-3 animate-spin" /> Running
                    </Badge>
                  )}
                </div>
                <div className="text-xs text-muted-foreground">Requested {r.requestedAt}</div>
              </div>
              <Button size="sm" variant="outline">Open report</Button>
            </div>
            {r.highlights.length > 0 && (
              <ul className="mt-3 space-y-1 text-sm">
                {r.highlights.map((h, i) => (
                  <li key={i} className="flex gap-2">
                    <span className="text-primary">•</span> {h}
                  </li>
                ))}
              </ul>
            )}
          </Card>
        ))}
      </div>
    </div>
  );
}
