"""API behaviour: search, filters, details, analytics, gaps, export, import and error handling."""
import csv
import io


def _cancer_id(client, code):
    return next(c["cancer_id"] for c in client.get("/api/cancers").json() if c["code"] == code)


def test_health(client):
    assert client.get("/api/health").json() == {"status": "ok"}


def test_search_by_gene_symbol(client):
    names = {i["name"] for i in client.get("/api/biomarkers", params={"q": "EGFR"}).json()["items"]}
    assert names == {"EGFR activating mutation (exon 19 deletion / L858R)", "EGFR T790M resistance mutation"}


def test_search_by_code(client):
    items = client.get("/api/biomarkers", params={"q": "CBM-038"}).json()["items"]
    assert [i["name"] for i in items] == ["Prostate-specific antigen (PSA)"]


def test_filters_combine(client):
    prostate = _cancer_id(client, "prostate")
    r = client.get("/api/biomarkers", params={"cancer_id": prostate, "role": "diagnostic",
                                              "biomarker_type": "circulating_protein"}).json()
    assert [i["biomarker_code"] for i in r["items"]] == ["CBM-038"]


def test_pagination_and_sort(client):
    r = client.get("/api/biomarkers", params={"page_size": 5, "page": 2}).json()
    assert r["total"] == 47 and len(r["items"]) == 5 and r["pages"] == 10
    by_pubs = client.get("/api/biomarkers", params={"sort": "publications", "order": "desc", "page_size": 47}).json()
    counts = [i["n_publications"] for i in by_pubs["items"]]
    assert counts == sorted(counts, reverse=True)


def test_biomarker_detail_has_evidence_and_score_breakdown(client):
    bid = client.get("/api/biomarkers", params={"q": "CBM-003"}).json()["items"][0]["biomarker_id"]
    d = client.get(f"/api/biomarkers/{bid}").json()
    assert d["genes"][0]["official_symbol"] == "ERBB2"
    assert d["genes"][0]["proteins"][0]["accession"] == "P04626"
    roles = {(a["cancer"]["code"], a["biomarker_role"]) for a in d["associations"]}
    assert ("breast", "predictive") in roles and ("colorectal", "predictive") in roles
    score = next(a for a in d["associations"] if a["biomarker_role"] == "predictive"
                 and a["cancer"]["code"] == "breast")["score"]
    assert score["score_status"] == "complete" and 0 <= score["overall_score"] <= 100


def test_cancer_detail_and_compare(client):
    breast, crc = _cancer_id(client, "breast"), _cancer_id(client, "colorectal")
    d = client.get(f"/api/cancers/{breast}").json()
    assert len(d["associations"]) == 19
    assert sum(b["count"] for b in d["score_distribution"]) == 19
    cmp = client.get("/api/cancers/compare", params={"a": breast, "b": crc}).json()
    assert [s["biomarker_code"] for s in cmp["shared"]] == ["CBM-003"]  # HER2
    assert client.get("/api/cancers/compare", params={"a": breast, "b": breast}).status_code == 400


def test_publication_filters(client):
    r = client.get("/api/publications", params={"q": "17625570"}).json()
    assert r["items"][0]["title"].startswith("Identification of the transforming EML4-ALK")
    rcts = client.get("/api/publications", params={"evidence_type": "randomized_clinical_trial",
                                                   "year_from": 2015, "page_size": 100}).json()
    assert rcts["total"] > 0
    assert all(p["publication_year"] >= 2015 for p in rcts["items"])
    assert client.get("/api/publications", params={"year_from": 2020, "year_to": 2000}).status_code == 400


def test_missing_evidence_association_is_flagged_not_zero(client):
    gaps = client.get("/api/gaps", params={"flag": "no_evidence"}).json()
    assert [g["biomarker_code"] for g in gaps["items"]] == ["CBM-012"]
    item = gaps["items"][0]
    assert item["overall_score"] is None and item["score_status"] == "insufficient"


def test_conflicting_evidence_reported(client):
    items = client.get("/api/gaps", params={"flag": "inconsistent"}).json()["items"]
    codes = {(g["biomarker_code"], g["biomarker_role"]) for g in items}
    assert ("CBM-035", "diagnostic") in codes  # CEA screening: guideline evidence against


def test_association_detail_explains_score(client):
    aid = client.get("/api/associations", params={"score_status": "provisional"}).json()[0]["association_id"]
    d = client.get(f"/api/associations/{aid}").json()
    assert d["score_explanation"]["score_status"] == "provisional"
    assert "consistency" in d["score_explanation"]["missing_components"]
    assert d["score_explanation"]["method"].startswith("Provisional")


def test_analytics_reports(client):
    multi = client.get("/api/analytics/multi_cancer_biomarkers").json()
    assert {r["biomarker_code"] for r in multi["rows"]} == {"CBM-002", "CBM-003", "CBM-024", "CBM-030"}
    breast, crc = _cancer_id(client, "breast"), _cancer_id(client, "colorectal")
    shared = client.get("/api/analytics/shared_biomarkers", params={"cancer_a": breast, "cancer_b": crc}).json()
    assert [r["biomarker_code"] for r in shared["rows"]] == ["CBM-003"]
    assert client.get("/api/analytics/shared_biomarkers").status_code == 400
    assert client.get("/api/analytics/multi_cancer_biomarkers", params={"min_cancers": "x"}).status_code == 400
    assert all("sql" in r for r in client.get("/api/analytics/catalogue").json())


def test_dashboard_counts_from_database(client):
    d = client.get("/api/dashboard/stats").json()
    assert d["totals"]["biomarkers"] == 47 and d["totals"]["associations"] == 58
    assert sum(r["count"] for r in d["by_role"]) == 58
    filtered = client.get("/api/dashboard/stats", params={"role": "risk"}).json()
    assert filtered["totals"]["associations"] == sum(r["count"] for r in filtered["by_role"])
    assert {r["role"] for r in filtered["by_role"]} == {"risk"}


def test_network_built_from_relationships(client):
    bid = client.get("/api/biomarkers", params={"q": "CBM-019"}).json()["items"][0]["biomarker_id"]
    net = client.get("/api/network", params={"biomarker_id": bid}).json()
    labels = {n["label"] for n in net["nodes"]}
    assert {"ALK", "EML4", "Non-small cell lung cancer", "PMID 17625570"} <= labels
    ids = {n["id"] for n in net["nodes"]}
    assert all(e["source"] in ids and e["target"] in ids for e in net["edges"])


def test_csv_export(client):
    r = client.get("/api/export/biomarkers", params={"q": "KRAS"})
    assert r.headers["content-type"].startswith("text/csv")
    rows = list(csv.DictReader(io.StringIO(r.text)))
    assert {row["biomarker_code"] for row in rows} == {"CBM-021", "CBM-022", "CBM-037"}
    gaps = list(csv.DictReader(io.StringIO(client.get("/api/export/gaps").text)))
    assert gaps and "flags" in gaps[0]
    rep = client.get("/api/export/analytics", params={"report": "cancers_by_biomarker_count"})
    assert rep.text.splitlines()[0] == "cancer_id,cancer,n_biomarkers,n_associations"


def test_import_endpoint_dry_run_and_validation(client):
    good = "code,name\nliver,Liver cancer\n"
    r = client.post("/api/import/cancers", files={"file": ("c.csv", good, "text/csv")})
    assert r.status_code == 200 and r.json()["ok"] and r.json()["dry_run"]
    bad = "code,name\nLiver Cancer!,x\n"
    body = client.post("/api/import/cancers", files={"file": ("c.csv", bad, "text/csv")}).json()
    assert not body["ok"] and body["errors"][0]["row"] == 2
    assert client.post("/api/import/cancers", files={"file": ("c.txt", good)}).status_code == 400
    assert client.post("/api/import/unknown", files={"file": ("c.csv", good)}).status_code == 404


def test_structured_errors(client):
    r = client.get("/api/biomarkers/99999")
    assert r.status_code == 404 and r.json()["error"]["code"] == "not_found"
    r = client.get("/api/biomarkers", params={"role": "cure"})
    assert r.status_code == 422 and r.json()["error"]["code"] == "validation_error"
    r = client.get("/api/biomarkers", params={"page_size": 1000})
    assert r.status_code == 422
