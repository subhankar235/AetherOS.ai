import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { knowledgeDocs } from "@/lib/mock-data";
import { BookOpen, Upload, Search } from "lucide-react";

export default function KnowledgePage() {
  return (
    <div className="mx-auto max-w-5xl space-y-6">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Knowledge Base</h1>
          <p className="text-sm text-muted-foreground">
            Aether's RAG index — powers Knowledge Agent answers and grounded reply tone.
          </p>
        </div>
        <Button>
          <Upload className="mr-1.5 h-4 w-4" /> Upload docs
        </Button>
      </div>

      <Card className="p-4">
        <div className="flex items-center gap-2">
          <Search className="h-4 w-4 text-muted-foreground" />
          <Input placeholder="Ask a question about your company knowledge…" />
          <Button>Ask</Button>
        </div>
        <div className="mt-3 rounded-md border border-primary/30 bg-primary/5 p-3 text-sm">
          <span className="text-primary">Aether:</span> Ready to answer from{" "}
          {knowledgeDocs.reduce((a, d) => a + d.chunks, 0)} indexed chunks across{" "}
          {knowledgeDocs.length} documents.
        </div>
      </Card>

      <div className="grid gap-3 md:grid-cols-2">
        {knowledgeDocs.map((d) => (
          <Card key={d.id} className="p-4">
            <div className="flex items-start gap-3">
              <div className="rounded-md bg-primary/10 p-2 text-primary">
                <BookOpen className="h-4 w-4" />
              </div>
              <div className="flex-1">
                <div className="font-medium">{d.title}</div>
                <div className="text-xs text-muted-foreground">
                  {d.source} · updated {d.updatedAt} · {d.chunks} chunks
                </div>
                <div className="mt-2 flex flex-wrap gap-1">
                  {d.tags.map((t) => (
                    <Badge key={t} variant="secondary" className="text-[10px]">
                      {t}
                    </Badge>
                  ))}
                </div>
              </div>
              <Button size="sm" variant="ghost">Reindex</Button>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}
