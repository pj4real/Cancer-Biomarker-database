"""initial schema

Revision ID: 0001
Revises: 
Create Date: 2026-10-11 13:50:31.424780
"""
from alembic import op
import sqlalchemy as sa


revision = '0001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Generated with `alembic revision --autogenerate` from app/models.py and reviewed.
    op.create_table('biomarker',
    sa.Column('biomarker_id', sa.Integer(), nullable=False),
    sa.Column('biomarker_code', sa.String(length=20), nullable=False),
    sa.Column('name', sa.String(length=200), nullable=False),
    sa.Column('biomarker_type', sa.String(length=40), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('biological_function', sa.Text(), nullable=True),
    sa.Column('external_identifier', sa.String(length=100), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.CheckConstraint("biomarker_type IN ('genetic_mutation', 'germline_variant', 'gene_fusion', 'copy_number_alteration', 'protein_expression', 'circulating_protein', 'gene_expression_signature', 'rna_transcript', 'epigenetic_methylation', 'genomic_signature')", name='ck_biomarker_type'),
    sa.PrimaryKeyConstraint('biomarker_id'),
    sa.UniqueConstraint('biomarker_code')
    )
    with op.batch_alter_table('biomarker', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_biomarker_biomarker_type'), ['biomarker_type'], unique=False)
        batch_op.create_index(batch_op.f('ix_biomarker_name'), ['name'], unique=True)

    op.create_table('cancer',
    sa.Column('cancer_id', sa.Integer(), nullable=False),
    sa.Column('code', sa.String(length=30), nullable=False),
    sa.Column('name', sa.String(length=150), nullable=False),
    sa.Column('tissue_origin', sa.String(length=100), nullable=True),
    sa.Column('cancer_category', sa.String(length=100), nullable=True),
    sa.Column('external_identifier', sa.String(length=50), nullable=True),
    sa.Column('gdc_project_id', sa.String(length=30), nullable=True),
    sa.Column('description', sa.Text(), nullable=True),
    sa.PrimaryKeyConstraint('cancer_id'),
    sa.UniqueConstraint('code'),
    sa.UniqueConstraint('name')
    )
    op.create_table('gene',
    sa.Column('gene_id', sa.Integer(), nullable=False),
    sa.Column('official_symbol', sa.String(length=30), nullable=False),
    sa.Column('full_name', sa.String(length=255), nullable=True),
    sa.Column('organism', sa.String(length=100), nullable=False),
    sa.Column('ncbi_gene_id', sa.Integer(), nullable=True),
    sa.Column('description', sa.Text(), nullable=True),
    sa.PrimaryKeyConstraint('gene_id'),
    sa.UniqueConstraint('ncbi_gene_id'),
    sa.UniqueConstraint('official_symbol')
    )
    op.create_table('pathway',
    sa.Column('pathway_id', sa.Integer(), nullable=False),
    sa.Column('pathway_name', sa.String(length=200), nullable=False),
    sa.Column('pathway_database', sa.String(length=30), nullable=False),
    sa.Column('external_identifier', sa.String(length=50), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('source_url', sa.String(length=300), nullable=True),
    sa.CheckConstraint("pathway_database IN ('KEGG', 'Reactome', 'WikiPathways', 'Other')", name='ck_pathway_database'),
    sa.PrimaryKeyConstraint('pathway_id'),
    sa.UniqueConstraint('pathway_database', 'external_identifier', name='uq_pathway_source_id')
    )
    op.create_table('protein',
    sa.Column('protein_id', sa.Integer(), nullable=False),
    sa.Column('accession', sa.String(length=20), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.Column('function', sa.Text(), nullable=True),
    sa.Column('organism', sa.String(length=100), nullable=False),
    sa.PrimaryKeyConstraint('protein_id'),
    sa.UniqueConstraint('accession')
    )
    op.create_table('publication',
    sa.Column('publication_id', sa.Integer(), nullable=False),
    sa.Column('pmid', sa.String(length=12), nullable=True),
    sa.Column('doi', sa.String(length=120), nullable=True),
    sa.Column('title', sa.Text(), nullable=False),
    sa.Column('authors', sa.Text(), nullable=True),
    sa.Column('publication_year', sa.Integer(), nullable=True),
    sa.Column('journal', sa.String(length=200), nullable=True),
    sa.Column('source_url', sa.String(length=300), nullable=True),
    sa.CheckConstraint('pmid IS NOT NULL OR doi IS NOT NULL', name='ck_publication_identifier'),
    sa.CheckConstraint('publication_year IS NULL OR (publication_year >= 1900 AND publication_year <= 2100)', name='ck_publication_year'),
    sa.PrimaryKeyConstraint('publication_id'),
    sa.UniqueConstraint('doi'),
    sa.UniqueConstraint('pmid')
    )
    with op.batch_alter_table('publication', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_publication_publication_year'), ['publication_year'], unique=False)

    op.create_table('biomarker_cancer',
    sa.Column('association_id', sa.Integer(), nullable=False),
    sa.Column('biomarker_id', sa.Integer(), nullable=False),
    sa.Column('cancer_id', sa.Integer(), nullable=False),
    sa.Column('biomarker_role', sa.String(length=20), nullable=False),
    sa.Column('association_description', sa.Text(), nullable=True),
    sa.Column('source_status', sa.String(length=30), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.CheckConstraint("biomarker_role IN ('diagnostic', 'prognostic', 'predictive', 'risk', 'monitoring')", name='ck_biomarker_role'),
    sa.CheckConstraint("source_status IN ('curated_literature', 'database_annotation', 'computational_prediction', 'synthetic_demo', 'pending_curation')", name='ck_source_status'),
    sa.ForeignKeyConstraint(['biomarker_id'], ['biomarker.biomarker_id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['cancer_id'], ['cancer.cancer_id'], ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('association_id'),
    sa.UniqueConstraint('biomarker_id', 'cancer_id', 'biomarker_role', name='uq_biomarker_cancer_role')
    )
    with op.batch_alter_table('biomarker_cancer', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_biomarker_cancer_biomarker_id'), ['biomarker_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_biomarker_cancer_cancer_id'), ['cancer_id'], unique=False)
        batch_op.create_index('ix_biomarker_cancer_cancer_role', ['cancer_id', 'biomarker_role'], unique=False)

    op.create_table('biomarker_gene',
    sa.Column('biomarker_id', sa.Integer(), nullable=False),
    sa.Column('gene_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['biomarker_id'], ['biomarker.biomarker_id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['gene_id'], ['gene.gene_id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('biomarker_id', 'gene_id')
    )
    with op.batch_alter_table('biomarker_gene', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_biomarker_gene_gene_id'), ['gene_id'], unique=False)

    op.create_table('biomarker_pathway',
    sa.Column('biomarker_id', sa.Integer(), nullable=False),
    sa.Column('pathway_id', sa.Integer(), nullable=False),
    sa.Column('annotation_source', sa.String(length=100), nullable=True),
    sa.ForeignKeyConstraint(['biomarker_id'], ['biomarker.biomarker_id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['pathway_id'], ['pathway.pathway_id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('biomarker_id', 'pathway_id')
    )
    with op.batch_alter_table('biomarker_pathway', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_biomarker_pathway_pathway_id'), ['pathway_id'], unique=False)

    op.create_table('gene_pathway',
    sa.Column('gene_id', sa.Integer(), nullable=False),
    sa.Column('pathway_id', sa.Integer(), nullable=False),
    sa.Column('annotation_source', sa.String(length=100), nullable=True),
    sa.ForeignKeyConstraint(['gene_id'], ['gene.gene_id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['pathway_id'], ['pathway.pathway_id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('gene_id', 'pathway_id')
    )
    with op.batch_alter_table('gene_pathway', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_gene_pathway_pathway_id'), ['pathway_id'], unique=False)

    op.create_table('gene_protein',
    sa.Column('gene_id', sa.Integer(), nullable=False),
    sa.Column('protein_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['gene_id'], ['gene.gene_id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['protein_id'], ['protein.protein_id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('gene_id', 'protein_id')
    )
    with op.batch_alter_table('gene_protein', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_gene_protein_protein_id'), ['protein_id'], unique=False)

    op.create_table('variant',
    sa.Column('variant_id', sa.Integer(), nullable=False),
    sa.Column('gene_id', sa.Integer(), nullable=False),
    sa.Column('variant_identifier', sa.String(length=120), nullable=False),
    sa.Column('protein_change', sa.String(length=60), nullable=True),
    sa.Column('dbsnp_id', sa.String(length=30), nullable=True),
    sa.Column('genome_assembly', sa.String(length=20), nullable=True),
    sa.Column('chromosome', sa.String(length=5), nullable=True),
    sa.Column('position', sa.Integer(), nullable=True),
    sa.Column('reference_allele', sa.String(length=50), nullable=True),
    sa.Column('alternate_allele', sa.String(length=50), nullable=True),
    sa.Column('clinical_or_research_annotation', sa.Text(), nullable=True),
    sa.Column('source_identifier', sa.String(length=100), nullable=True),
    sa.CheckConstraint('position IS NULL OR position > 0', name='ck_variant_position'),
    sa.ForeignKeyConstraint(['gene_id'], ['gene.gene_id'], ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('variant_id'),
    sa.UniqueConstraint('variant_identifier')
    )
    with op.batch_alter_table('variant', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_variant_gene_id'), ['gene_id'], unique=False)

    op.create_table('evidence',
    sa.Column('evidence_id', sa.Integer(), nullable=False),
    sa.Column('association_id', sa.Integer(), nullable=False),
    sa.Column('publication_id', sa.Integer(), nullable=True),
    sa.Column('evidence_type', sa.String(length=40), nullable=True),
    sa.Column('source_name', sa.String(length=100), nullable=False),
    sa.Column('source_record_id', sa.String(length=100), nullable=True),
    sa.Column('evidence_summary', sa.Text(), nullable=True),
    sa.Column('consistency_annotation', sa.String(length=20), nullable=True),
    sa.Column('retrieved_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('source_url', sa.String(length=300), nullable=True),
    sa.CheckConstraint("consistency_annotation IS NULL OR consistency_annotation IN ('supports', 'mixed', 'conflicting')", name='ck_consistency_annotation'),
    sa.CheckConstraint("evidence_type IS NULL OR evidence_type IN ('meta_analysis', 'randomized_clinical_trial', 'clinical_trial', 'patient_cohort', 'clinical_guideline', 'genomic_profiling', 'experimental', 'review', 'computational_prediction')", name='ck_evidence_type'),
    sa.ForeignKeyConstraint(['association_id'], ['biomarker_cancer.association_id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['publication_id'], ['publication.publication_id'], ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('evidence_id'),
    sa.UniqueConstraint('association_id', 'publication_id', 'source_name', name='uq_evidence_assoc_pub_source')
    )
    with op.batch_alter_table('evidence', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_evidence_association_id'), ['association_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_evidence_evidence_type'), ['evidence_type'], unique=False)
        batch_op.create_index(batch_op.f('ix_evidence_publication_id'), ['publication_id'], unique=False)

    op.create_table('evidence_score',
    sa.Column('score_id', sa.Integer(), nullable=False),
    sa.Column('association_id', sa.Integer(), nullable=False),
    sa.Column('publication_support_score', sa.Float(), nullable=True),
    sa.Column('source_diversity_score', sa.Float(), nullable=True),
    sa.Column('evidence_type_score', sa.Float(), nullable=True),
    sa.Column('consistency_score', sa.Float(), nullable=True),
    sa.Column('overall_score', sa.Float(), nullable=True),
    sa.Column('evidence_coverage', sa.Float(), nullable=False),
    sa.Column('score_status', sa.String(length=20), nullable=False),
    sa.Column('missing_components', sa.String(length=200), nullable=True),
    sa.Column('n_publications', sa.Integer(), nullable=False),
    sa.Column('n_sources', sa.Integer(), nullable=False),
    sa.Column('scoring_version', sa.String(length=20), nullable=False),
    sa.Column('calculated_at', sa.DateTime(timezone=True), nullable=False),
    sa.CheckConstraint("score_status IN ('complete', 'provisional', 'insufficient')", name='ck_score_status'),
    sa.CheckConstraint('evidence_coverage >= 0 AND evidence_coverage <= 1', name='ck_evidence_coverage'),
    sa.CheckConstraint('overall_score IS NULL OR (overall_score >= 0 AND overall_score <= 100)', name='ck_overall_score'),
    sa.ForeignKeyConstraint(['association_id'], ['biomarker_cancer.association_id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('score_id'),
    sa.UniqueConstraint('association_id', 'scoring_version', name='uq_score_assoc_version')
    )
    with op.batch_alter_table('evidence_score', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_evidence_score_association_id'), ['association_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_evidence_score_overall_score'), ['overall_score'], unique=False)

    op.create_table('variant_association',
    sa.Column('variant_id', sa.Integer(), nullable=False),
    sa.Column('association_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['association_id'], ['biomarker_cancer.association_id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['variant_id'], ['variant.variant_id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('variant_id', 'association_id')
    )
    with op.batch_alter_table('variant_association', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_variant_association_association_id'), ['association_id'], unique=False)



def downgrade() -> None:
    # Generated with `alembic revision --autogenerate` from app/models.py and reviewed.
    with op.batch_alter_table('variant_association', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_variant_association_association_id'))

    op.drop_table('variant_association')
    with op.batch_alter_table('evidence_score', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_evidence_score_overall_score'))
        batch_op.drop_index(batch_op.f('ix_evidence_score_association_id'))

    op.drop_table('evidence_score')
    with op.batch_alter_table('evidence', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_evidence_publication_id'))
        batch_op.drop_index(batch_op.f('ix_evidence_evidence_type'))
        batch_op.drop_index(batch_op.f('ix_evidence_association_id'))

    op.drop_table('evidence')
    with op.batch_alter_table('variant', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_variant_gene_id'))

    op.drop_table('variant')
    with op.batch_alter_table('gene_protein', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_gene_protein_protein_id'))

    op.drop_table('gene_protein')
    with op.batch_alter_table('gene_pathway', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_gene_pathway_pathway_id'))

    op.drop_table('gene_pathway')
    with op.batch_alter_table('biomarker_pathway', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_biomarker_pathway_pathway_id'))

    op.drop_table('biomarker_pathway')
    with op.batch_alter_table('biomarker_gene', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_biomarker_gene_gene_id'))

    op.drop_table('biomarker_gene')
    with op.batch_alter_table('biomarker_cancer', schema=None) as batch_op:
        batch_op.drop_index('ix_biomarker_cancer_cancer_role')
        batch_op.drop_index(batch_op.f('ix_biomarker_cancer_cancer_id'))
        batch_op.drop_index(batch_op.f('ix_biomarker_cancer_biomarker_id'))

    op.drop_table('biomarker_cancer')
    with op.batch_alter_table('publication', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_publication_publication_year'))

    op.drop_table('publication')
    op.drop_table('protein')
    op.drop_table('pathway')
    op.drop_table('gene')
    op.drop_table('cancer')
    with op.batch_alter_table('biomarker', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_biomarker_name'))
        batch_op.drop_index(batch_op.f('ix_biomarker_biomarker_type'))

    op.drop_table('biomarker')
