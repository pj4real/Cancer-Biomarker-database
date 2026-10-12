"""Evidence-gap analysis: flags associations whose recorded evidence is thin, narrow or inconsistent."""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app import models as m
from app.services.scores import current_score

GAP_FLAGS = {
    "no_evidence": "No evidence records are stored for this association.",
    "few_publications": "Fewer than the threshold number of distinct supporting publications.",
    "single_source": "All evidence comes from a single source database.",
    "untyped_evidence": "At least one evidence record has no specified evidence type.",
    "no_consistency_annotation": "No evidence record carries a curated consistency annotation.",
    "incomplete_metadata": "Evidence or publication records are missing provenance fields "
    "(source record ID, source URL, retrieval date, or publication year/journal).",
    "inconsistent": "Documented mixed or conflicting evidence exists.",
    "low_score": "Evidence-support score below the threshold, or no score could be computed.",
}


def _incomplete(ev: m.Evidence) -> list[str]:
    missing = [f for f in ("source_record_id", "source_url", "retrieved_at") if getattr(ev, f) is None]
    if ev.publication is not None:
        missing += [f"publication.{f}" for f in ("publication_year", "journal") if getattr(ev.publication, f) is None]
    return missing


def analyse_association(assoc: m.BiomarkerCancer, min_publications: int = 2, min_score: float = 50.0) -> dict:
    evidence = assoc.evidence
    pubs = {e.publication_id for e in evidence if e.publication_id is not None}
    sources = {e.source_name.strip().lower() for e in evidence}
    score = current_score(assoc)
    flags: list[str] = []
    details: dict[str, object] = {}

    if not evidence:
        flags.append("no_evidence")
    if len(pubs) < min_publications:
        flags.append("few_publications")
    if len(sources) == 1:
        flags.append("single_source")
    untyped = [e.evidence_id for e in evidence if e.evidence_type is None]
    if untyped:
        flags.append("untyped_evidence")
        details["untyped_evidence_ids"] = untyped
    if evidence and all(e.consistency_annotation is None for e in evidence):
        flags.append("no_consistency_annotation")
    incomplete = {e.evidence_id: _incomplete(e) for e in evidence if _incomplete(e)}
    if incomplete:
        flags.append("incomplete_metadata")
        details["incomplete_fields"] = sorted({f for fs in incomplete.values() for f in fs})
    conflicting = [e for e in evidence if e.consistency_annotation in ("mixed", "conflicting")]
    if conflicting:
        flags.append("inconsistent")
        details["inconsistent_evidence"] = [
            {"evidence_id": e.evidence_id, "annotation": e.consistency_annotation, "summary": e.evidence_summary}
            for e in conflicting
        ]
    if score is None or score.overall_score is None or score.overall_score < min_score:
        flags.append("low_score")

    return {
        "association_id": assoc.association_id,
        "biomarker_id": assoc.biomarker_id,
        "biomarker_name": assoc.biomarker.name,
        "biomarker_code": assoc.biomarker.biomarker_code,
        "cancer_id": assoc.cancer_id,
        "cancer_name": assoc.cancer.name,
        "biomarker_role": assoc.biomarker_role,
        "source_status": assoc.source_status,
        "n_evidence": len(evidence),
        "n_publications": len(pubs),
        "n_sources": len(sources),
        "overall_score": score.overall_score if score else None,
        "score_status": score.score_status if score else None,
        "evidence_coverage": score.evidence_coverage if score else None,
        "flags": flags,
        "gap_count": len(flags),
        "details": details,
    }


def gap_analysis(
    db: Session,
    cancer_id: int | None = None,
    role: str | None = None,
    flag: str | None = None,
    min_publications: int = 2,
    min_score: float = 50.0,
    sort: str = "gap_count",
    order: str = "desc",
) -> list[dict]:
    q = select(m.BiomarkerCancer).options(
        selectinload(m.BiomarkerCancer.biomarker),
        selectinload(m.BiomarkerCancer.cancer),
        selectinload(m.BiomarkerCancer.evidence).selectinload(m.Evidence.publication),
        selectinload(m.BiomarkerCancer.scores),
    )
    if cancer_id is not None:
        q = q.where(m.BiomarkerCancer.cancer_id == cancer_id)
    if role is not None:
        q = q.where(m.BiomarkerCancer.biomarker_role == role)
    rows = [analyse_association(a, min_publications, min_score) for a in db.scalars(q).all()]
    if flag:
        rows = [r for r in rows if flag in r["flags"]]
    else:
        rows = [r for r in rows if r["flags"]]

    reverse = order == "desc"
    if sort == "overall_score":
        # Unknown scores always sort last regardless of direction.
        known = sorted((r for r in rows if r["overall_score"] is not None), key=lambda r: r["overall_score"], reverse=reverse)
        rows = known + [r for r in rows if r["overall_score"] is None]
    elif sort in ("n_publications", "n_sources", "gap_count"):
        rows.sort(key=lambda r: (r[sort], r["biomarker_name"]), reverse=reverse)
    else:
        rows.sort(key=lambda r: (r["biomarker_name"], r["cancer_name"]), reverse=reverse)
    return rows


def gap_summary(rows: list[dict]) -> dict[str, int]:
    return {f: sum(1 for r in rows if f in r["flags"]) for f in GAP_FLAGS}
