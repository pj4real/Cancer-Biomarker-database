"""Browse/search endpoints: biomarkers, cancers, genes, proteins, pathways, variants, publications."""
from typing import Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.common import ERROR_RESPONSES, PageParams, bad_request, not_found, page_response
from app.database import get_db
from app.services import queries as qs
from app.vocab import BIOMARKER_ROLES, BIOMARKER_TYPES, EVIDENCE_TYPES

router = APIRouter(prefix="/api", responses=ERROR_RESPONSES)

RoleParam = Literal[BIOMARKER_ROLES]  # type: ignore[valid-type]
TypeParam = Literal[BIOMARKER_TYPES]  # type: ignore[valid-type]
EvidenceTypeParam = Literal[EVIDENCE_TYPES]  # type: ignore[valid-type]


# --------------------------------------------------------------------------- biomarkers
@router.get("/biomarkers", tags=["Biomarkers"], summary="Search and filter biomarkers")
def list_biomarkers(
    q: str | None = Query(None, max_length=100, description="Gene symbol, biomarker name or identifier"),
    cancer_id: int | None = Query(None, ge=1),
    biomarker_type: TypeParam | None = None,
    role: RoleParam | None = None,
    sort: Literal["name", "publications", "score", "code"] = "name",
    order: Literal["asc", "desc"] = "asc",
    page: PageParams = Depends(),
    db: Session = Depends(get_db),
):
    items, total = qs.list_biomarkers(db, q=q, cancer_id=cancer_id, biomarker_type=biomarker_type, role=role,
                                      sort=sort, order=order, offset=page.offset, limit=page.page_size)
    return page_response(items, total, page)


@router.get("/biomarkers/{biomarker_id}", tags=["Biomarkers"], summary="Biomarker detail with evidence and scores")
def get_biomarker(biomarker_id: int, db: Session = Depends(get_db)):
    d = qs.biomarker_detail(db, biomarker_id)
    if d is None:
        raise not_found("Biomarker", biomarker_id)
    return d


# --------------------------------------------------------------------------- cancers
@router.get("/cancers", tags=["Cancers"], summary="List cancer types")
def list_cancers(db: Session = Depends(get_db)):
    return qs.list_cancers(db)


@router.get("/cancers/compare", tags=["Cancers"], summary="Compare biomarkers of two cancers")
def compare(a: int = Query(..., ge=1), b: int = Query(..., ge=1), db: Session = Depends(get_db)):
    if a == b:
        raise bad_request("Choose two different cancers to compare")
    d = qs.compare_cancers(db, a, b)
    if d is None:
        raise not_found("Cancer", f"{a} or {b}")
    return d


@router.get("/cancers/{cancer_id}", tags=["Cancers"], summary="Cancer detail with biomarkers, genes and pathways")
def get_cancer(cancer_id: int, db: Session = Depends(get_db)):
    d = qs.cancer_detail(db, cancer_id)
    if d is None:
        raise not_found("Cancer", cancer_id)
    return d


# --------------------------------------------------------------------------- genes / proteins / pathways / variants
@router.get("/genes", tags=["Genes & proteins"])
def list_genes(q: str | None = Query(None, max_length=100), db: Session = Depends(get_db)):
    return qs.list_genes(db, q)


@router.get("/genes/{gene_id}", tags=["Genes & proteins"])
def get_gene(gene_id: int, db: Session = Depends(get_db)):
    d = qs.gene_detail(db, gene_id)
    if d is None:
        raise not_found("Gene", gene_id)
    return d


@router.get("/proteins", tags=["Genes & proteins"])
def list_proteins(q: str | None = Query(None, max_length=100), db: Session = Depends(get_db)):
    return qs.list_proteins(db, q)


@router.get("/proteins/{protein_id}", tags=["Genes & proteins"])
def get_protein(protein_id: int, db: Session = Depends(get_db)):
    d = qs.protein_detail(db, protein_id)
    if d is None:
        raise not_found("Protein", protein_id)
    return d


@router.get("/pathways", tags=["Pathways & variants"])
def list_pathways(q: str | None = Query(None, max_length=100), db: Session = Depends(get_db)):
    return qs.list_pathways(db, q)


@router.get("/pathways/{pathway_id}", tags=["Pathways & variants"])
def get_pathway(pathway_id: int, db: Session = Depends(get_db)):
    d = qs.pathway_detail(db, pathway_id)
    if d is None:
        raise not_found("Pathway", pathway_id)
    return d


@router.get("/variants", tags=["Pathways & variants"])
def list_variants(q: str | None = Query(None, max_length=100), gene_id: int | None = None,
                  db: Session = Depends(get_db)):
    return qs.list_variants(db, q, gene_id)


@router.get("/variants/{variant_id}", tags=["Pathways & variants"])
def get_variant(variant_id: int, db: Session = Depends(get_db)):
    d = qs.variant_detail(db, variant_id)
    if d is None:
        raise not_found("Variant", variant_id)
    return d


# --------------------------------------------------------------------------- publications
@router.get("/publications", tags=["Publications"], summary="Search research publications")
def list_publications(
    q: str | None = Query(None, max_length=200, description="Title, PMID, DOI, author or journal"),
    biomarker_id: int | None = Query(None, ge=1),
    cancer_id: int | None = Query(None, ge=1),
    year_from: int | None = Query(None, ge=1900, le=2100),
    year_to: int | None = Query(None, ge=1900, le=2100),
    evidence_type: EvidenceTypeParam | None = None,
    page: PageParams = Depends(),
    db: Session = Depends(get_db),
):
    if year_from and year_to and year_from > year_to:
        raise bad_request("year_from must not be greater than year_to")
    items, total = qs.list_publications(db, q=q, biomarker_id=biomarker_id, cancer_id=cancer_id,
                                        year_from=year_from, year_to=year_to, evidence_type=evidence_type,
                                        offset=page.offset, limit=page.page_size)
    return page_response(items, total, page)


# --------------------------------------------------------------------------- network
@router.get("/network", tags=["Network"], summary="Relationship graph generated from database links")
def get_network(biomarker_id: int | None = None, cancer_id: int | None = None,
                include_publications: bool = True, db: Session = Depends(get_db)):
    if (biomarker_id is None) == (cancer_id is None):
        raise bad_request("Provide exactly one of biomarker_id or cancer_id")
    d = qs.network(db, biomarker_id, cancer_id, include_publications)
    if d is None:
        raise not_found("Biomarker" if biomarker_id else "Cancer", biomarker_id or cancer_id)
    return d
