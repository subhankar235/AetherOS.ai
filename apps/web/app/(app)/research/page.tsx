"use client";

import { useState, useCallback } from "react";
import { useAuth } from "@clerk/nextjs";
import { motion, AnimatePresence } from "framer-motion";
import {
  Search,
  Loader2,
  CheckCircle2,
  AlertTriangle,
  Clock,
  ExternalLink,
  Zap,
  Globe,
  TrendingUp,
  Users,
  FileText,
  ShieldAlert,
  Newspaper,
  Target,
  ArrowRight,
  RefreshCw,
  HelpCircle,
  Sparkles,
  ChevronRight,
} from "lucide-react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { runResearch } from "@/lib/api/research";
import {
  type ResearchResponse,
  type ResearchReportResult,
  type SwotData,
  type SourceReference,
  isCompletedReport,
  isDisambiguation,
  parseSwotAnalysis,
  collectAllSources,
} from "@/lib/types/research";

/* ------------------------------------------------------------------ */
/* State types                                                        */
/* ------------------------------------------------------------------ */
type PageState = "idle" | "loading" | "completed" | "error" | "disambiguation";

interface ReportEntry {
  company: string;
  result: ResearchReportResult;
  fromCache: boolean;
  generatedAt: string;
}

/* ------------------------------------------------------------------ */
/* Animation variants                                                  */
/* ------------------------------------------------------------------ */
const fadeUp = {
  initial: { opacity: 0, y: 18 },
  animate: { opacity: 1, y: 0 },
  exit: { opacity: 0, y: -10 },
};

const staggerContainer = {
  animate: { transition: { staggerChildren: 0.07 } },
};

/* ------------------------------------------------------------------ */
/* Skeleton Loader                                                     */
/* ------------------------------------------------------------------ */
function ReportSkeleton() {
  return (
    <div className="space-y-4 mt-6">
      {[1, 2, 3, 4, 5].map((i) => (
        <Card key={i} className="p-5">
          <div className="space-y-3 animate-pulse">
            <div className="h-4 w-1/3 rounded bg-muted" />
            <div className="space-y-2">
              <div className="h-3 w-full rounded bg-muted/60" />
              <div className="h-3 w-5/6 rounded bg-muted/60" />
              <div className="h-3 w-4/6 rounded bg-muted/40" />
            </div>
          </div>
        </Card>
      ))}
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* SWOT Grid                                                           */
/* ------------------------------------------------------------------ */
function SwotGrid({ data }: { data: SwotData }) {
  const quadrants = [
    {
      title: "Strengths",
      items: data.strengths,
      color: "text-emerald-400",
      bg: "bg-emerald-500/10",
      border: "border-emerald-500/20",
      icon: TrendingUp,
    },
    {
      title: "Weaknesses",
      items: data.weaknesses,
      color: "text-amber-400",
      bg: "bg-amber-500/10",
      border: "border-amber-500/20",
      icon: AlertTriangle,
    },
    {
      title: "Opportunities",
      items: data.opportunities,
      color: "text-blue-400",
      bg: "bg-blue-500/10",
      border: "border-blue-500/20",
      icon: Target,
    },
    {
      title: "Threats",
      items: data.threats,
      color: "text-red-400",
      bg: "bg-red-500/10",
      border: "border-red-500/20",
      icon: ShieldAlert,
    },
  ];

  return (
    <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
      {quadrants.map((q) => (
        <div
          key={q.title}
          className={`rounded-lg border ${q.border} ${q.bg} p-4`}
        >
          <div className={`mb-2 flex items-center gap-2 text-sm font-semibold ${q.color}`}>
            <q.icon className="h-4 w-4" />
            {q.title}
          </div>
          {q.items.length > 0 ? (
            <ul className="space-y-1.5">
              {q.items.map((item, i) => (
                <li
                  key={i}
                  className="flex gap-2 text-[13px] leading-relaxed text-foreground/80"
                >
                  <ChevronRight className={`mt-0.5 h-3 w-3 shrink-0 ${q.color}`} />
                  <span>{item}</span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-xs text-muted-foreground italic">No data found</p>
          )}
        </div>
      ))}
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* Report Section Component                                            */
/* ------------------------------------------------------------------ */
function ReportSection({
  icon: Icon,
  title,
  content,
  accentColor = "text-primary",
  delay = 0,
}: {
  icon: React.ComponentType<{ className?: string }>;
  title: string;
  content: string;
  accentColor?: string;
  delay?: number;
}) {
  if (!content || content === "No data found.") return null;

  // Clean inline source references for display — replace [url @ ts] with subtle timestamp
  const formattedContent = content.replace(
    /\[([^\]\s@]+)\s*@\s*([^\]]+)\]/g,
    "⌞$2⌝"
  );

  return (
    <motion.div
      variants={fadeUp}
      initial="initial"
      animate="animate"
      transition={{ delay, duration: 0.4 }}
    >
      <Card className="p-5">
        <div className={`mb-3 flex items-center gap-2 font-semibold ${accentColor}`}>
          <Icon className="h-4 w-4" />
          {title}
        </div>
        <div className="text-sm leading-relaxed text-foreground/80 whitespace-pre-line">
          {formattedContent}
        </div>
      </Card>
    </motion.div>
  );
}

/* ------------------------------------------------------------------ */
/* Sources Panel                                                       */
/* ------------------------------------------------------------------ */
function SourcesPanel({ sources }: { sources: SourceReference[] }) {
  if (sources.length === 0) return null;

  return (
    <motion.div variants={fadeUp} initial="initial" animate="animate" transition={{ delay: 0.6 }}>
      <Card className="p-5">
        <div className="mb-3 flex items-center gap-2 font-semibold text-muted-foreground">
          <ExternalLink className="h-4 w-4" />
          Sources &amp; Timestamps
        </div>
        <div className="space-y-2">
          {sources.map((src, i) => (
            <div
              key={i}
              className="flex items-start gap-3 rounded-md border border-border/50 bg-muted/20 px-3 py-2 text-xs"
            >
              <Globe className="mt-0.5 h-3.5 w-3.5 shrink-0 text-primary/60" />
              <div className="min-w-0 flex-1">
                <a
                  href={src.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="block truncate font-medium text-primary hover:underline"
                >
                  {src.url}
                </a>
                <span className="text-muted-foreground">
                  <Clock className="mr-1 inline h-3 w-3" />
                  {src.timestamp}
                </span>
              </div>
            </div>
          ))}
        </div>
      </Card>
    </motion.div>
  );
}

/* ================================================================== */
/* Main Research Page                                                  */
/* ================================================================== */
export default function ResearchPage() {
  const { getToken } = useAuth();

  const [company, setCompany] = useState("");
  const [context, setContext] = useState("");
  const [state, setState] = useState<PageState>("idle");
  const [report, setReport] = useState<ResearchReportResult | null>(null);
  const [fromCache, setFromCache] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [disambiguation, setDisambiguation] = useState<string | null>(null);
  const [history, setHistory] = useState<ReportEntry[]>([]);
  const [searchedCompany, setSearchedCompany] = useState("");


  const handleResearch = useCallback(
    async (overrideContext?: string) => {
      const companyName = company.trim();
      if (!companyName) return;

      setState("loading");
      setError(null);
      setReport(null);
      setDisambiguation(null);
      setFromCache(false);
      setSearchedCompany(companyName);

      try {
        const token = await getToken();
        const res: ResearchResponse = await runResearch(
          companyName,
          token,
          overrideContext || context || undefined
        );

        if (isDisambiguation(res)) {
          setState("disambiguation");
          setDisambiguation(res.result.clarification as string);
          return;
        }

        if (isCompletedReport(res)) {
          const result = res.result as unknown as ResearchReportResult;
          setReport(result);
          setFromCache(!!res._from_cache || !!res._cache_hit);
          setState("completed");

          // Add to history
          setHistory((prev) => {
            const filtered = prev.filter(
              (h) => h.company.toLowerCase() !== companyName.toLowerCase()
            );
            return [
              {
                company: companyName,
                result,
                fromCache: !!res._from_cache || !!res._cache_hit,
                generatedAt: result.report_date || new Date().toISOString(),
              },
              ...filtered,
            ].slice(0, 10);
          });
          return;
        }

        // Unknown status — treat as error
        setState("error");
        setError("Received an unexpected response from the research agent.");
      } catch (err: unknown) {
        setState("error");
        setError(err instanceof Error ? err.message : "An unexpected error occurred");
      }
    },
    [company, context, getToken]
  );

  const handleDisambiguationSubmit = useCallback(() => {
    if (context.trim()) {
      handleResearch(context.trim());
    }
  }, [context, handleResearch]);

  const handleRetry = useCallback(() => {
    handleResearch();
  }, [handleResearch]);

  const handleHistoryClick = useCallback(
    (entry: ReportEntry) => {
      setCompany(entry.company);
      setReport(entry.result);
      setFromCache(entry.fromCache);
      setSearchedCompany(entry.company);
      setState("completed");
    },
    []
  );

  // Parse SWOT + sources from the current report
  const swotData = report ? parseSwotAnalysis(report.swot_analysis) : null;
  const sources = report ? collectAllSources(report) : [];

  return (
    <div className="mx-auto max-w-5xl space-y-6 pb-12">
      {/* ── Header ── */}
      <div>
        <h1 className="text-2xl font-semibold flex items-center gap-2">
          <Sparkles className="h-6 w-6 text-primary" />
          Market Research
        </h1>
        <p className="text-sm text-muted-foreground">
          AI-powered company research — web search, synthesis, SWOT, and competitive analysis
        </p>
      </div>

      {/* ── Search Bar ── */}
      <Card className="p-4">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-end">
          <div className="flex-1 space-y-1">
            <label htmlFor="research-company" className="text-xs font-medium text-muted-foreground">
              Company
            </label>
            <Input
              autoFocus
              id="research-company"
              placeholder="e.g. Stripe, Notion, Linear…"
              value={company}
              onChange={(e) => setCompany(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleResearch()}
              disabled={state === "loading"}
            />
          </div>
          <div className="sm:w-52 space-y-1">
            <label htmlFor="research-context" className="text-xs font-medium text-muted-foreground">
              Context{" "}
              <span className="text-muted-foreground/60">(optional)</span>
            </label>
            <Input
              id="research-context"
              placeholder="e.g. fintech, SaaS…"
              value={context}
              onChange={(e) => setContext(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleResearch()}
              disabled={state === "loading"}
            />
          </div>
          <Button
            onClick={() => handleResearch()}
            disabled={state === "loading" || !company.trim()}
            className="sm:w-auto shrink-0"
          >
            {state === "loading" ? (
              <>
                <Loader2 className="mr-1.5 h-4 w-4 animate-spin" />
                Researching…
              </>
            ) : (
              <>
                <Search className="mr-1.5 h-4 w-4" />
                Run report
              </>
            )}
          </Button>
        </div>
      </Card>

      {/* ── Loading ── */}
      <AnimatePresence mode="wait">
        {state === "loading" && (
          <motion.div
            key="loading"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
          >
            <Card className="p-6">
              <div className="flex flex-col items-center gap-4 py-8 text-center">
                <div className="relative">
                  <div className="absolute -inset-4 rounded-full bg-primary/10 animate-ping" />
                  <Loader2 className="h-8 w-8 animate-spin text-primary relative" />
                </div>
                <div>
                  <p className="font-medium">
                    Researching {searchedCompany}…
                  </p>
                  <p className="mt-1 text-xs text-muted-foreground">
                    Searching the web, crawling sources, and synthesizing insights
                  </p>
                </div>
                <div className="flex gap-6 text-[11px] text-muted-foreground mt-2">
                  <span className="flex items-center gap-1">
                    <Globe className="h-3 w-3" /> Web search
                  </span>
                  <span className="flex items-center gap-1">
                    <FileText className="h-3 w-3" /> Crawling pages
                  </span>
                  <span className="flex items-center gap-1">
                    <Sparkles className="h-3 w-3" /> AI synthesis
                  </span>
                </div>
              </div>
            </Card>
            <ReportSkeleton />
          </motion.div>
        )}

        {/* ── Disambiguation ── */}
        {state === "disambiguation" && disambiguation && (
          <motion.div key="disambig" {...fadeUp}>
            <Card className="border-amber-500/30 bg-amber-500/5 p-5">
              <div className="flex items-start gap-3">
                <div className="rounded-full bg-amber-500/20 p-2">
                  <HelpCircle className="h-5 w-5 text-amber-400" />
                </div>
                <div className="flex-1 space-y-3">
                  <div>
                    <p className="font-medium text-amber-300">
                      Disambiguation needed
                    </p>
                    <p className="mt-1 text-sm text-foreground/80">
                      {disambiguation}
                    </p>
                  </div>
                  <div className="flex gap-2">
                    <Input
                      placeholder="Provide context to clarify…"
                      value={context}
                      onChange={(e) => setContext(e.target.value)}
                      onKeyDown={(e) =>
                        e.key === "Enter" && handleDisambiguationSubmit()
                      }
                      className="max-w-sm"
                      autoFocus
                    />
                    <Button
                      onClick={handleDisambiguationSubmit}
                      disabled={!context.trim()}
                      size="sm"
                    >
                      <ArrowRight className="mr-1 h-4 w-4" />
                      Clarify
                    </Button>
                  </div>
                </div>
              </div>
            </Card>
          </motion.div>
        )}

        {/* ── Error ── */}
        {state === "error" && error && (
          <motion.div key="error" {...fadeUp}>
            <Card className="border-destructive/30 bg-destructive/5 p-5">
              <div className="flex items-start gap-3">
                <div className="rounded-full bg-destructive/20 p-2">
                  <AlertTriangle className="h-5 w-5 text-destructive" />
                </div>
                <div className="flex-1">
                  <p className="font-medium text-destructive">
                    Research failed
                  </p>
                  <p className="mt-1 text-sm text-foreground/70">{error}</p>
                  <Button
                    variant="outline"
                    size="sm"
                    className="mt-3"
                    onClick={handleRetry}
                  >
                    <RefreshCw className="mr-1.5 h-3.5 w-3.5" />
                    Retry
                  </Button>
                </div>
              </div>
            </Card>
          </motion.div>
        )}

        {/* ── Completed Report ── */}
        {state === "completed" && report && (
          <motion.div
            key="report"
            variants={staggerContainer}
            initial="initial"
            animate="animate"
            className="space-y-4"
          >
            {/* Report Header */}
            <motion.div variants={fadeUp}>
              <Card className="border-primary/20 bg-primary/5 p-5">
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div className="flex items-center gap-3">
                    <div className="rounded-lg bg-primary/20 p-2.5">
                      <Globe className="h-5 w-5 text-primary" />
                    </div>
                    <div>
                      <h2 className="text-lg font-semibold">{searchedCompany}</h2>
                      <div className="flex items-center gap-2 text-xs text-muted-foreground">
                        <Clock className="h-3 w-3" />
                        Report generated {report.report_date}
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    {fromCache && (
                      <Badge
                        variant="secondary"
                        className="border-amber-500/30 bg-amber-500/10 text-amber-400"
                      >
                        <Zap className="mr-1 h-3 w-3" />
                        Cached
                      </Badge>
                    )}
                    <Badge variant="secondary" className="border-emerald-500/30 bg-emerald-500/10 text-emerald-400">
                      <CheckCircle2 className="mr-1 h-3 w-3" />
                      Completed
                    </Badge>
                  </div>
                </div>
              </Card>
            </motion.div>

            {/* Executive Summary */}
            <ReportSection
              icon={FileText}
              title="Executive Summary"
              content={report.executive_summary}
              accentColor="text-primary"
              delay={0.08}
            />

            {/* Company Overview */}
            <ReportSection
              icon={Globe}
              title="Company Overview"
              content={report.company_overview}
              accentColor="text-blue-400"
              delay={0.15}
            />

            {/* SWOT Analysis */}
            {swotData && (
              <motion.div
                variants={fadeUp}
                initial="initial"
                animate="animate"
                transition={{ delay: 0.22 }}
              >
                <Card className="p-5">
                  <div className="mb-4 flex items-center gap-2 font-semibold text-purple-400">
                    <Target className="h-4 w-4" />
                    SWOT Analysis
                  </div>
                  <SwotGrid data={swotData} />
                </Card>
              </motion.div>
            )}

            {/* Competitors */}
            <ReportSection
              icon={Users}
              title="Competitors"
              content={report.competitors}
              accentColor="text-cyan-400"
              delay={0.29}
            />

            {/* Recent News */}
            <ReportSection
              icon={Newspaper}
              title="Recent News"
              content={report.recent_news}
              accentColor="text-sky-400"
              delay={0.36}
            />

            {/* Opportunities */}
            <ReportSection
              icon={TrendingUp}
              title="Opportunities"
              content={report.opportunities}
              accentColor="text-emerald-400"
              delay={0.43}
            />

            {/* Risks */}
            <ReportSection
              icon={ShieldAlert}
              title="Risks & Challenges"
              content={report.risks}
              accentColor="text-red-400"
              delay={0.50}
            />

            {/* Sources */}
            <SourcesPanel sources={sources} />
          </motion.div>
        )}
      </AnimatePresence>

      {/* ── Recent Reports (History) ── */}
      {history.length > 0 && state !== "loading" && (
        <div className="space-y-3">
          <h3 className="text-sm font-medium text-muted-foreground">
            Recent Reports
          </h3>
          <div className="grid gap-2 sm:grid-cols-2">
            {history.map((entry) => (
              <Card
                key={entry.company}
                className="group cursor-pointer p-4 transition-colors hover:border-primary/30 hover:bg-primary/5"
                onClick={() => handleHistoryClick(entry)}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Globe className="h-4 w-4 text-muted-foreground group-hover:text-primary transition-colors" />
                    <span className="font-medium">{entry.company}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    {entry.fromCache && (
                      <Zap className="h-3 w-3 text-amber-400" />
                    )}
                    <Badge variant="secondary" className="text-[10px]">
                      <CheckCircle2 className="mr-1 h-2.5 w-2.5" />
                      Done
                    </Badge>
                  </div>
                </div>
                <p className="mt-1.5 line-clamp-2 text-xs text-muted-foreground">
                  {entry.result.executive_summary.slice(0, 120)}…
                </p>
                <div className="mt-1.5 text-[10px] text-muted-foreground/60">
                  <Clock className="mr-0.5 inline h-2.5 w-2.5" />
                  {entry.generatedAt}
                </div>
              </Card>
            ))}
          </div>
        </div>
      )}

      {/* ── Empty State ── */}
      {state === "idle" && history.length === 0 && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.2 }}>
          <Card className="p-8">
            <div className="flex flex-col items-center gap-4 text-center">
              <div className="rounded-2xl bg-primary/10 p-4">
                <Search className="h-8 w-8 text-primary" />
              </div>
              <div>
                <p className="font-medium">No research reports yet</p>
                <p className="mt-1 text-sm text-muted-foreground">
                  Enter a company name above to generate an AI-powered market research report
                  with SWOT analysis, competitor insights, and more.
                </p>
              </div>
              <div className="flex flex-wrap justify-center gap-2 mt-2">
                {["Stripe", "Notion", "Linear", "Vercel"].map((name) => (
                  <Button
                    key={name}
                    variant="outline"
                    size="sm"
                    onClick={() => {
                      setCompany(name);
                      document.getElementById("research-company")?.focus();
                    }}
                    className="text-xs"
                  >
                    {name}
                  </Button>
                ))}
              </div>
            </div>
          </Card>
        </motion.div>
      )}
    </div>
  );
}
