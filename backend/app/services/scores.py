"""Bridge between the database and the pure scoring module (app.scoring)."""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app import models as m
from app.config import Settings, get_settings
from app.scoring import SCORING_VERSION, EvidenceItem, ScoreResult, ScoreWeights, compute_score


def weights_from_settings(settings: Settings) -> ScoreWeights:
    return ScoreWeights(
        publication_support=settings.score_weight_publication,
        source_diversity=settings.score_weight_source_diversity,
        evidence_type=settings.score_weight_evidence_type,
        consistency=settings.score_weight_consistency,
    )


def evidence_items(assoc: m.BiomarkerCancer) -> list[EvidenceItem]:
    items = []
    for ev in assoc.evidence:
        pub = ev.publication
        key = None
        if pub is not None:
            # De-duplicate studies on their identifier, not on the evidence row.
            key = f"pmid:{pub.pmid}" if pub.pmid else f"doi:{(pub.doi or '').lower()}"
        items.append(EvidenceItem(key, ev.source_name, ev.evidence_type, ev.consistency_annotation))
    return items


def score_association(assoc: m.BiomarkerCancer, settings: Settings | None = None) -> ScoreResult:
    settings = settings or get_settings()
    return compute_score(
        evidence_items(assoc),
        weights=weights_from_settings(settings),
        publication_cap=settings.score_publication_cap,
        min_coverage=settings.score_min_coverage,
    )


def recompute_all(db: Session, settings: Settings | None = None) -> int:
    """Recalculate and upsert EvidenceScore rows for every association (current scoring version)."""
    settings = settings or get_settings()
    assocs = db.scalars(
        select(m.BiomarkerCancer).options(
            selectinload(m.BiomarkerCancer.evidence).selectinload(m.Evidence.publication),
            selectinload(m.BiomarkerCancer.scores),
        )
    ).all()
    for assoc in assocs:
        res = score_association(assoc, settings)
        row = next((s for s in assoc.scores if s.scoring_version == SCORING_VERSION), None)
        if row is None:
            row = m.EvidenceScore(association_id=assoc.association_id, scoring_version=SCORING_VERSION)
            db.add(row)
        row.publication_support_score = res.publication_support
        row.source_diversity_score = res.source_diversity
        row.evidence_type_score = res.evidence_type
        row.consistency_score = res.consistency
        row.overall_score = res.overall_score
        row.evidence_coverage = res.evidence_coverage
        row.score_status = res.score_status
        row.missing_components = ",".join(res.missing_components) or None
        row.n_publications = res.n_publications
        row.n_sources = res.n_sources
        row.calculated_at = m.utcnow()
    db.commit()
    return len(assocs)


def score_to_dict(row: m.EvidenceScore | None) -> dict | None:
    if row is None:
        return None
    return {
        "publication_support": row.publication_support_score,
        "source_diversity": row.source_diversity_score,
        "evidence_type": row.evidence_type_score,
        "consistency": row.consistency_score,
        "overall_score": row.overall_score,
        "evidence_coverage": row.evidence_coverage,
        "score_status": row.score_status,
        "missing_components": row.missing_components.split(",") if row.missing_components else [],
        "n_publications": row.n_publications,
        "n_sources": row.n_sources,
        "scoring_version": row.scoring_version,
        "calculated_at": row.calculated_at,
    }


def current_score(assoc: m.BiomarkerCancer) -> m.EvidenceScore | None:
    return next((s for s in assoc.scores if s.scoring_version == SCORING_VERSION), None)
