import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { ArrowDown, ArrowUp } from "lucide-react";
import { exportUrl } from "../api/client";
import type { BiomarkerListItem, Cancer, Page, Vocabularies } from "../api/types";
import { AsyncBlock, Badge, Card, ExportButton, PageHeader, Pagination, RoleBadge, ScorePill, Select } from "../components/ui";
import { humanize } from "../lib/format";
import { useApi } from "../lib/useApi";

type SortKey = "name" | "publications" | "score";

export default function BiomarkerExplorer() {
  const [params, setParams] = useSearchParams();
  const q = params.get("q") ?? "";
  const cancerId = params.get("cancer_id") ?? "";
  const type = params.get("biomarker_type") ?? "";
  const role = params.get("role") ?? "";
  const sort = (params.get("sort") as SortKey) ?? "name";
  const order = params.get("order") ?? "asc";
  const page = Number(params.get("page") ?? 1);
  const [text, setText] = useState(q);
  useEffect(() => setText(q), [q]);

  const update = (patch: Record<string, string>) => {
    const next = new URLSearchParams(params);
    for (const [k, v] of Object.entries(patch)) (v ? next.set(k, v) : next.delete(k));
    if (!("page" in patch)) next.delete("page");
    setParams(next, { replace: true });
  };

  // Debounced search-as-you-type; the backend does the matching.
  useEffect(() => {
    const t = setTimeout(() => { if (text !== q) update({ q: text }); }, 300);
    return () => clearTimeout(t);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [text]);

  const cancers = useApi<Cancer[]>("/cancers");
  const vocab = useApi<Vocabularies>("/meta/vocabularies");
  const filters = { q, cancer_id: cancerId, biomarker_type: type, role };
  const list = useApi<Page<BiomarkerListItem>>("/biomarkers", { ...filters, sort, order, page, page_size: 15 });

  const sortHeader = (key: SortKey, label: string, align = "") => {
    const active = sort === key;
    const nextOrder = active && order === "asc" ? "desc" : active ? "asc" : key === "name" ? "asc" : "desc";
    return (
      <button onClick={() => update({ sort: key, order: nextOrder })} className={`inline-flex items-center gap-1 uppercase ${align}`}
        aria-label={`Sort by ${label}`}>
        {label}
        {active && (order === "asc" ? <ArrowUp className="h-3 w-3" /> : <ArrowDown className="h-3 w-3" />)}
      </button>
    );
  };

  return (
    <div>
      <PageHeader title="Biomarker Explorer"
        subtitle="Search and filter queries run in the database. The score column shows the highest evidence-support score across a biomarker's associations."
        actions={<ExportButton href={exportUrl("biomarkers", filters)} />} />

      <div className="mb-4 grid grid-cols-1 gap-3 rounded-xl border border-slate-200 bg-white p-4 shadow-sm md:grid-cols-4">
        <label className="flex flex-col gap-1 text-xs font-medium text-slate-600">
          Search
          <input value={text} onChange={(e) => setText(e.target.value)} placeholder="KRAS, HER2, CBM-012…"
            className="rounded-md border border-slate-300 px-2 py-1.5 text-sm shadow-sm" />
        </label>
        <Select label="Cancer type" value={cancerId} onChange={(v) => update({ cancer_id: v })}
          options={(cancers.data ?? []).map((c) => ({ value: String(c.cancer_id), label: c.name }))} />
        <Select label="Biomarker category" value={type} onChange={(v) => update({ biomarker_type: v })}
          options={(vocab.data?.biomarker_types ?? []).map((t) => ({ value: t, label: humanize(t) }))} />
        <Select label="Role" value={role} onChange={(v) => update({ role: v })}
          options={(vocab.data?.biomarker_roles ?? []).map((t) => ({ value: t, label: humanize(t) }))} />
      </div>

      <Card bodyClass="p-0">
        <AsyncBlock state={list} isEmpty={(d) => d.items.length === 0}>
          {(d) => (
            <>
              <div className="overflow-x-auto">
                <table className="w-full text-left text-sm">
                  <thead className="border-b border-slate-200 bg-slate-50 text-xs tracking-wide text-slate-500">
                    <tr>
                      <th className="px-4 py-2">{sortHeader("name", "Biomarker")}</th>
                      <th className="px-4 py-2 uppercase">Gene</th>
                      <th className="px-4 py-2 uppercase">Category</th>
                      <th className="px-4 py-2 uppercase">Cancers</th>
                      <th className="px-4 py-2 uppercase">Roles</th>
                      <th className="px-4 py-2 text-right">{sortHeader("publications", "Pubs")}</th>
                      <th className="px-4 py-2 text-right">{sortHeader("score", "Score")}</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {d.items.map((b) => (
                      <tr key={b.biomarker_id} className="hover:bg-slate-50">
                        <td className="px-4 py-2.5">
                          <Link to={`/biomarkers/${b.biomarker_id}`} className="font-medium text-navy-700 hover:underline">{b.name}</Link>
                          <div className="text-xs text-slate-400">{b.biomarker_code}</div>
                        </td>
                        <td className="px-4 py-2.5 font-mono text-xs">{b.gene_symbols.join(", ") || "—"}</td>
                        <td className="px-4 py-2.5 text-xs text-slate-600">{humanize(b.biomarker_type)}</td>
                        <td className="px-4 py-2.5"><div className="flex flex-wrap gap-1">{b.cancers.map((c) => <Badge key={c}>{c}</Badge>)}</div></td>
                        <td className="px-4 py-2.5"><div className="flex flex-wrap gap-1">{b.roles.map((r) => <RoleBadge key={r} role={r} />)}</div></td>
                        <td className="tabular px-4 py-2.5 text-right">{b.n_publications}</td>
                        <td className="px-4 py-2.5 text-right"><ScorePill score={b.max_score} /></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <Pagination page={d.page} pages={d.pages} total={d.total} onPage={(p) => update({ page: String(p) })} />
            </>
          )}
        </AsyncBlock>
      </Card>
    </div>
  );
}
