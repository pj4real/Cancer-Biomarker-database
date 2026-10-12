-- CancerBioMap SQL query catalogue
-- Generated from app/services/analytics.py (the same statements the API executes).
-- Parameters use :name bind syntax (SQLAlchemy text()); the API binds them, never interpolates.
-- Portable SQL: runs unchanged on PostgreSQL and SQLite.

-- Q1. Biomarkers associated with multiple cancer types
--     Biomarkers recorded for at least N distinct cancers.
--     Parameters: :min_cancers (Minimum number of distinct cancers; default 2)
--     Concepts: JOIN, GROUP BY, HAVING, COUNT DISTINCT
SELECT b.biomarker_id, b.biomarker_code, b.name AS biomarker,
       COUNT(DISTINCT bc.cancer_id) AS n_cancers,
       COUNT(bc.association_id)     AS n_associations
FROM biomarker b
JOIN biomarker_cancer bc ON bc.biomarker_id = b.biomarker_id
GROUP BY b.biomarker_id, b.biomarker_code, b.name
HAVING COUNT(DISTINCT bc.cancer_id) >= :min_cancers
ORDER BY n_cancers DESC, b.name;

-- Q2. Cancer types with the most recorded biomarkers
--     Number of distinct biomarkers and associations per cancer (LEFT JOIN keeps cancers with none).
--     Concepts: LEFT JOIN, GROUP BY, COUNT DISTINCT
SELECT c.cancer_id, c.name AS cancer,
       COUNT(DISTINCT bc.biomarker_id) AS n_biomarkers,
       COUNT(bc.association_id)        AS n_associations
FROM cancer c
LEFT JOIN biomarker_cancer bc ON bc.cancer_id = c.cancer_id
GROUP BY c.cancer_id, c.name
ORDER BY n_biomarkers DESC, c.name;

-- Q3. Biomarkers with the most supporting publications
--     Distinct publications linked through evidence records, across all associations of a biomarker.
--     Parameters: :limit (Number of rows; default 10)
--     Concepts: multi-table JOIN, COUNT DISTINCT, LIMIT
SELECT b.biomarker_id, b.name AS biomarker,
       COUNT(DISTINCT e.publication_id) AS n_publications,
       COUNT(e.evidence_id)             AS n_evidence_records
FROM biomarker b
JOIN biomarker_cancer bc ON bc.biomarker_id = b.biomarker_id
JOIN evidence e          ON e.association_id = bc.association_id
GROUP BY b.biomarker_id, b.name
ORDER BY n_publications DESC, b.name
LIMIT :limit;

-- Q4. Biomarker-cancer associations grouped by evidence type
--     Untyped evidence is reported as 'unspecified' rather than hidden.
--     Concepts: COALESCE, GROUP BY expression
SELECT COALESCE(e.evidence_type, 'unspecified') AS evidence_type,
       COUNT(DISTINCT e.association_id)          AS n_associations,
       COUNT(e.evidence_id)                      AS n_evidence_records
FROM evidence e
GROUP BY COALESCE(e.evidence_type, 'unspecified')
ORDER BY n_associations DESC;

-- Q5. Biomarkers linked to common biological pathways
--     Pathways (KEGG gene membership) shared by at least N biomarkers.
--     Parameters: :min_biomarkers (Minimum biomarkers per pathway; default 2)
--     Concepts: JOIN, HAVING
SELECT p.pathway_id, p.pathway_name, p.pathway_database, p.external_identifier,
       COUNT(DISTINCT bp.biomarker_id) AS n_biomarkers
FROM pathway p
JOIN biomarker_pathway bp ON bp.pathway_id = p.pathway_id
GROUP BY p.pathway_id, p.pathway_name, p.pathway_database, p.external_identifier
HAVING COUNT(DISTINCT bp.biomarker_id) >= :min_biomarkers
ORDER BY n_biomarkers DESC, p.pathway_name;

-- Q6. Biomarker pairs that share pathways
--     Self-join on the junction table; b1 < b2 avoids duplicate and self pairs.
--     Parameters: :min_shared (Minimum shared pathways; default 3), :limit (Number of rows; default 25)
--     Concepts: self-join, HAVING, LIMIT
SELECT b1.name AS biomarker_a, b2.name AS biomarker_b,
       COUNT(*) AS shared_pathways
FROM biomarker_pathway bp1
JOIN biomarker_pathway bp2
  ON bp1.pathway_id = bp2.pathway_id AND bp1.biomarker_id < bp2.biomarker_id
JOIN biomarker b1 ON b1.biomarker_id = bp1.biomarker_id
JOIN biomarker b2 ON b2.biomarker_id = bp2.biomarker_id
GROUP BY b1.name, b2.name
HAVING COUNT(*) >= :min_shared
ORDER BY shared_pathways DESC, b1.name, b2.name
LIMIT :limit;

-- Q7. Associations with limited or missing supporting evidence
--     Associations with fewer than N distinct publications (LEFT JOIN keeps those with no evidence).
--     Parameters: :max_publications (Flag associations with fewer publications than this; default 2)
--     Concepts: LEFT JOIN, HAVING, COUNT DISTINCT
SELECT bc.association_id, b.name AS biomarker, c.name AS cancer, bc.biomarker_role,
       COUNT(DISTINCT e.publication_id) AS n_publications,
       COUNT(DISTINCT e.source_name)    AS n_sources,
       COUNT(e.evidence_id)             AS n_evidence_records
FROM biomarker_cancer bc
JOIN biomarker b      ON b.biomarker_id = bc.biomarker_id
JOIN cancer c         ON c.cancer_id = bc.cancer_id
LEFT JOIN evidence e  ON e.association_id = bc.association_id
GROUP BY bc.association_id, b.name, c.name, bc.biomarker_role
HAVING COUNT(DISTINCT e.publication_id) < :max_publications
ORDER BY n_publications, n_sources, b.name;

-- Q8. Shared biomarkers between two cancers
--     Set intersection of the biomarkers recorded for two cancers.
--     Parameters: :cancer_a (First cancer; default None), :cancer_b (Second cancer; default None)
--     Concepts: INTERSECT, subquery
SELECT b.biomarker_id, b.biomarker_code, b.name AS biomarker, b.biomarker_type
FROM biomarker b
WHERE b.biomarker_id IN (
    SELECT biomarker_id FROM biomarker_cancer WHERE cancer_id = :cancer_a
    INTERSECT
    SELECT biomarker_id FROM biomarker_cancer WHERE cancer_id = :cancer_b
)
ORDER BY b.name;

-- Q9. Average evidence-support score by cancer and role
--     Aggregates stored scores; incomplete (NULL) scores are counted separately, not averaged as zero.
--     Concepts: CASE, AVG ignores NULL, GROUP BY
SELECT c.name AS cancer, bc.biomarker_role,
       COUNT(*)                                    AS n_associations,
       AVG(s.overall_score)                        AS mean_score,
       SUM(CASE WHEN s.overall_score IS NULL THEN 1 ELSE 0 END) AS n_unscored,
       SUM(CASE WHEN s.score_status = 'provisional' THEN 1 ELSE 0 END) AS n_provisional
FROM evidence_score s
JOIN biomarker_cancer bc ON bc.association_id = s.association_id
JOIN cancer c            ON c.cancer_id = bc.cancer_id
WHERE s.scoring_version = :scoring_version
GROUP BY c.name, bc.biomarker_role
ORDER BY c.name, bc.biomarker_role;
