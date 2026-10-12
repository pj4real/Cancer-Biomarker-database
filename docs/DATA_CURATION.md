# Adding and Curating Data

All curated data lives in `backend/data/sample/*.csv`. Import order (dependencies first):

```
cancers → genes → proteins → pathways → publications → biomarkers → gene_pathways
→ biomarker_pathways → associations → evidence → evidence_kegg → variants
```

## Workflow for a new biomarker–cancer association

1. **Genes / proteins.** Add rows to `genes.csv` (official HGNC symbol and NCBI Gene ID) and
   `proteins.csv` (reviewed UniProt accession plus `gene_symbol`).
2. **Publications.** Add the PMID with an approximate title to `publications.csv`, then run:
   ```bash
   cd backend
   python -m scripts.fetch_pubmed           # reports mismatches; never trust a PMID from memory
   python -m scripts.fetch_pubmed --write   # overwrite metadata with the PubMed record
   ```
3. **Biomarker.** Add to `biomarkers.csv` with a new code (`CBM-048`, …). `gene_symbols` is a
   `;`-separated list. `biomarker_type` must be one of the vocabulary values in `app/vocab.py`.
4. **Association.** Add `biomarker_code, cancer_code, biomarker_role, source_status, description` to
   `associations.csv`. Use `pending_curation` if evidence is not yet curated, and `synthetic_demo` for
   any illustrative record. Never present synthetic rows as scientific evidence.
5. **Evidence.** One row per (association, publication, source) in `evidence.csv`:
   - `evidence_type`: the study design you verified in the paper; leave blank if unsure.
   - `consistency_annotation`: `supports`, `mixed` or `conflicting` only when the paper's finding
     clearly bears on the role; otherwise leave blank (unknown). Never invent contradictory findings.
   - `evidence_summary`: paraphrase the paper's main reported result.
   - `retrieved_at`: the date you verified the record.
6. **Pathways and verification.**
   ```bash
   python -m scripts.verify_sources --write-kegg   # gene/protein/variant checks + KEGG links
   python -m scripts.init_db                        # import (idempotent) + recompute scores
   ```

Or upload a single CSV in the UI (*Data Import* page): run a dry-run validation first, then import.

## Validation rules enforced by the importer

| Field | Rule |
|---|---|
| `official_symbol` | Uppercase HGNC-style symbol; unique |
| `ncbi_gene_id` | Positive integer; unique; cannot be reassigned to another symbol |
| `accession` | UniProt accession pattern |
| `pmid` / `doi` | At least one is required; PMID numeric; both unique |
| `publication_year` | 1900 to next year |
| `biomarker_type`, `biomarker_role`, `source_status`, `evidence_type`, `consistency_annotation` | Controlled vocabularies |
| `chromosome` | 1–22, X, Y, MT (a `chr` prefix is stripped) |
| `reference_allele`, `alternate_allele` | A, C, G, T, N or `-` |
| `dbsnp_id` | `rs` followed by digits |
| Referenced codes | Must already exist (biomarker, cancer, gene, publication, association) |
| Duplicate natural key in one file | Rejected with both row numbers |

Any error rejects the whole file (atomic), and the report lists row numbers (header = row 1).

## Access and attribution

- NCBI E-utilities: at most 3 requests/second without an API key (set `NCBI_EMAIL`/`NCBI_API_KEY`
  in `.env`). The scripts batch requests and pause between calls.
- KEGG REST: free for academic use; commercial use requires a licence.
- UniProt, Ensembl and GDC: public REST APIs; cite them as described on their websites.
- Do not scrape web pages. Use the documented APIs only.
