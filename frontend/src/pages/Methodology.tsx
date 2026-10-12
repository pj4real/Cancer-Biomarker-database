import type { Methodology as M } from "../api/types";
import { AsyncBlock, Card, Disclaimer, PageHeader, Table } from "../components/ui";
import { COMPONENT_LABELS, humanize } from "../lib/format";
import { useApi } from "../lib/useApi";

export default function Methodology() {
  const state = useApi<M>("/scores/methodology");
  return (
    <AsyncBlock state={state}>
      {(m) => (
        <div className="space-y-5">
          <PageHeader title="Evidence-Aware Confidence & Gap Analysis"
            subtitle={`Scoring version ${m.scoring_version}. A transparent, explainable evidence-support score, not a clinical prediction model.`} />
          <Disclaimer />
          <Card title="Formula">
            <p className="font-mono text-lg text-navy-900">Score = 0.35·P + 0.25·D + 0.25·T + 0.15·C</p>
            <p className="mt-2 text-sm text-slate-600">
              Weights are proposed project parameters (configurable through environment variables), not validated clinical standards.
              Active configuration:{" "}
              {Object.entries(m.weights).map(([k, w]) => `${COMPONENT_LABELS[k]?.key ?? k} = ${w}`).join(", ")}; publication cap = {m.publication_cap};
              minimum coverage for a provisional score = {Math.round(m.min_coverage * 100)}%.
            </p>
          </Card>
          <div className="grid gap-5 lg:grid-cols-2">
            <Card title="Components (each 0–100)">
              <dl className="space-y-3 text-sm">
                {Object.entries(m.components).map(([k, v]) => (
                  <div key={k}><dt className="font-semibold text-navy-800">{k}</dt><dd className="text-slate-700">{v}</dd></div>
                ))}
              </dl>
            </Card>
            <Card title="Evidence-type rubric" bodyClass="p-0">
              <Table head={["Evidence type", "Rubric value"]}>
                {Object.entries(m.evidence_type_rubric).map(([k, v]) => (
                  <tr key={k}><td className="px-3 py-1.5">{humanize(k)}</td><td className="tabular px-3 py-1.5">{v}</td></tr>
                ))}
              </Table>
            </Card>
          </div>
          <Card title="Missing data and uncertainty">
            <p className="text-sm text-slate-700">{m.missing_data}</p>
            <ul className="mt-3 list-disc space-y-1 pl-5 text-sm text-slate-700">
              <li><strong>Complete</strong>: all four components observed; weighted sum reported.</li>
              <li><strong>Provisional</strong>: some components unknown; score = Σ(wᵢ·xᵢ) / Σwᵢ over observed components, shown with an asterisk, a dashed outline and a warning.</li>
              <li><strong>Insufficient</strong>: observed weight below the minimum; no overall score is reported.</li>
              <li>Zero recorded publications, sources, typed evidence or consistency annotations make that component <em>unknown</em>, never 0.</li>
              <li>Duplicate records are collapsed: publications by PMID/DOI, sources by name.</li>
            </ul>
          </Card>
          <Card title="Worked example (verified by automated test)">
            <p className="text-sm text-slate-700">
              Three distinct publications (an RCT and a patient cohort in PubMed, a genomic-profiling study via NCI GDC), two
              sources, and two "supports" annotations:
            </p>
            <ul className="mt-2 space-y-1 font-mono text-xs text-slate-800">
              <li>P = 100·log2(1+3)/log2(1+5) = 77.37</li>
              <li>D = 100·(1 − 0.5²) = 75.00</li>
              <li>T = 0.7·95 + 0.3·mean(95, 80, 65) = 90.50</li>
              <li>C = 100·(2 supports) / 2 annotated = 100.00</li>
              <li>Score = 0.35·77.37 + 0.25·75 + 0.25·90.5 + 0.15·100 = 83.45 (complete)</li>
            </ul>
          </Card>
          <p className="text-xs text-slate-500">{m.disclaimer}</p>
        </div>
      )}
    </AsyncBlock>
  );
}
