/** Mirrors Python `extract_title_body` + preview rule. Unit-tested. */
export function extractTitle(text: string): string {
  const lines = (text || "").trim().split("\n");
  let title = (lines[0] || "").trim() || "Untitled";
  if (title.length > 80) title = title.slice(0, 80);
  return title || "Untitled";
}

export function makePreview(title: string, body: string): string {
  const p = body ? body.replace(/\n/g, " ").slice(0, 120) : title.slice(0, 120);
  return p || "Untitled";
}

/** Mirrors Python FTS builder: `"word"*` per token. */
export function buildFtsQuery(query: string): string {
  return query
    .split(/\s+/)
    .filter(Boolean)
    .map((w) => `"${w.replace(/"/g, "")}"*`)
    .join(" ");
}

export function formatEdited(ts: number): string {
  const d = new Date(ts * 1000);
  return `Edited ${d.toLocaleString(undefined, { month: "short", day: "numeric" })}, ${d.toLocaleString(undefined, { hour: "2-digit", minute: "2-digit", hour12: false })}`;
}

export function wordCount(text: string): number {
  const t = (text || "").trim();
  return t ? t.split(/\s+/).length : 0;
}
