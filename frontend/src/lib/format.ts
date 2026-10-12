/** Formatting helpers shared across pages. */

const LABEL_OVERRIDES: Record<string, string> = {
  nsclc: "NSCLC",
  msi: "MSI",
  randomized_clinical_trial: "Randomized clinical trial",
  genomic_profiling: "Genomic profiling",
  copy_number_alteration: "Copy-number alteration",
  pending_curation: "Pending curation",
  curated_literature: "Curated literature",
  rna_transcript: "RNA transcript",
  epigenetic_methylation: "Epigenetic methylation",
};

/** snake_case vocabulary value -> readable label. */
export function humanize(value: string | null | undefined): string {
  if (!value) return "—";
  if (LABEL_OVERRIDES[value]) return LABEL_OVERRIDES[value];
  const s = value.replace(/_/g, " ");
  return s.charAt(0).toUpperCase() + s.slice(1);
}

export function formatScore(score: number | null | undefined): string {
  return score === null || score === undefined ? "n/a" : score.toFixed(1);
}

export function formatPercent(fraction: number | null | undefined): string {
  return fraction === null || fraction === undefined ? "n/a" : `${Math.round(fraction * 100)}%`;
}

export function truncate(text: string, max = 90): string {
  return text.length > max ? `${text.slice(0, max - 1)}…` : text;
}

export const COMPONENT_LABELS: Record<string, { label: string; key: "P" | "D" | "T" | "C" }> = {
  publication_support: { label: "Publication support", key: "P" },
  source_diversity: { label: "Source diversity", key: "D" },
  evidence_type: { label: "Evidence type", key: "T" },
  consistency: { label: "Evidence consistency", key: "C" },
};

export const WEIGHT_KEYS: Record<string, string> = {
  publication_support: "publication_support",
  source_diversity: "source_diversity",
  evidence_type: "evidence_type",
  consistency: "consistency",
};
