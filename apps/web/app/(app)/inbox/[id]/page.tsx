import Link from "next/link";
import { notFound } from "next/navigation";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { emails, drafts } from "@/lib/mock-data";
import { ArrowLeft, Calendar, MessageSquare, Sparkles } from "lucide-react";

export default async function EmailDetail({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const email = emails.find((e) => e.id === id);
  if (!email) notFound();

  const draft = drafts.find((d) => d.emailId === email.id);

  return (
    <div className="mx-auto max-w-4xl space-y-4">
      <Link href="/dashboard" className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground">
        <ArrowLeft className="h-4 w-4" /> Back to inbox
      </Link>

      <Card className="p-6">
        <div className="flex flex-wrap items-center gap-2">
          <Badge variant="outline">{email.category}</Badge>
          <Badge variant="outline" className="border-destructive/40 text-destructive">
            {email.priority}
          </Badge>
          {email.urgent && <Badge variant="destructive">urgent</Badge>}
          {email.labels.map((l: string) => (
            <Badge key={l} variant="secondary">
              {l}
            </Badge>
          ))}
        </div>
        <h1 className="mt-3 text-2xl font-semibold">{email.subject}</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          From <span className="text-foreground">{email.from}</span> &lt;{email.fromEmail}&gt; ·{" "}
          {new Date(email.receivedAt).toLocaleString()}
        </p>

        <div className="mt-4 rounded-md border border-primary/30 bg-primary/5 p-3">
          <div className="flex items-center gap-1.5 text-xs font-medium text-primary">
            <Sparkles className="h-3.5 w-3.5" /> Aether's summary
          </div>
          <p className="mt-1 text-sm">{email.summary}</p>
        </div>

        <pre className="mt-5 whitespace-pre-wrap font-sans text-sm leading-relaxed">
          {email.body}
        </pre>

        <div className="mt-6 flex flex-wrap gap-2">
          <Link
            href="/replies"
            className="inline-flex h-7 items-center justify-center gap-1 rounded-lg bg-primary px-2.5 text-[0.8rem] font-medium text-primary-foreground whitespace-nowrap transition-all hover:bg-primary/80"
          >
            <MessageSquare className="h-3.5 w-3.5" /> Draft reply
          </Link>
          <Link
            href="/calendar"
            className="inline-flex h-7 items-center justify-center gap-1 rounded-lg border border-border bg-background px-2.5 text-[0.8rem] font-medium whitespace-nowrap transition-all hover:bg-muted hover:text-foreground"
          >
            <Calendar className="h-3.5 w-3.5" /> Schedule from this
          </Link>
          <Button size="sm" variant="ghost">Archive</Button>
          <Button size="sm" variant="ghost">Mark unread</Button>
        </div>
      </Card>

      {draft && (
        <Card className="border-primary/30 bg-primary/5 p-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-1.5 text-sm font-medium text-primary">
              <Sparkles className="h-4 w-4" /> Aether already drafted a reply
            </div>
            <Badge variant="outline">Awaiting approval</Badge>
          </div>
          <pre className="mt-3 whitespace-pre-wrap rounded-md bg-background p-3 text-sm">
            {draft.body}
          </pre>
          <div className="mt-3 flex gap-2">
            <Button size="sm">Approve & send</Button>
            <Button size="sm" variant="outline">Edit tone</Button>
            <Button size="sm" variant="ghost">Discard</Button>
          </div>
        </Card>
      )}
    </div>
  );
}
