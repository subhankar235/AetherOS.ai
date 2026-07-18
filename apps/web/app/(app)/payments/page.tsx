import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { payments } from "@/lib/mock-data";
import { AlertTriangle, CheckCircle2, ShieldAlert, ShieldCheck } from "lucide-react";

export default function PaymentsPage() {
  return (
    <div className="mx-auto max-w-5xl space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Payment Agent</h1>
        <p className="text-sm text-muted-foreground">
          Scaffold only — every payment shows policy + fraud checks and blocks on approval.
        </p>
      </div>

      <div className="space-y-3">
        {payments.map((p) => (
          <Card
            key={p.id}
            className={`p-5 ${p.status === "flagged" ? "border-destructive/40" : ""}`}
          >
            <div className="flex flex-wrap items-start justify-between gap-4">
              <div>
                <div className="flex items-center gap-2">
                  <span className="font-medium">{p.vendor}</span>
                  <Badge variant="outline">{p.invoiceRef}</Badge>
                  {p.status === "paid" && (
                    <Badge variant="secondary">
                      <CheckCircle2 className="mr-1 h-3 w-3" /> Paid
                    </Badge>
                  )}
                  {p.status === "flagged" && (
                    <Badge variant="destructive">
                      <ShieldAlert className="mr-1 h-3 w-3" /> Flagged
                    </Badge>
                  )}
                  {p.status === "pending_approval" && (
                    <Badge variant="outline" className="border-accent/40 text-accent">
                      <ShieldCheck className="mr-1 h-3 w-3" /> Awaiting approval
                    </Badge>
                  )}
                </div>
                <div className="mt-1 text-2xl font-semibold">
                  ${p.amount.toLocaleString()} {p.currency}
                </div>
                <div className="text-xs text-muted-foreground">Due {p.dueDate}</div>
              </div>
              <div className="text-right">
                <div className="text-xs text-muted-foreground">Fraud score</div>
                <div
                  className={`text-xl font-semibold ${
                    p.fraudScore > 40 ? "text-destructive" : ""
                  }`}
                >
                  {p.fraudScore}/100
                </div>
              </div>
            </div>

            <div className="mt-4 space-y-1">
              {p.policyChecks.map((c, i) => (
                <div key={i} className="flex items-center gap-2 text-sm">
                  {c.passed ? (
                    <CheckCircle2 className="h-4 w-4 text-primary" />
                  ) : (
                    <AlertTriangle className="h-4 w-4 text-destructive" />
                  )}
                  <span className={c.passed ? "" : "text-destructive"}>{c.label}</span>
                </div>
              ))}
            </div>

            {p.status !== "paid" && (
              <div className="mt-4 flex gap-2">
                <Button
                  size="sm"
                  disabled={p.status === "flagged"}
                  variant={p.status === "flagged" ? "outline" : "default"}
                >
                  Approve payment
                </Button>
                <Button size="sm" variant="outline">Request more info</Button>
                <Button size="sm" variant="ghost" className="text-destructive">
                  Reject
                </Button>
              </div>
            )}
          </Card>
        ))}
      </div>
    </div>
  );
}
