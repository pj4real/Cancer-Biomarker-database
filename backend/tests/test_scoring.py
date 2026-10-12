"""Evidence-support score: manually verified cases, missing-data handling and determinism."""
import math

import pytest

from app.scoring import (
    EvidenceItem,
    ScoreWeights,
    compute_score,
    consistency_score,
    evidence_type_score,
    publication_support_score,
    source_diversity_score,
)


def test_publication_support_curve():
    assert publication_support_score(0) is None  # unknown, never 0
    assert publication_support_score(1) == pytest.approx(38.69, abs=0.01)
    assert publication_support_score(3) == pytest.approx(77.37, abs=0.01)
    assert publication_support_score(5) == 100.0
    assert publication_support_score(50) == 100.0  # capped


def test_source_diversity():
    assert source_diversity_score(0) is None
    assert [source_diversity_score(n) for n in (1, 2, 3)] == [50.0, 75.0, 87.5]


def test_evidence_type_ignores_unlabelled_and_duplicates():
    assert evidence_type_score([None, None]) is None
    # max 95, distinct values {95, 80} -> 0.7*95 + 0.3*87.5 = 92.75
    assert evidence_type_score(["randomized_clinical_trial", "patient_cohort", "patient_cohort", None]) == 92.75


def test_consistency_only_uses_curated_annotations():
    assert consistency_score([None, None]) is None  # unknown is not agreement
    assert consistency_score(["supports", "conflicting"]) == 50.0
    assert consistency_score(["supports", "mixed", None]) == 75.0


def test_manual_complete_case():
    """Hand calculation:
    P = 100*log2(4)/log2(6) = 77.37 ; D = 100*(1-0.5^2) = 75
    T = 0.7*95 + 0.3*mean(95,80,65) = 90.5 ; C = 100
    Score = 0.35*77.37 + 0.25*75 + 0.25*90.5 + 0.15*100 = 83.45
    """
    items = [
        EvidenceItem("pmid:1", "PubMed", "randomized_clinical_trial", "supports"),
        EvidenceItem("pmid:2", "PubMed", "patient_cohort", "supports"),
        EvidenceItem("pmid:3", "NCI GDC (TCGA)", "genomic_profiling", None),
    ]
    r = compute_score(items)
    assert r.score_status == "complete"
    assert (r.publication_support, r.source_diversity, r.evidence_type, r.consistency) == (77.37, 75.0, 90.5, 100.0)
    assert r.overall_score == pytest.approx(83.45, abs=0.01)
    assert r.evidence_coverage == 1.0 and r.missing_components == []


def test_duplicate_records_do_not_inflate_support():
    one = [EvidenceItem("pmid:1", "PubMed", "patient_cohort", "supports")]
    dup = one * 3 + [EvidenceItem("pmid:1", "pubmed ", "patient_cohort", "supports")]
    a, b = compute_score(one), compute_score(dup)
    assert (b.n_publications, b.n_sources) == (1, 1)
    assert a.overall_score == b.overall_score


def test_missing_consistency_gives_provisional_renormalised_score():
    items = [
        EvidenceItem("pmid:1", "PubMed", "randomized_clinical_trial", None),
        EvidenceItem("pmid:2", "PubMed", "patient_cohort", None),
        EvidenceItem("pmid:3", "NCI GDC (TCGA)", "genomic_profiling", None),
    ]
    r = compute_score(items)
    assert r.score_status == "provisional"
    assert r.consistency is None and r.missing_components == ["consistency"]
    assert r.evidence_coverage == 0.85
    expected = (0.35 * 77.37 + 0.25 * 75 + 0.25 * 90.5) / 0.85
    assert r.overall_score == pytest.approx(expected, abs=0.01)


def test_insufficient_when_coverage_below_minimum():
    r = compute_score([EvidenceItem(None, "KEGG", None, None)])
    assert r.score_status == "insufficient"
    assert r.overall_score is None
    assert r.evidence_coverage == 0.25


def test_no_evidence_is_insufficient_not_zero():
    r = compute_score([])
    assert r.overall_score is None and r.score_status == "insufficient"
    assert len(r.missing_components) == 4


def test_conflicting_evidence_lowers_consistency():
    base = [EvidenceItem("pmid:1", "PubMed", "clinical_guideline", "supports")]
    conflict = base + [EvidenceItem("pmid:2", "PubMed", "clinical_guideline", "conflicting")]
    assert compute_score(conflict).consistency == 50.0


def test_deterministic_for_identical_inputs():
    items = [EvidenceItem(f"pmid:{i}", s, t, c) for i, (s, t, c) in enumerate(
        [("PubMed", "review", "mixed"), ("KEGG", None, None), ("PubMed", "experimental", "supports")])]
    results = [compute_score(list(items)).to_dict() for _ in range(5)]
    assert all(r == results[0] for r in results)


def test_custom_weights_validated_and_applied():
    with pytest.raises(ValueError):
        ScoreWeights(0.5, 0.5, 0.5, 0.5).validate()
    w = ScoreWeights(1.0, 0.0, 0.0, 0.0)
    r = compute_score([EvidenceItem("pmid:1", "PubMed", "review", "supports")], weights=w)
    assert math.isclose(r.overall_score, 38.69, abs_tol=0.01)
