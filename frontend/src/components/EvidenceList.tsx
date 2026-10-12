import { CheckCircle2, CircleSlash, HelpCircle, MinusCircle } from "lucide-react";
import type { Evidence } from "../api/types";
import { humanize } from "../lib/format";
import { Badge, ExternalLink } from "./ui";

const CONSISTENCY = {
  supports: { icon: CheckCircle2, cls: "text-status-good", label: "Supports" },
  mixed: { icon: MinusCircle, cls: "text-amber-600", label: "Mixed" },
  conflicting: { icon: CircleSlash, cls: "text-status-critical", label: "Conflicting" },
} as const;

export function ConsistencyLabel({ value }: { value: string | null }) {
  const c = value ? CONSISTENCY[value as keyof typeof CONSISTENCY] : null;
  if (!c) {
    return <span className="inline-flex items-center gap-1 text-xs text-slate-500" title="No curated consistency annotation">
      <HelpCircle className="h-3.5 w-3.5" aria-hidden /> Not annotated</span>;
  }
  const Icon = c.icon;
  return <span className="inline-flex items-center gap-1 text-xs font-medium text-slate-700">
    <Icon className={`h-3.5 w-3.5 ${c.cls}`} aria-hidden /> {c.label}</span>;
}

/** Evidence records with provenance: source, record ID, retrieval date and link. */
export function EvidenceList({ evidence }: { evidence: Evidence[] }) {
  if (evidence.length === 0) {
    return <p className="rounded-md border border-dashed border-slate-300 p-3 text-sm text-slate-500">
      No evidence records are stored for this association. It is flagged in the evidence-gap analysis.</p>;
  }
  return (
    <ul className="space-y-2">
      {evidence.map((e) => (
        <li key={e.evidence_id} className="rounded-lg border border-slate-200 p-3 text-sm">
          <div className="flex flex-wrap items-center gap-2">
            {e.evidence_type ? <Badge className="bg-navy-50 text-navy-800 ring-navy-200">{humanize(e.evidence_type)}</Badge>
              : <Badge className="bg-slate-50 text-slate-500 ring-slate-200" title="Evidence type not specified">type unspecified</Badge>}
            <Badge>{e.source_name}</Badge>
            <ConsistencyLabel value={e.consistency_annotation} />
          </div>
          {e.publication && (
            <p className="mt-1.5 font-medium text-slate-900">
              {e.publication.title}{" "}
              <span className="font-normal text-slate-500">
                {e.publication.authors?.split(",")[0]} et al. {e.publication.journal} {e.publication.publication_year}
              </span>
            </p>
          )}
          {e.evidence_summary && <p className="mt-1 text-slate-700">{e.evidence_summary}</p>}
          <div className="mt-1.5 flex flex-wrap gap-x-4 gap-y-1 text-xs text-slate-500">
            {e.source_record_id && <span>Record: {e.source_record_id}</span>}
            {e.publication?.doi && <span>DOI: {e.publication.doi}</span>}
            <span>Retrieved: {e.retrieved_at ? e.retrieved_at.slice(0, 10) : "not recorded"}</span>
            {e.source_url && <ExternalLink href={e.source_url}>Source</ExternalLink>}
          </div>
        </li>
      ))}
    </ul>
  );
}
