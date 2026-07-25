import type { ResearchResponse } from "@/lib/types/research";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

/**
 * Build auth headers consistent with other pages (calendar, replies, etc.)
 * Takes a token from Clerk's useAuth().getToken() — passed in by the caller.
 */
function buildHeaders(token: string | null): Record<string, string> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  } else {
    headers["Authorization"] = `Bearer dev-token-nathsubhankar57@gmail.com`;
  }
  return headers;
}

/**
 * Run market research for a company.
 * POST /research/run → FastAPI backend
 */
export async function runResearch(
  company: string,
  token: string | null,
  context?: string
): Promise<ResearchResponse> {
  const headers = buildHeaders(token);

  const res = await fetch(`${API_URL}/research/run`, {
    method: "POST",
    headers,
    body: JSON.stringify({
      company: company.trim(),
      ...(context ? { context: context.trim() } : {}),
    }),
  });

  if (!res.ok) {
    const errorBody = await res.json().catch(() => null);
    const message =
      errorBody?.detail ||
      errorBody?.error?.message ||
      `Research failed with status ${res.status}`;
    throw new Error(message);
  }

  return res.json();
}

/**
 * Look up an existing research result (or trigger fresh research).
 * GET /research/result?company=...&context=...
 */
export async function getResearchResult(
  company: string,
  token: string | null,
  context?: string
): Promise<ResearchResponse> {
  const headers = buildHeaders(token);
  const params = new URLSearchParams({ company: company.trim() });
  if (context) params.set("context", context.trim());

  const res = await fetch(`${API_URL}/research/result?${params}`, {
    method: "GET",
    headers,
  });

  if (!res.ok) {
    const errorBody = await res.json().catch(() => null);
    const message =
      errorBody?.detail ||
      errorBody?.error?.message ||
      `Research lookup failed with status ${res.status}`;
    throw new Error(message);
  }

  return res.json();
}
