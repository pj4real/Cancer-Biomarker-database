import { AlertTriangle, HelpCircle } from "lucide-react";
import type { Score } from "../api/types";
import { COMPONENT_LABELS, formatPercent, formatScore } from "../lib/format";
import { ScorePill, ScoreStatusLabel } from "./ui";

const DEFAULT_WEIGHTS: Record<string, number> = {
  publication_support: 0.35,
  source_diversity: 0.25,
  evidence_type: 0.25,
  consistency: 0.15,
};

/**
 * Visual breakdown of the four score components. Unknown components are drawn as
 * hatched "unknown" bars, never as zero.
 */
export function ScoreBreakdown({ score, weights = DEFAULT_WEIGHTS, compact = false }: {
  score: Score | null; weights?: Record<string, number>; compact?: boolean;
}) {
  if (!score) return <p className="text-sm text-slate-500">No score has been calculated.</p>;
  const comps = Object.keys(COMPONENT_LABELS) as (keyof typeof COMPONENT_LABELS)[];
  return (
    <div className="space-y-3">
      <div className="flex flex-wrap items-center gap-3">
        <span className="text-sm text-slate-600">Evidence-support score</span>
        <ScorePill score={score.overall_score} status={score.score_status} />
        <ScoreStatusLabel status={score.score_status} />
        <span className="text-xs text-slate-500">coverage {formatPercent(score.evidence_coverage)}</span>
      </div>
      {score.score_status !== "complete" && (
        <p className="flex items-start gap-1.5 rounded-md bg-amber-50 px-2 py-1.5 text-xs text-amber-900">
          <AlertTriangle className="mt-0.5 h-3.5 w-3.5 shrink-0" aria-hidden />
          {score.score_status === "provisional"
            ? `Provisional: based on incomplete information. Unknown: ${score.missing_components.join(", ").replace(/_/g, " ")}. Not equivalent to a fully observed score.`
            : "Insufficient evidence metadata to report an overall score."}
        </p>
      )}
      <ul className="space-y-2" aria-label="Score components">
        {comps.map((k) => {
          const v = score[k as keyof Score] as number | null;
          const meta = COMPONENT_LABELS[k];
          return (
            <li key={k}>
              <div className="flex items-center justify-between text-xs">
                <span className="font-medium text-slate-700">
                  {meta.label} <span className="text-slate-400">({meta.key}, weight {Math.round((weights[k] ?? 0) * 100)}%)</span>
                </span>
                <span className="tabular text-slate-700">
                  {v === null ? (
                    <span className="inline-flex items-center gap-1 text-slate-500"><HelpCircle className="h-3 w-3" aria-hidden />unknown</span>
                  ) : formatScore(v)}
                </span>
              </div>
              <div className="mt-1 h-2 overflow-hidden rounded-full bg-slate-100" role="img"
                aria-label={`${meta.label}: ${v === null ? "unknown" : formatScore(v)}`}>
                {v === null ? (
                  <div className="h-full w-full bg-[repeating-linear-gradient(45deg,#e2e8f0_0_4px,#f8fafc_4px_8px)]" />
                ) : (
                  <div className="h-full rounded-full bg-chart-1" style={{ width: `${v}%` }} />
                )}
              </div>
            </li>
          );
        })}
      </ul>
      {!compact && (
        <p className="text-xs text-slate-500">
          {score.n_publications} distinct publication{score.n_publications === 1 ? "" : "s"} · {score.n_sources} distinct
          source{score.n_sources === 1 ? "" : "s"} · scoring v{score.scoring_version}
        </p>
      )}
    </div>
  );
}
