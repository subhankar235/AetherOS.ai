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
import { tickets } from "@/lib/mock-data";

export default function SupportPage() {
  return (
    <div className="mx-auto max-w-5xl space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Support Agent</h1>
        <p className="text-sm text-muted-foreground">
          Aether triages customer emails into tickets and drafts responses grounded in your macros.
        </p>
      </div>

      <Card className="p-0">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Customer</TableHead>
              <TableHead>Subject</TableHead>
              <TableHead>Priority</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Updated</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {tickets.map((t) => (
              <TableRow key={t.id}>
                <TableCell className="font-medium">{t.customer}</TableCell>
                <TableCell>{t.subject}</TableCell>
                <TableCell>
                  <Badge variant="outline">{t.priority}</Badge>
                </TableCell>
                <TableCell>
                  <Badge
                    variant={t.status === "resolved" ? "secondary" : "default"}
                    className="capitalize"
                  >
                    {t.status}
                  </Badge>
                </TableCell>
                <TableCell className="text-muted-foreground">{t.updatedAt}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </Card>
    </div>
  );
}
