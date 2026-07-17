import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { auditLog } from "@/lib/mock-data";

export default function AuditPage() {
  return (
    <div className="mx-auto max-w-5xl space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Audit Log</h1>
        <p className="text-sm text-muted-foreground">
          Every consequential action, who approved it, and when.
        </p>
      </div>

      <Card className="p-0">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Time</TableHead>
              <TableHead>Agent</TableHead>
              <TableHead>Action</TableHead>
              <TableHead>Target</TableHead>
              <TableHead>Approved by</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {auditLog.map((a) => (
              <TableRow key={a.id}>
                <TableCell className="text-xs text-muted-foreground">
                  {new Date(a.at).toLocaleString()}
                </TableCell>
                <TableCell>
                  <Badge variant="secondary">{a.actor}</Badge>
                </TableCell>
                <TableCell className="font-mono text-xs">{a.action}</TableCell>
                <TableCell className="text-sm">{a.target}</TableCell>
                <TableCell>
                  <Badge variant={a.approvedBy === "user" ? "default" : "outline"}>
                    {a.approvedBy}
                  </Badge>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </Card>
    </div>
  );
}
