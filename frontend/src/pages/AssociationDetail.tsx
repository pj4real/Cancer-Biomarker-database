import { Link, useParams } from "react-router-dom";
import type { Association, GapItem } from "../api/types";
import { EvidenceList } from "../components/EvidenceList";
import { ScoreBreakdown } from "../components/ScoreBreakdown";
import { AsyncBlock, Badge, Card, Disclaimer, PageHeader, RoleBadge, SourceStatusBadge } from "../components/ui";
import { useApi } from "../lib/useApi";

interface AssociationFull extends Association {
  score_explanation: { method: string; n_evidence: number };
  gap_analysis: GapItem;
}

export default function AssociationDetail() {
  const { id } = useParams();
  const state = useApi<AssociationFull>(`/associations/${id}`);
  const vocab = useApi<{ gap_flags: Record<string, string> }>("/meta/vocabularies");
  return (
    <AsyncBlock state={state}>
      {(a) => (
        <div className="space-y-5">
          <PageHeader
            title={`${a.biomarker.name} — ${a.cancer.name}`}
            subtitle={<span className="flex flex-wrap items-center gap-2"><RoleBadge role={a.biomarker_role} /><SourceStatusBadge status={a.source_status} />
              <Link to={`/biomarkers/${a.biomarker.biomarker_id}`} className="text-teal-brand hover:underline">Biomarker page</Link>
              <Link to={`/cancers/${a.cancer.cancer_id}`} className="text-teal-brand hover:underline">Cancer page</Link></span>}
          />
          <div className="grid gap-5 lg:grid-cols-[1fr_360px]">
            <Card title={`Evidence records (${a.evidence?.length ?? 0})`}>
              {a.association_description && <p className="mb-3 text-sm text-slate-700">{a.association_description}</p>}
              <EvidenceList evidence={a.evidence ?? []} />
            </Card>
            <div className="space-y-5">
              <Card title="Evidence-support score"><ScoreBreakdown score={a.score} />
                <p className="mt-3 border-t border-slate-100 pt-2 text-xs text-slate-600"><strong>Method:</strong> {a.score_explanation.method}</p>
                <Link to="/methodology" className="mt-1 inline-block text-xs text-teal-brand hover:underline">How the score is calculated</Link>
              </Card>
              <Card title="Evidence gaps">
                {a.gap_analysis.flags.length === 0 ? <p className="text-sm text-slate-600">No gaps flagged.</p> : (
                  <ul className="space-y-2 text-sm">
                    {a.gap_analysis.flags.map((f) => (
                      <li key={f}><Badge className="bg-amber-50 text-amber-900 ring-amber-200">{f.replace(/_/g, " ")}</Badge>
                        <p className="mt-0.5 text-xs text-slate-600">{vocab.data?.gap_flags[f]}</p></li>
                    ))}
                  </ul>
                )}
              </Card>
            </div>
          </div>
          <Disclaimer />
        </div>
      )}
    </AsyncBlock>
  );
}
