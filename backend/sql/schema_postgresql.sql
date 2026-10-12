-- CancerBioMap PostgreSQL schema
-- Generated from the Alembic migration with:
--   DATABASE_URL=postgresql+psycopg://... alembic upgrade head --sql

BEGIN;

CREATE TABLE alembic_version (
    version_num VARCHAR(32) NOT NULL, 
    CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
);

-- Running upgrade  -> 0001

CREATE TABLE biomarker (
    biomarker_id SERIAL NOT NULL, 
    biomarker_code VARCHAR(20) NOT NULL, 
    name VARCHAR(200) NOT NULL, 
    biomarker_type VARCHAR(40) NOT NULL, 
    description TEXT, 
    biological_function TEXT, 
    external_identifier VARCHAR(100), 
    created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    PRIMARY KEY (biomarker_id), 
    CONSTRAINT ck_biomarker_type CHECK (biomarker_type IN ('genetic_mutation', 'germline_variant', 'gene_fusion', 'copy_number_alteration', 'protein_expression', 'circulating_protein', 'gene_expression_signature', 'rna_transcript', 'epigenetic_methylation', 'genomic_signature')), 
    UNIQUE (biomarker_code)
);

CREATE INDEX ix_biomarker_biomarker_type ON biomarker (biomarker_type);

CREATE UNIQUE INDEX ix_biomarker_name ON biomarker (name);

CREATE TABLE cancer (
    cancer_id SERIAL NOT NULL, 
    code VARCHAR(30) NOT NULL, 
    name VARCHAR(150) NOT NULL, 
    tissue_origin VARCHAR(100), 
    cancer_category VARCHAR(100), 
    external_identifier VARCHAR(50), 
    gdc_project_id VARCHAR(30), 
    description TEXT, 
    PRIMARY KEY (cancer_id), 
    UNIQUE (code), 
    UNIQUE (name)
);

CREATE TABLE gene (
    gene_id SERIAL NOT NULL, 
    official_symbol VARCHAR(30) NOT NULL, 
    full_name VARCHAR(255), 
    organism VARCHAR(100) NOT NULL, 
    ncbi_gene_id INTEGER, 
    description TEXT, 
    PRIMARY KEY (gene_id), 
    UNIQUE (ncbi_gene_id), 
    UNIQUE (official_symbol)
);

CREATE TABLE pathway (
    pathway_id SERIAL NOT NULL, 
    pathway_name VARCHAR(200) NOT NULL, 
    pathway_database VARCHAR(30) NOT NULL, 
    external_identifier VARCHAR(50) NOT NULL, 
    description TEXT, 
    source_url VARCHAR(300), 
    PRIMARY KEY (pathway_id), 
    CONSTRAINT ck_pathway_database CHECK (pathway_database IN ('KEGG', 'Reactome', 'WikiPathways', 'Other')), 
    CONSTRAINT uq_pathway_source_id UNIQUE (pathway_database, external_identifier)
);

CREATE TABLE protein (
    protein_id SERIAL NOT NULL, 
    accession VARCHAR(20) NOT NULL, 
    name VARCHAR(255) NOT NULL, 
    function TEXT, 
    organism VARCHAR(100) NOT NULL, 
    PRIMARY KEY (protein_id), 
    UNIQUE (accession)
);

CREATE TABLE publication (
    publication_id SERIAL NOT NULL, 
    pmid VARCHAR(12), 
    doi VARCHAR(120), 
    title TEXT NOT NULL, 
    authors TEXT, 
    publication_year INTEGER, 
    journal VARCHAR(200), 
    source_url VARCHAR(300), 
    PRIMARY KEY (publication_id), 
    CONSTRAINT ck_publication_identifier CHECK (pmid IS NOT NULL OR doi IS NOT NULL), 
    CONSTRAINT ck_publication_year CHECK (publication_year IS NULL OR (publication_year >= 1900 AND publication_year <= 2100)), 
    UNIQUE (doi), 
    UNIQUE (pmid)
);

CREATE INDEX ix_publication_publication_year ON publication (publication_year);

CREATE TABLE biomarker_cancer (
    association_id SERIAL NOT NULL, 
    biomarker_id INTEGER NOT NULL, 
    cancer_id INTEGER NOT NULL, 
    biomarker_role VARCHAR(20) NOT NULL, 
    association_description TEXT, 
    source_status VARCHAR(30) NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    PRIMARY KEY (association_id), 
    CONSTRAINT ck_biomarker_role CHECK (biomarker_role IN ('diagnostic', 'prognostic', 'predictive', 'risk', 'monitoring')), 
    CONSTRAINT ck_source_status CHECK (source_status IN ('curated_literature', 'database_annotation', 'computational_prediction', 'synthetic_demo', 'pending_curation')), 
    FOREIGN KEY(biomarker_id) REFERENCES biomarker (biomarker_id) ON DELETE CASCADE, 
    FOREIGN KEY(cancer_id) REFERENCES cancer (cancer_id) ON DELETE RESTRICT, 
    CONSTRAINT uq_biomarker_cancer_role UNIQUE (biomarker_id, cancer_id, biomarker_role)
);

CREATE INDEX ix_biomarker_cancer_biomarker_id ON biomarker_cancer (biomarker_id);

CREATE INDEX ix_biomarker_cancer_cancer_id ON biomarker_cancer (cancer_id);

CREATE INDEX ix_biomarker_cancer_cancer_role ON biomarker_cancer (cancer_id, biomarker_role);

CREATE TABLE biomarker_gene (
    biomarker_id INTEGER NOT NULL, 
    gene_id INTEGER NOT NULL, 
    PRIMARY KEY (biomarker_id, gene_id), 
    FOREIGN KEY(biomarker_id) REFERENCES biomarker (biomarker_id) ON DELETE CASCADE, 
    FOREIGN KEY(gene_id) REFERENCES gene (gene_id) ON DELETE CASCADE
);

CREATE INDEX ix_biomarker_gene_gene_id ON biomarker_gene (gene_id);

CREATE TABLE biomarker_pathway (
    biomarker_id INTEGER NOT NULL, 
    pathway_id INTEGER NOT NULL, 
    annotation_source VARCHAR(100), 
    PRIMARY KEY (biomarker_id, pathway_id), 
    FOREIGN KEY(biomarker_id) REFERENCES biomarker (biomarker_id) ON DELETE CASCADE, 
    FOREIGN KEY(pathway_id) REFERENCES pathway (pathway_id) ON DELETE CASCADE
);

CREATE INDEX ix_biomarker_pathway_pathway_id ON biomarker_pathway (pathway_id);

CREATE TABLE gene_pathway (
    gene_id INTEGER NOT NULL, 
    pathway_id INTEGER NOT NULL, 
    annotation_source VARCHAR(100), 
    PRIMARY KEY (gene_id, pathway_id), 
    FOREIGN KEY(gene_id) REFERENCES gene (gene_id) ON DELETE CASCADE, 
    FOREIGN KEY(pathway_id) REFERENCES pathway (pathway_id) ON DELETE CASCADE
);

CREATE INDEX ix_gene_pathway_pathway_id ON gene_pathway (pathway_id);

CREATE TABLE gene_protein (
    gene_id INTEGER NOT NULL, 
    protein_id INTEGER NOT NULL, 
    PRIMARY KEY (gene_id, protein_id), 
    FOREIGN KEY(gene_id) REFERENCES gene (gene_id) ON DELETE CASCADE, 
    FOREIGN KEY(protein_id) REFERENCES protein (protein_id) ON DELETE CASCADE
);

CREATE INDEX ix_gene_protein_protein_id ON gene_protein (protein_id);

CREATE TABLE variant (
    variant_id SERIAL NOT NULL, 
    gene_id INTEGER NOT NULL, 
    variant_identifier VARCHAR(120) NOT NULL, 
    protein_change VARCHAR(60), 
    dbsnp_id VARCHAR(30), 
    genome_assembly VARCHAR(20), 
    chromosome VARCHAR(5), 
    position INTEGER, 
    reference_allele VARCHAR(50), 
    alternate_allele VARCHAR(50), 
    clinical_or_research_annotation TEXT, 
    source_identifier VARCHAR(100), 
    PRIMARY KEY (variant_id), 
    CONSTRAINT ck_variant_position CHECK (position IS NULL OR position > 0), 
    FOREIGN KEY(gene_id) REFERENCES gene (gene_id) ON DELETE RESTRICT, 
    UNIQUE (variant_identifier)
);

CREATE INDEX ix_variant_gene_id ON variant (gene_id);

CREATE TABLE evidence (
    evidence_id SERIAL NOT NULL, 
    association_id INTEGER NOT NULL, 
    publication_id INTEGER, 
    evidence_type VARCHAR(40), 
    source_name VARCHAR(100) NOT NULL, 
    source_record_id VARCHAR(100), 
    evidence_summary TEXT, 
    consistency_annotation VARCHAR(20), 
    retrieved_at TIMESTAMP WITH TIME ZONE, 
    source_url VARCHAR(300), 
    PRIMARY KEY (evidence_id), 
    CONSTRAINT ck_consistency_annotation CHECK (consistency_annotation IS NULL OR consistency_annotation IN ('supports', 'mixed', 'conflicting')), 
    CONSTRAINT ck_evidence_type CHECK (evidence_type IS NULL OR evidence_type IN ('meta_analysis', 'randomized_clinical_trial', 'clinical_trial', 'patient_cohort', 'clinical_guideline', 'genomic_profiling', 'experimental', 'review', 'computational_prediction')), 
    FOREIGN KEY(association_id) REFERENCES biomarker_cancer (association_id) ON DELETE CASCADE, 
    FOREIGN KEY(publication_id) REFERENCES publication (publication_id) ON DELETE SET NULL, 
    CONSTRAINT uq_evidence_assoc_pub_source UNIQUE (association_id, publication_id, source_name)
);

CREATE INDEX ix_evidence_association_id ON evidence (association_id);

CREATE INDEX ix_evidence_evidence_type ON evidence (evidence_type);

CREATE INDEX ix_evidence_publication_id ON evidence (publication_id);

CREATE TABLE evidence_score (
    score_id SERIAL NOT NULL, 
    association_id INTEGER NOT NULL, 
    publication_support_score FLOAT, 
    source_diversity_score FLOAT, 
    evidence_type_score FLOAT, 
    consistency_score FLOAT, 
    overall_score FLOAT, 
    evidence_coverage FLOAT NOT NULL, 
    score_status VARCHAR(20) NOT NULL, 
    missing_components VARCHAR(200), 
    n_publications INTEGER NOT NULL, 
    n_sources INTEGER NOT NULL, 
    scoring_version VARCHAR(20) NOT NULL, 
    calculated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    PRIMARY KEY (score_id), 
    CONSTRAINT ck_score_status CHECK (score_status IN ('complete', 'provisional', 'insufficient')), 
    CONSTRAINT ck_evidence_coverage CHECK (evidence_coverage >= 0 AND evidence_coverage <= 1), 
    CONSTRAINT ck_overall_score CHECK (overall_score IS NULL OR (overall_score >= 0 AND overall_score <= 100)), 
    FOREIGN KEY(association_id) REFERENCES biomarker_cancer (association_id) ON DELETE CASCADE, 
    CONSTRAINT uq_score_assoc_version UNIQUE (association_id, scoring_version)
);

CREATE INDEX ix_evidence_score_association_id ON evidence_score (association_id);

CREATE INDEX ix_evidence_score_overall_score ON evidence_score (overall_score);

CREATE TABLE variant_association (
    variant_id INTEGER NOT NULL, 
    association_id INTEGER NOT NULL, 
    PRIMARY KEY (variant_id, association_id), 
    FOREIGN KEY(association_id) REFERENCES biomarker_cancer (association_id) ON DELETE CASCADE, 
    FOREIGN KEY(variant_id) REFERENCES variant (variant_id) ON DELETE CASCADE
);

CREATE INDEX ix_variant_association_association_id ON variant_association (association_id);

INSERT INTO alembic_version (version_num) VALUES ('0001') RETURNING alembic_version.version_num;

COMMIT;

