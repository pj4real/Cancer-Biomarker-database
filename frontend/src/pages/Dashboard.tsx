import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { BookOpen, Dna, FlaskConical, GitBranch, Link2, Microscope, Network, Shapes } from "lucide-react";
import type { Cancer, DashboardStats, Vocabularies } from "../api/types";
import { ChartCard, HBar, VBar, histogramData } from "../components/charts";
import { AsyncBlock, Card, Disclaimer, PageHeader, ScoreStatusLabel, Select, StatTile } from "../components/ui";
import { humanize } from "../lib/format";
import { useApi } from "../lib/useApi";

export default function Dashboard() {
  const [cancerId, setCancerId] = useState("");
  const [role, setRole] = useState("");
  const [evidenceType, setEvidenceType] = useState("");
  const navigate = useNavigate();
  const cancers = useApi<Cancer[]>("/cancers");
  const vocab = useApi<Vocabularies>("/meta/vocabularies");
  const stats = useApi<DashboardStats>("/dashboard/stats", { cancer_id: cancerId, role, evidence_type: evidenceType });
  const filtered = Boolean(cancerId || role || evidenceType);

  return (
    <div>
      <PageHeader
        title="Dashboard"
        subtitle="All figures are calculated live from the database. Filters apply to association-level statistics."
      />
      <div className="mb-5 grid grid-cols-1 gap-3 rounded-xl border border-slate-200 bg-white p-4 shadow-sm sm:grid-cols-4">
        <Select label="Cancer type" value={cancerId} onChange={setCancerId}
          options={(cancers.data ?? []).map((c) => ({ value: String(c.cancer_id), label: c.name }))} />
        <Select label="Biomarker role" value={role} onChange={setRole}
          options={(vocab.data?.biomarker_roles ?? []).map((r) => ({ value: r, label: humanize(r) }))} />
        <Select label="Evidence type" value={evidenceType} onChange={setEvidenceType}
          options={(vocab.data?.evidence_types ?? []).map((r) => ({ value: r, label: humanize(r) }))} />
        <div className="flex items-end">
          <button disabled={!filtered} onClick={() => { setCancerId(""); setRole(""); setEvidenceType(""); }}
            className="w-full rounded-md border border-slate-300 px-3 py-1.5 text-sm text-slate-700 disabled:opacity-40 enabled:hover:bg-slate-50">
            Clear filters
          </button>
        </div>
      </div>

      <AsyncBlock state={stats}>
        {(s) => (
          <div className="space-y-5">
            <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
              <StatTile label={filtered ? "Biomarkers (filtered)" : "Biomarkers"} value={s.totals.biomarkers} icon={<FlaskConical className="h-5 w-5" />} to="/biomarkers" />
              <StatTile label="Cancer types" value={s.totals.cancers} icon={<Microscope className="h-5 w-5" />} to="/cancers" />
              <StatTile label="Genes / proteins" value={`${s.totals.genes} / ${s.totals.proteins}`} icon={<Dna className="h-5 w-5" />} to="/entities" />
              <StatTile label={filtered ? "Publications (filtered)" : "Publications"} value={s.totals.publications} icon={<BookOpen className="h-5 w-5" />} to="/publications" />
              <StatTile label="Associations" value={s.totals.associations} icon={<Link2 className="h-5 w-5" />} />
              <StatTile label="Evidence records" value={s.totals.evidence_records} icon={<Shapes className="h-5 w-5" />} />
              <StatTile label="Pathways" value={s.totals.pathways} icon={<Network className="h-5 w-5" />} to="/entities?tab=pathways" />
              <StatTile label="Variants" value={s.totals.variants} icon={<GitBranch className="h-5 w-5" />} to="/entities?tab=variants" />
            </div>

            <div className="grid grid-cols-1 gap-5 lg:grid-cols-2">
              <ChartCard title="Associations by biomarker role" valueLabel="Associations"
                data={s.by_role.map((r) => ({ label: humanize(r.role), value: r.count }))}>
                <HBar valueLabel="Associations" data={s.by_role.map((r) => ({ label: humanize(r.role), value: r.count, id: r.role }))}
                  onSelect={(d) => setRole(String(d.id))} />
              </ChartCard>
              <ChartCard title="Associations by cancer type" valueLabel="Associations"
                data={s.by_cancer.map((r) => ({ label: r.cancer, value: r.count }))}>
                <HBar valueLabel="Associations" data={s.by_cancer.map((r) => ({ label: r.cancer, value: r.count, id: r.cancer_id }))}
                  onSelect={(d) => navigate(`/cancers/${d.id}`)} />
              </ChartCard>
              <ChartCard title="Evidence records by evidence type" valueLabel="Evidence records"
                data={s.by_evidence_type.map((r) => ({ label: humanize(r.evidence_type), value: r.count }))}>
                <HBar valueLabel="Evidence records"
                  data={s.by_evidence_type.map((r) => ({ label: humanize(r.evidence_type), value: r.count, muted: r.evidence_type === "unspecified" }))} />
                <p className="mt-2 text-xs text-slate-500">Grey bar: records without a specified evidence type (KEGG database annotations).</p>
              </ChartCard>
              <ChartCard title="Biomarkers by category" valueLabel="Biomarkers"
                data={s.by_biomarker_type.map((r) => ({ label: humanize(r.biomarker_type), value: r.count }))}>
                <HBar valueLabel="Biomarkers" data={s.by_biomarker_type.map((r) => ({ label: humanize(r.biomarker_type), value: r.count }))} />
              </ChartCard>
              <ChartCard title="Evidence-support score distribution" valueLabel="Associations"
                data={histogramData(s.score_distribution)}>
                <VBar valueLabel="Associations" data={histogramData(s.score_distribution)} />
                <div className="mt-2 flex flex-wrap gap-4 text-xs text-slate-600">
                  {s.score_status.map((st) => (
                    <span key={st.status} className="inline-flex items-center gap-1"><ScoreStatusLabel status={st.status} /> {st.count}</span>
                  ))}
                </div>
              </ChartCard>
              <Card title="Most represented biomarkers" bodyClass="p-0">
                <table className="w-full text-sm">
                  <thead className="bg-slate-50 text-left text-xs uppercase tracking-wide text-slate-500">
                    <tr><th className="px-4 py-2">Biomarker</th><th className="px-4 py-2 text-right">Cancers</th><th className="px-4 py-2 text-right">Publications</th></tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {s.top_biomarkers.map((b) => (
                      <tr key={b.biomarker_id} className="hover:bg-slate-50">
                        <td className="px-4 py-2"><Link className="text-navy-700 hover:underline" to={`/biomarkers/${b.biomarker_id}`}>{b.name}</Link></td>
                        <td className="tabular px-4 py-2 text-right">{b.n_cancers}</td>
                        <td className="tabular px-4 py-2 text-right">{b.n_publications}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </Card>
            </div>
            <Disclaimer />
          </div>
        )}
      </AsyncBlock>
    </div>
  );
}
