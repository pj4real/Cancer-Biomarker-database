import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { exportUrl } from "../api/client";
import type { BiomarkerListItem, Cancer, Page, PublicationListItem, Vocabularies } from "../api/types";
import { ConsistencyLabel } from "../components/EvidenceList";
import { AsyncBlock, Badge, Card, ExportButton, ExternalLink, PageHeader, Pagination, Select } from "../components/ui";
import { humanize } from "../lib/format";
import { useApi } from "../lib/useApi";

export default function Publications() {
  const [params, setParams] = useSearchParams();
  const get = (k: string) => params.get(k) ?? "";
  const update = (patch: Record<string, string>) => {
    const n = new URLSearchParams(params);
    for (const [k, v] of Object.entries(patch)) (v ? n.set(k, v) : n.delete(k));
    if (!("page" in patch)) n.delete("page");
    setParams(n, { replace: true });
  };
  const [text, setText] = useState(get("q"));
  useEffect(() => {
    const t = setTimeout(() => { if (text !== get("q")) update({ q: text }); }, 300);
    return () => clearTimeout(t);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [text]);

  const cancers = useApi<Cancer[]>("/cancers");
  const vocab = useApi<Vocabularies>("/meta/vocabularies");
  const biomarkers = useApi<Page<BiomarkerListItem>>("/biomarkers", { page_size: 200 });
  const filters = { q: get("q"), biomarker_id: get("biomarker_id"), cancer_id: get("cancer_id"),
    year_from: get("year_from"), year_to: get("year_to"), evidence_type: get("evidence_type") };
  const list = useApi<Page<PublicationListItem>>("/publications", { ...filters, page: get("page") || 1, page_size: 10 });

  return (
    <div>
      <PageHeader title="Research Evidence Explorer"
        subtitle="Publication metadata (title, authors, journal, year, DOI) was retrieved from PubMed E-utilities. Original links are preserved."
        actions={<ExportButton href={exportUrl("publications", filters)} />} />
      <div className="mb-4 grid grid-cols-2 gap-3 rounded-xl border border-slate-200 bg-white p-4 shadow-sm md:grid-cols-6">
        <label className="col-span-2 flex flex-col gap-1 text-xs font-medium text-slate-600">
          Search
          <input value={text} onChange={(e) => setText(e.target.value)} placeholder="Title, PMID, DOI, author, journal"
            className="rounded-md border border-slate-300 px-2 py-1.5 text-sm shadow-sm" />
        </label>
        <Select label="Biomarker" value={get("biomarker_id")} onChange={(v) => update({ biomarker_id: v })}
          options={(biomarkers.data?.items ?? []).map((b) => ({ value: String(b.biomarker_id), label: b.name }))} />
        <Select label="Cancer" value={get("cancer_id")} onChange={(v) => update({ cancer_id: v })}
          options={(cancers.data ?? []).map((c) => ({ value: String(c.cancer_id), label: c.name }))} />
        <Select label="Evidence type" value={get("evidence_type")} onChange={(v) => update({ evidence_type: v })}
          options={(vocab.data?.evidence_types ?? []).map((t) => ({ value: t, label: humanize(t) }))} />
        <div className="grid grid-cols-2 gap-2">
          {(["year_from", "year_to"] as const).map((k) => (
            <label key={k} className="flex flex-col gap-1 text-xs font-medium text-slate-600">
              {k === "year_from" ? "From" : "To"}
              <input type="number" min={1900} max={2100} value={get(k)} onChange={(e) => update({ [k]: e.target.value })}
                className="w-full rounded-md border border-slate-300 px-2 py-1.5 text-sm shadow-sm" />
            </label>
          ))}
        </div>
      </div>
      <Card bodyClass="p-0">
        <AsyncBlock state={list} isEmpty={(d) => d.items.length === 0}>
          {(d) => (
            <>
              <ul className="divide-y divide-slate-100">
                {d.items.map((p) => (
                  <li key={p.publication_id} className="p-4">
                    <div className="flex flex-wrap items-start justify-between gap-2">
                      <h3 className="min-w-0 flex-1 font-medium text-navy-900">
                        {p.source_url ? <ExternalLink href={p.source_url}>{p.title}</ExternalLink> : p.title}
                      </h3>
                      <span className="tabular text-sm font-semibold text-slate-600">{p.publication_year}</span>
                    </div>
                    <p className="mt-0.5 text-xs text-slate-500">
                      {p.authors} · <em>{p.journal}</em> · PMID {p.pmid}{p.doi && <> · DOI {p.doi}</>}
                    </p>
                    <div className="mt-2 flex flex-wrap gap-1">
                      {p.evidence_types.map((t) => <Badge key={t} className="bg-navy-50 text-navy-800 ring-navy-200">{humanize(t)}</Badge>)}
                      {p.source_names.map((s) => <Badge key={s}>{s}</Badge>)}
                    </div>
                    <ul className="mt-2 space-y-1">
                      {p.summaries.map((s, i) => (
                        <li key={i} className="text-sm text-slate-700">
                          <span className="font-medium">{s.biomarker}</span> · {s.cancer} · {humanize(s.role)}: {s.summary}{" "}
                          <ConsistencyLabel value={s.consistency} />
                        </li>
                      ))}
                    </ul>
                    <div className="mt-1.5 flex flex-wrap gap-x-3 text-xs">
                      {p.biomarker_links.map(([id, name]) => (
                        <Link key={id} to={`/biomarkers/${id}`} className="text-teal-brand hover:underline">{name}</Link>
                      ))}
                    </div>
                  </li>
                ))}
              </ul>
              <Pagination page={d.page} pages={d.pages} total={d.total} onPage={(pg) => update({ page: String(pg) })} />
            </>
          )}
        </AsyncBlock>
      </Card>
    </div>
  );
}
