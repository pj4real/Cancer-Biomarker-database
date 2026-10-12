"""Schema integrity: foreign keys, unique and check constraints, cascades, migrations."""
import pytest
from sqlalchemy import create_engine, inspect, select
from sqlalchemy.exc import IntegrityError

from app import models as m
from app.database import Base


def _cancer(db, code="test"):
    c = m.Cancer(code=code, name=f"{code} cancer")
    db.add(c)
    db.flush()
    return c


def _biomarker(db, code="T-1"):
    b = m.Biomarker(biomarker_code=code, name=f"marker {code}", biomarker_type="genetic_mutation")
    db.add(b)
    db.flush()
    return b


def test_foreign_key_enforced(empty_db):
    b = _biomarker(empty_db)
    empty_db.add(m.BiomarkerCancer(biomarker_id=b.biomarker_id, cancer_id=999, biomarker_role="diagnostic"))
    with pytest.raises(IntegrityError):
        empty_db.flush()


def test_duplicate_gene_symbol_rejected(empty_db):
    empty_db.add(m.Gene(official_symbol="TP53", ncbi_gene_id=7157))
    empty_db.flush()
    empty_db.add(m.Gene(official_symbol="TP53"))
    with pytest.raises(IntegrityError):
        empty_db.flush()


def test_duplicate_pmid_rejected(empty_db):
    empty_db.add(m.Publication(pmid="1", title="a"))
    empty_db.flush()
    empty_db.add(m.Publication(pmid="1", title="b"))
    with pytest.raises(IntegrityError):
        empty_db.flush()


def test_publication_requires_identifier(empty_db):
    empty_db.add(m.Publication(title="no identifiers"))
    with pytest.raises(IntegrityError):
        empty_db.flush()


def test_duplicate_association_rejected(empty_db):
    b, c = _biomarker(empty_db), _cancer(empty_db)
    empty_db.add(m.BiomarkerCancer(biomarker_id=b.biomarker_id, cancer_id=c.cancer_id, biomarker_role="predictive"))
    empty_db.flush()
    empty_db.add(m.BiomarkerCancer(biomarker_id=b.biomarker_id, cancer_id=c.cancer_id, biomarker_role="predictive"))
    with pytest.raises(IntegrityError):
        empty_db.flush()


def test_same_pair_different_role_allowed(empty_db):
    b, c = _biomarker(empty_db), _cancer(empty_db)
    for role in ("predictive", "prognostic"):
        empty_db.add(m.BiomarkerCancer(biomarker_id=b.biomarker_id, cancer_id=c.cancer_id, biomarker_role=role))
    empty_db.flush()


@pytest.mark.parametrize("field,value", [("biomarker_role", "cure"), ("source_status", "rumour")])
def test_check_constraints_on_association(empty_db, field, value):
    b, c = _biomarker(empty_db), _cancer(empty_db)
    kwargs = {"biomarker_id": b.biomarker_id, "cancer_id": c.cancer_id, "biomarker_role": "diagnostic",
              "source_status": "curated_literature", field: value}
    empty_db.add(m.BiomarkerCancer(**kwargs))
    with pytest.raises(IntegrityError):
        empty_db.flush()


def test_invalid_consistency_annotation_rejected(empty_db):
    b, c = _biomarker(empty_db), _cancer(empty_db)
    a = m.BiomarkerCancer(biomarker_id=b.biomarker_id, cancer_id=c.cancer_id, biomarker_role="diagnostic")
    empty_db.add(a)
    empty_db.flush()
    empty_db.add(m.Evidence(association_id=a.association_id, source_name="PubMed", consistency_annotation="agree"))
    with pytest.raises(IntegrityError):
        empty_db.flush()


def test_deleting_biomarker_cascades_to_association_and_evidence(empty_db):
    b, c = _biomarker(empty_db), _cancer(empty_db)
    a = m.BiomarkerCancer(biomarker_id=b.biomarker_id, cancer_id=c.cancer_id, biomarker_role="diagnostic")
    empty_db.add(a)
    empty_db.flush()
    empty_db.add(m.Evidence(association_id=a.association_id, source_name="PubMed"))
    empty_db.commit()
    empty_db.delete(b)
    empty_db.commit()
    assert empty_db.scalar(select(m.Evidence)) is None
    assert empty_db.scalar(select(m.BiomarkerCancer)) is None


def test_relationship_navigation(db):
    """Cancer -> Biomarker -> Gene -> Protein -> Pathway -> Publication."""
    cancer = db.scalars(select(m.Cancer).filter_by(code="breast")).one()
    assoc = next(a for a in cancer.associations
                 if a.biomarker.biomarker_code == "CBM-003" and a.biomarker_role == "predictive")
    gene = assoc.biomarker.genes[0]
    assert gene.official_symbol == "ERBB2"
    assert gene.proteins[0].accession == "P04626"
    assert "hsa04012" in {p.external_identifier for p in gene.pathways}
    assert "11248153" in {e.publication.pmid for e in assoc.evidence if e.publication}


def test_alembic_migration_matches_models(tmp_path, monkeypatch):
    from alembic import command
    from alembic.config import Config

    from app.config import BACKEND_DIR

    url = f"sqlite:///{(tmp_path / 'mig.db').as_posix()}"
    cfg = Config(str(BACKEND_DIR / "alembic.ini"))
    cfg.set_main_option("script_location", str(BACKEND_DIR / "alembic"))
    cfg.attributes["database_url"] = url
    command.upgrade(cfg, "head")
    tables = set(inspect(create_engine(url)).get_table_names()) - {"alembic_version"}
    assert tables == set(Base.metadata.tables)
