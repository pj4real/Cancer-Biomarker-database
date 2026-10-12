export interface Page<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export interface Link {
  label: string;
  url: string;
}

export interface BiomarkerBrief {
  biomarker_id: number;
  biomarker_code: string;
  name: string;
  biomarker_type: string;
}

export interface CancerBrief {
  cancer_id: number;
  code: string;
  name: string;
}

export interface GeneBrief {
  gene_id: number;
  official_symbol: string;
  full_name: string | null;
  ncbi_gene_id: number | null;
}

export interface ProteinBrief {
  protein_id: number;
  accession: string;
  name: string;
}

export interface PathwayBrief {
  pathway_id: number;
  pathway_name: string;
  pathway_database: string;
  external_identifier: string;
  source_url: string | null;
}

export interface Publication {
  publication_id: number;
  pmid: string | null;
  doi: string | null;
  title: string;
  authors: string | null;
  publication_year: number | null;
  journal: string | null;
  source_url: string | null;
}

export type ScoreStatus = "complete" | "provisional" | "insufficient";

export interface Score {
  publication_support: number | null;
  source_diversity: number | null;
  evidence_type: number | null;
  consistency: number | null;
  overall_score: number | null;
  evidence_coverage: number;
  score_status: ScoreStatus;
  missing_components: string[];
  n_publications: number;
  n_sources: number;
  scoring_version: string;
  calculated_at?: string;
}

export interface Evidence {
  evidence_id: number;
  evidence_type: string | null;
  source_name: string;
  source_record_id: string | null;
  evidence_summary: string | null;
  consistency_annotation: string | null;
  retrieved_at: string | null;
  source_url: string | null;
  publication: Publication | null;
}

export interface Association {
  association_id: number;
  biomarker: BiomarkerBrief;
  cancer: CancerBrief;
  biomarker_role: string;
  association_description: string | null;
  source_status: string;
  score: Score | null;
  variants: { variant_id: number; variant_identifier: string }[];
  n_evidence: number;
  n_publications: number;
  evidence?: Evidence[];
}

export interface BiomarkerListItem extends BiomarkerBrief {
  gene_symbols: string[];
  cancers: string[];
  roles: string[];
  n_associations: number;
  n_publications: number;
  max_score: number | null;
  has_incomplete_score: boolean;
}

export interface Variant {
  variant_id: number;
  variant_identifier: string;
  gene: GeneBrief;
  protein_change: string | null;
  dbsnp_id: string | null;
  genome_assembly: string | null;
  chromosome: string | null;
  position: number | null;
  reference_allele: string | null;
  alternate_allele: string | null;
  clinical_or_research_annotation: string | null;
  source_identifier: string | null;
  links: Link[];
}

export interface BiomarkerDetail extends BiomarkerBrief {
  description: string | null;
  biological_function: string | null;
  external_identifier: string | null;
  genes: (GeneBrief & { description: string | null; links: Link[]; proteins: (ProteinBrief & { links: Link[] })[] })[];
  pathways: (PathwayBrief & { annotation_source: string | null })[];
  associations: Association[];
  variants: Variant[];
  publications: (Publication & { contexts: { cancer: string; role: string; evidence_type: string | null }[] })[];
  source_databases: { source_name: string; n_records: number }[];
}

export interface Cancer extends CancerBrief {
  tissue_origin: string | null;
  cancer_category: string | null;
  external_identifier: string | null;
  gdc_project_id: string | null;
  description: string | null;
  n_biomarkers: number;
  n_associations: number;
  links: Link[];
}

export interface HistogramBin {
  bin: string;
  lower: number | null;
  count: number;
}

export interface CancerDetail extends Omit<Cancer, "n_biomarkers" | "n_associations"> {
  associations: Association[];
  role_distribution: { role: string; count: number }[];
  genes: (GeneBrief & { biomarkers: string[] })[];
  pathways: (PathwayBrief & { n_gene_links: number })[];
  variants: { variant_id: number; variant_identifier: string; biomarker: string }[];
  publications: (Publication & { biomarkers: string[] })[];
  score_distribution: HistogramBin[];
}

export interface CompareEntry extends BiomarkerBrief {
  a: { role: string; score: number | null; score_status: string | null; association_id: number }[];
  b: { role: string; score: number | null; score_status: string | null; association_id: number }[];
}

export interface CompareResult {
  cancer_a: CancerBrief;
  cancer_b: CancerBrief;
  shared: CompareEntry[];
  only_a: CompareEntry[];
  only_b: CompareEntry[];
}

export interface PublicationListItem extends Publication {
  biomarkers: string[];
  biomarker_links: [number, string][];
  cancers: string[];
  evidence_types: string[];
  source_names: string[];
  summaries: { biomarker: string; cancer: string; role: string; summary: string | null; consistency: string | null }[];
}

export interface DashboardStats {
  totals: Record<string, number>;
  by_role: { role: string; count: number }[];
  by_cancer: { cancer_id: number; cancer: string; count: number }[];
  by_evidence_type: { evidence_type: string; count: number }[];
  by_biomarker_type: { biomarker_type: string; count: number }[];
  top_biomarkers: { biomarker_id: number; name: string; n_cancers: number; n_publications: number }[];
  score_status: { status: ScoreStatus; count: number }[];
  score_distribution: HistogramBin[];
}

export interface GapItem {
  association_id: number;
  biomarker_id: number;
  biomarker_name: string;
  biomarker_code: string;
  cancer_id: number;
  cancer_name: string;
  biomarker_role: string;
  source_status: string;
  n_evidence: number;
  n_publications: number;
  n_sources: number;
  overall_score: number | null;
  score_status: ScoreStatus | null;
  evidence_coverage: number | null;
  flags: string[];
  gap_count: number;
  details: Record<string, unknown>;
}

export interface GapResponse {
  summary: Record<string, number>;
  flag_descriptions: Record<string, string>;
  total: number;
  items: GapItem[];
}

export interface ReportParam {
  name: string;
  type: "int" | "float" | "cancer";
  default: number | null;
  description: string;
}

export interface CatalogueEntry {
  key: string;
  title: string;
  description: string;
  sql: string;
  params: ReportParam[];
  concepts: string[];
}

export interface ReportResult {
  key: string;
  title: string;
  columns: string[];
  rows: Record<string, string | number | null>[];
  params: Record<string, unknown>;
}

export interface NetworkNode {
  id: string;
  label: string;
  type: "biomarker" | "cancer" | "gene" | "protein" | "pathway" | "publication" | "variant";
  entity_id: number;
}

export interface NetworkData {
  nodes: NetworkNode[];
  edges: { source: string; target: string; label: string }[];
}

export interface Vocabularies {
  biomarker_types: string[];
  biomarker_roles: string[];
  evidence_types: string[];
  consistency_values: string[];
  source_statuses: string[];
  gap_flags: Record<string, string>;
  import_entities: string[];
}

export interface Methodology {
  scoring_version: string;
  formula: string;
  components: Record<string, string>;
  evidence_type_rubric: Record<string, number>;
  missing_data: string;
  disclaimer: string;
  weights: Record<string, number>;
  publication_cap: number;
  min_coverage: number;
}

export interface ImportReport {
  entity: string;
  rows_total: number;
  inserted: number;
  updated: number;
  unchanged: number;
  errors: { row: number; field: string | null; message: string }[];
  dry_run: boolean;
  ok: boolean;
}
