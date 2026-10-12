import { useEffect, useMemo, useState } from "react";
import { Code2, Play } from "lucide-react";
import { exportUrl } from "../api/client";
import type { Cancer, CatalogueEntry, ReportResult } from "../api/types";
import { AsyncBlock, Badge, Card, ExportButton, PageHeader, Select } from "../components/ui";
import { humanize } from "../lib/format";
import { useApi } from "../lib/useApi";

export default function Analytics() {
  const catalogue = useApi<CatalogueEntry[]>("/analytics/catalogue");
  const cancers = useApi<Cancer[]>("/cancers");
  const [key, setKey] = useState("multi_cancer_biomarkers");
  const [values, setValues] = useState<Record<string, string>>({});
  const [run, setRun] = useState<Record<string, string>>({});
  const entry = catalogue.data?.find((c) => c.key === key);

  useEffect(() => {
    if (!entry) return;
    const defaults: Record<string, string> = {};
    entry.params.forEach((p) => {
      if (p.type === "cancer") {
        const ids = (cancers.data ?? []).map((c) => String(c.cancer_id));
        defaults[p.name] = p.name.endsWith("_a") ? ids[0] ?? "" : ids[2] ?? ids[1] ?? "";
      } else defaults[p.name] = String(p.default ?? "");
    });
    setValues(defaults);
    setRun(defaults);
  }, [entry, cancers.data]);

  const ready = entry && entry.params.every((p) => run[p.name] !== undefined && run[p.name] !== "");
  const result = useApi<ReportResult>(ready ? `/analytics/${key}` : null, run);
  const cancerOpts = useMemo(() => (cancers.data ?? []).map((c) => ({ value: String(c.cancer_id), label: c.name })), [cancers.data]);

  return (
    <div>
      <PageHeader title="SQL Analytics & Reports"
        subtitle="Each report is a documented, parameterized SQL query that runs unchanged on PostgreSQL and SQLite." />
      <div className="grid gap-5 lg:grid-cols-[280px_1fr]">
        <Card title="Query catalogue" bodyClass="p-2">
          <AsyncBlock state={catalogue}>
            {(list) => (
              <ul className="space-y-0.5">
                {list.map((c, i) => (
                  <li key={c.key}>
                    <button onClick={() => setKey(c.key)}
                      className={`w-full rounded-md px-3 py-2 text-left text-sm ${key === c.key ? "bg-navy-800 text-white" : "text-slate-700 hover:bg-slate-100"}`}>
                      <span className="mr-1 text-xs opacity-60">Q{i + 1}</span> {c.title}
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </AsyncBlock>
        </Card>

        <div className="min-w-0 space-y-5">
          {entry && (
            <Card title={entry.title} actions={<div className="flex flex-wrap gap-1">{entry.concepts.map((c) => <Badge key={c}>{c}</Badge>)}</div>}>
              <p className="mb-3 text-sm text-slate-600">{entry.description}</p>
              <details open className="mb-3">
                <summary className="inline-flex cursor-pointer items-center gap-1 text-xs font-medium text-slate-600"><Code2 className="h-3.5 w-3.5" /> SQL</summary>
                <pre className="mt-2 overflow-x-auto rounded-lg bg-navy-900 p-3 text-xs leading-relaxed text-slate-100">{entry.sql}</pre>
              </details>
              <form className="flex flex-wrap items-end gap-3" onSubmit={(e) => { e.preventDefault(); setRun({ ...values }); }}>
                {entry.params.map((p) => p.type === "cancer" ? (
                  <div key={p.name} className="w-56"><Select label={`${p.description} (:${p.name})`} value={values[p.name] ?? ""} allLabel={null}
                    onChange={(v) => setValues((s) => ({ ...s, [p.name]: v }))} options={cancerOpts} /></div>
                ) : (
                  <label key={p.name} className="flex flex-col gap-1 text-xs font-medium text-slate-600">
                    {p.description} (:{p.name})
                    <input type="number" min={0} value={values[p.name] ?? ""} onChange={(e) => setValues((s) => ({ ...s, [p.name]: e.target.value }))}
                      className="w-32 rounded-md border border-slate-300 px-2 py-1.5 text-sm" />
                  </label>
                ))}
                <button type="submit" className="inline-flex items-center gap-1.5 rounded-md bg-navy-800 px-3 py-1.5 text-sm font-medium text-white hover:bg-navy-700">
                  <Play className="h-4 w-4" aria-hidden /> Run query
                </button>
                {ready && <ExportButton href={exportUrl("analytics", { report: key, ...run })} />}
              </form>
            </Card>
          )}
          <Card title="Result" bodyClass="p-0">
            <AsyncBlock state={result} isEmpty={(r) => r.rows.length === 0}>
              {(r) => (
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-sm">
                    <thead className="border-b border-slate-200 bg-slate-50 text-xs uppercase tracking-wide text-slate-500">
                      <tr>{r.columns.map((c) => <th key={c} className="px-3 py-2">{c}</th>)}</tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {r.rows.map((row, i) => (
                        <tr key={i} className="hover:bg-slate-50">
                          {r.columns.map((c) => (
                            <td key={c} className={`px-3 py-1.5 ${typeof row[c] === "number" ? "tabular text-right" : ""}`}>
                              {row[c] === null ? <span className="text-slate-400">NULL</span> : c === "biomarker_role" ? humanize(String(row[c])) : String(row[c])}
                            </td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                  <p className="border-t border-slate-100 px-3 py-2 text-xs text-slate-500">{r.rows.length} row{r.rows.length === 1 ? "" : "s"}</p>
                </div>
              )}
            </AsyncBlock>
          </Card>
        </div>
      </div>
    </div>
  );
}
