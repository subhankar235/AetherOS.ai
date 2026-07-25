// TypeScript types for the Market Research Agent responses
// Matches the backend schema from agents/research_agent/__init__.py

/** Request payload sent to POST /api/research/run */
export interface ResearchRequest {
  company: string;
  context?: string;
}

/** The structured report content returned inside a completed research response */
export interface ResearchReportResult {
  executive_summary: string;
  company_overview: string;
  swot_analysis: string;
  competitors: string;
  recent_news: string;
  opportunities: string;
  risks: string;
  report_date: string;
}

/** Disambiguation result when the company name is ambiguous */
export interface ResearchDisambiguationResult {
  clarification: string;
  company: string;
}

/** Union of possible result payloads */
export type ResearchResult = ResearchReportResult | ResearchDisambiguationResult;

/**
 * Full response from the research agent.
 * Status determines the shape of `result`:
 *  - "completed" → ResearchReportResult
 *  - "clarification_needed" → ResearchDisambiguationResult
 *  - "error" → { message: string }
 */
export interface ResearchResponse {
  agent: string;
  status: "completed" | "clarification_needed" | "error";
  result: Record<string, string>;
  context_updates: Record<string, unknown>;
  requires_approval: boolean;
  _from_cache?: boolean;
  _cache_hit?: boolean;
}

/** Typed guard to check if the response is a completed report */
export function isCompletedReport(
  res: ResearchResponse
): res is ResearchResponse & { result: ResearchReportResult } {
  return res.status === "completed" && "executive_summary" in res.result;
}

/** Typed guard to check if disambiguation is needed */
export function isDisambiguation(
  res: ResearchResponse
): res is ResearchResponse & { result: ResearchDisambiguationResult } {
  return res.status === "clarification_needed" && "clarification" in res.result;
}

/** A parsed SWOT item for rendering the grid */
export interface SwotData {
  strengths: string[];
  weaknesses: string[];
  opportunities: string[];
  threats: string[];
}

/** Parse a SWOT analysis string into structured data */
export function parseSwotAnalysis(swotText: string): SwotData {
  const data: SwotData = {
    strengths: [],
    weaknesses: [],
    opportunities: [],
    threats: [],
  };

  if (!swotText || swotText === "No data found.") return data;

  // Try to parse structured SWOT text
  // Common formats: "Strengths: ...\nWeaknesses: ..." or "**Strengths**: ..."
  const sections = swotText.split(/(?=\*{0,2}(?:Strengths|Weaknesses|Opportunities|Threats)\*{0,2}\s*:)/i);

  for (const section of sections) {
    const trimmed = section.trim();
    if (!trimmed) continue;

    const matchCategory = trimmed.match(
      /^\*{0,2}(Strengths|Weaknesses|Opportunities|Threats)\*{0,2}\s*:\s*([\s\S]*)/i
    );
    if (matchCategory) {
      const category = matchCategory[1].toLowerCase() as keyof SwotData;
      const content = matchCategory[2].trim();
      // Split by bullet points, dashes, or numbered items
      const items = content
        .split(/(?:\n|;|•|–|—|-\s)/)
        .map((item) => item.replace(/^\d+\.\s*/, "").replace(/^\*\*/, "").replace(/\*\*$/, "").trim())
        .filter((item) => item.length > 2);
      data[category] = items.length > 0 ? items : [content];
    }
  }

  // Fallback: if no structured sections found, put entire text in strengths
  if (
    data.strengths.length === 0 &&
    data.weaknesses.length === 0 &&
    data.opportunities.length === 0 &&
    data.threats.length === 0
  ) {
    data.strengths = [swotText];
  }

  return data;
}

/** Extract source references from report text (format: [url @ timestamp]) */
export interface SourceReference {
  url: string;
  timestamp: string;
  context: string;
}

export function extractSourceReferences(text: string): SourceReference[] {
  const refs: SourceReference[] = [];
  // Match patterns like [https://example.com @ 2026-07-25 12:00 UTC]
  const regex = /\[([^\]\s@]+)\s*@\s*([^\]]+)\]/g;
  let match;
  while ((match = regex.exec(text)) !== null) {
    const url = match[1];
    const timestamp = match[2].trim();
    // Get surrounding context (up to 60 chars before the match)
    const start = Math.max(0, match.index - 60);
    const context = text.slice(start, match.index).trim();
    refs.push({ url, timestamp, context });
  }
  return refs;
}

/** Collect all source references from all report sections */
export function collectAllSources(result: ResearchReportResult): SourceReference[] {
  const allText = [
    result.executive_summary,
    result.company_overview,
    result.swot_analysis,
    result.competitors,
    result.recent_news,
    result.opportunities,
    result.risks,
  ].join("\n\n");

  // Deduplicate by URL
  const refs = extractSourceReferences(allText);
  const seen = new Set<string>();
  return refs.filter((ref) => {
    if (seen.has(ref.url)) return false;
    seen.add(ref.url);
    return true;
  });
}
