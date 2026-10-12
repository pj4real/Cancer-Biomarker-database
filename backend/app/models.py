"""SQLAlchemy ORM models: the normalized relational schema of CancerBioMap.

Every table uses a surrogate integer primary key plus a UNIQUE natural key
(gene symbol, UniProt accession, PMID, ...) to prevent duplicates on import.
Many-to-many relationships use junction tables with composite primary keys.
"""
from datetime import datetime, timezone

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.vocab import (
    BIOMARKER_ROLES,
    BIOMARKER_TYPES,
    CONSISTENCY_VALUES,
    EVIDENCE_TYPES,
    PATHWAY_DATABASES,
    SOURCE_STATUSES,
    sql_in,
)


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


# --------------------------------------------------------------------------- core entities
class Biomarker(Base):
    __tablename__ = "biomarker"
    __table_args__ = (
        CheckConstraint(f"biomarker_type IN {sql_in(BIOMARKER_TYPES)}", name="ck_biomarker_type"),
    )

    biomarker_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    biomarker_code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(200), unique=True, nullable=False, index=True)
    biomarker_type: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text)
    biological_function: Mapped[str | None] = mapped_column(Text)
    external_identifier: Mapped[str | None] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    genes: Mapped[list["Gene"]] = relationship(secondary="biomarker_gene", back_populates="biomarkers")
    pathways: Mapped[list["Pathway"]] = relationship(secondary="biomarker_pathway", back_populates="biomarkers")
    associations: Mapped[list["BiomarkerCancer"]] = relationship(
        back_populates="biomarker", cascade="all, delete-orphan"
    )


class Gene(Base):
    __tablename__ = "gene"

    gene_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    official_symbol: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(255))
    organism: Mapped[str] = mapped_column(String(100), nullable=False, default="Homo sapiens")
    ncbi_gene_id: Mapped[int | None] = mapped_column(Integer, unique=True)
    description: Mapped[str | None] = mapped_column(Text)

    biomarkers: Mapped[list[Biomarker]] = relationship(secondary="biomarker_gene", back_populates="genes")
    proteins: Mapped[list["Protein"]] = relationship(secondary="gene_protein", back_populates="genes")
    pathways: Mapped[list["Pathway"]] = relationship(secondary="gene_pathway", back_populates="genes")
    variants: Mapped[list["Variant"]] = relationship(back_populates="gene")


class Protein(Base):
    __tablename__ = "protein"

    protein_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    accession: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    function: Mapped[str | None] = mapped_column(Text)
    organism: Mapped[str] = mapped_column(String(100), nullable=False, default="Homo sapiens")

    genes: Mapped[list[Gene]] = relationship(secondary="gene_protein", back_populates="proteins")


class Cancer(Base):
    __tablename__ = "cancer"

    cancer_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(150), unique=True, nullable=False)
    tissue_origin: Mapped[str | None] = mapped_column(String(100))
    cancer_category: Mapped[str | None] = mapped_column(String(100))
    external_identifier: Mapped[str | None] = mapped_column(String(50))
    gdc_project_id: Mapped[str | None] = mapped_column(String(30))
    description: Mapped[str | None] = mapped_column(Text)

    associations: Mapped[list["BiomarkerCancer"]] = relationship(back_populates="cancer")


class Variant(Base):
    __tablename__ = "variant"
    __table_args__ = (CheckConstraint("position IS NULL OR position > 0", name="ck_variant_position"),)

    variant_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    gene_id: Mapped[int] = mapped_column(
        ForeignKey("gene.gene_id", ondelete="RESTRICT"), nullable=False, index=True
    )
    variant_identifier: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    protein_change: Mapped[str | None] = mapped_column(String(60))
    dbsnp_id: Mapped[str | None] = mapped_column(String(30))
    genome_assembly: Mapped[str | None] = mapped_column(String(20))
    chromosome: Mapped[str | None] = mapped_column(String(5))
    position: Mapped[int | None] = mapped_column(Integer)
    reference_allele: Mapped[str | None] = mapped_column(String(50))
    alternate_allele: Mapped[str | None] = mapped_column(String(50))
    clinical_or_research_annotation: Mapped[str | None] = mapped_column(Text)
    source_identifier: Mapped[str | None] = mapped_column(String(100))

    gene: Mapped[Gene] = relationship(back_populates="variants")
    associations: Mapped[list["BiomarkerCancer"]] = relationship(
        secondary="variant_association", back_populates="variants"
    )


class Pathway(Base):
    __tablename__ = "pathway"
    __table_args__ = (
        UniqueConstraint("pathway_database", "external_identifier", name="uq_pathway_source_id"),
        CheckConstraint(f"pathway_database IN {sql_in(PATHWAY_DATABASES)}", name="ck_pathway_database"),
    )

    pathway_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    pathway_name: Mapped[str] = mapped_column(String(200), nullable=False)
    pathway_database: Mapped[str] = mapped_column(String(30), nullable=False)
    external_identifier: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    source_url: Mapped[str | None] = mapped_column(String(300))

    biomarkers: Mapped[list[Biomarker]] = relationship(secondary="biomarker_pathway", back_populates="pathways")
    genes: Mapped[list[Gene]] = relationship(secondary="gene_pathway", back_populates="pathways")


class Publication(Base):
    __tablename__ = "publication"
    __table_args__ = (
        CheckConstraint(
            "publication_year IS NULL OR (publication_year >= 1900 AND publication_year <= 2100)",
            name="ck_publication_year",
        ),
        CheckConstraint("pmid IS NOT NULL OR doi IS NOT NULL", name="ck_publication_identifier"),
    )

    publication_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    pmid: Mapped[str | None] = mapped_column(String(12), unique=True)
    doi: Mapped[str | None] = mapped_column(String(120), unique=True)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    authors: Mapped[str | None] = mapped_column(Text)
    publication_year: Mapped[int | None] = mapped_column(Integer, index=True)
    journal: Mapped[str | None] = mapped_column(String(200))
    source_url: Mapped[str | None] = mapped_column(String(300))

    evidence: Mapped[list["Evidence"]] = relationship(back_populates="publication")


# --------------------------------------------------------------------------- association & evidence
class BiomarkerCancer(Base):
    """A biomarker-cancer association *for one role* (e.g. HER2 / breast / predictive)."""

    __tablename__ = "biomarker_cancer"
    __table_args__ = (
        UniqueConstraint("biomarker_id", "cancer_id", "biomarker_role", name="uq_biomarker_cancer_role"),
        CheckConstraint(f"biomarker_role IN {sql_in(BIOMARKER_ROLES)}", name="ck_biomarker_role"),
        CheckConstraint(f"source_status IN {sql_in(SOURCE_STATUSES)}", name="ck_source_status"),
        Index("ix_biomarker_cancer_cancer_role", "cancer_id", "biomarker_role"),
    )

    association_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    biomarker_id: Mapped[int] = mapped_column(
        ForeignKey("biomarker.biomarker_id", ondelete="CASCADE"), nullable=False, index=True
    )
    cancer_id: Mapped[int] = mapped_column(
        ForeignKey("cancer.cancer_id", ondelete="RESTRICT"), nullable=False, index=True
    )
    biomarker_role: Mapped[str] = mapped_column(String(20), nullable=False)
    association_description: Mapped[str | None] = mapped_column(Text)
    source_status: Mapped[str] = mapped_column(String(30), nullable=False, default="curated_literature")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    biomarker: Mapped[Biomarker] = relationship(back_populates="associations")
    cancer: Mapped[Cancer] = relationship(back_populates="associations")
    evidence: Mapped[list["Evidence"]] = relationship(back_populates="association", cascade="all, delete-orphan")
    variants: Mapped[list[Variant]] = relationship(secondary="variant_association", back_populates="associations")
    scores: Mapped[list["EvidenceScore"]] = relationship(back_populates="association", cascade="all, delete-orphan")


class Evidence(Base):
    __tablename__ = "evidence"
    __table_args__ = (
        CheckConstraint(
            f"evidence_type IS NULL OR evidence_type IN {sql_in(EVIDENCE_TYPES)}", name="ck_evidence_type"
        ),
        CheckConstraint(
            f"consistency_annotation IS NULL OR consistency_annotation IN {sql_in(CONSISTENCY_VALUES)}",
            name="ck_consistency_annotation",
        ),
        # The same publication cannot be recorded twice for the same association and source.
        UniqueConstraint("association_id", "publication_id", "source_name", name="uq_evidence_assoc_pub_source"),
    )

    evidence_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    association_id: Mapped[int] = mapped_column(
        ForeignKey("biomarker_cancer.association_id", ondelete="CASCADE"), nullable=False, index=True
    )
    publication_id: Mapped[int | None] = mapped_column(
        ForeignKey("publication.publication_id", ondelete="SET NULL"), index=True
    )
    evidence_type: Mapped[str | None] = mapped_column(String(40), index=True)
    source_name: Mapped[str] = mapped_column(String(100), nullable=False)
    source_record_id: Mapped[str | None] = mapped_column(String(100))
    evidence_summary: Mapped[str | None] = mapped_column(Text)
    consistency_annotation: Mapped[str | None] = mapped_column(String(20))
    retrieved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    source_url: Mapped[str | None] = mapped_column(String(300))

    association: Mapped[BiomarkerCancer] = relationship(back_populates="evidence")
    publication: Mapped[Publication | None] = relationship(back_populates="evidence")


class EvidenceScore(Base):
    """Stored output of the evidence-support scoring module (one row per association + version)."""

    __tablename__ = "evidence_score"
    __table_args__ = (
        UniqueConstraint("association_id", "scoring_version", name="uq_score_assoc_version"),
        CheckConstraint(
            "overall_score IS NULL OR (overall_score >= 0 AND overall_score <= 100)", name="ck_overall_score"
        ),
        CheckConstraint("evidence_coverage >= 0 AND evidence_coverage <= 1", name="ck_evidence_coverage"),
        CheckConstraint("score_status IN ('complete', 'provisional', 'insufficient')", name="ck_score_status"),
    )

    score_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    association_id: Mapped[int] = mapped_column(
        ForeignKey("biomarker_cancer.association_id", ondelete="CASCADE"), nullable=False, index=True
    )
    # NULL component = unknown (not observed). It is never silently replaced by zero.
    publication_support_score: Mapped[float | None] = mapped_column(Float)
    source_diversity_score: Mapped[float | None] = mapped_column(Float)
    evidence_type_score: Mapped[float | None] = mapped_column(Float)
    consistency_score: Mapped[float | None] = mapped_column(Float)
    overall_score: Mapped[float | None] = mapped_column(Float, index=True)
    evidence_coverage: Mapped[float] = mapped_column(Float, nullable=False)
    score_status: Mapped[str] = mapped_column(String(20), nullable=False)
    missing_components: Mapped[str | None] = mapped_column(String(200))
    n_publications: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    n_sources: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    scoring_version: Mapped[str] = mapped_column(String(20), nullable=False)
    calculated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    association: Mapped[BiomarkerCancer] = relationship(back_populates="scores")


# --------------------------------------------------------------------------- junction tables
class BiomarkerGene(Base):
    __tablename__ = "biomarker_gene"
    biomarker_id: Mapped[int] = mapped_column(
        ForeignKey("biomarker.biomarker_id", ondelete="CASCADE"), primary_key=True
    )
    gene_id: Mapped[int] = mapped_column(ForeignKey("gene.gene_id", ondelete="CASCADE"), primary_key=True, index=True)


class BiomarkerPathway(Base):
    __tablename__ = "biomarker_pathway"
    biomarker_id: Mapped[int] = mapped_column(
        ForeignKey("biomarker.biomarker_id", ondelete="CASCADE"), primary_key=True
    )
    pathway_id: Mapped[int] = mapped_column(
        ForeignKey("pathway.pathway_id", ondelete="CASCADE"), primary_key=True, index=True
    )
    annotation_source: Mapped[str | None] = mapped_column(String(100))


class GeneProtein(Base):
    __tablename__ = "gene_protein"
    gene_id: Mapped[int] = mapped_column(ForeignKey("gene.gene_id", ondelete="CASCADE"), primary_key=True)
    protein_id: Mapped[int] = mapped_column(
        ForeignKey("protein.protein_id", ondelete="CASCADE"), primary_key=True, index=True
    )


class GenePathway(Base):
    """Gene membership of a pathway as stated by the pathway database (e.g. KEGG REST link)."""

    __tablename__ = "gene_pathway"
    gene_id: Mapped[int] = mapped_column(ForeignKey("gene.gene_id", ondelete="CASCADE"), primary_key=True)
    pathway_id: Mapped[int] = mapped_column(
        ForeignKey("pathway.pathway_id", ondelete="CASCADE"), primary_key=True, index=True
    )
    annotation_source: Mapped[str | None] = mapped_column(String(100))


class VariantAssociation(Base):
    __tablename__ = "variant_association"
    variant_id: Mapped[int] = mapped_column(ForeignKey("variant.variant_id", ondelete="CASCADE"), primary_key=True)
    association_id: Mapped[int] = mapped_column(
        ForeignKey("biomarker_cancer.association_id", ondelete="CASCADE"), primary_key=True, index=True
    )
