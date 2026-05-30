USE cms_hospital_quality;
GO

-- ============================================================
-- Hospitals with above-average readmission scores
-- and below-average patient experience scores
--
-- Uses CTEs and cross joins for benchmark comparison
-- ============================================================

WITH readmission_scores AS (
    SELECT
        h.facility_id,
        h.name AS hospital_name,
        h.city,
        h.state,
        AVG(CAST(f.score AS FLOAT)) AS avg_readmission_score
    FROM fact_hospital_measures f
    JOIN dim_hospital h
        ON f.facility_id = h.facility_id
    JOIN dim_measure m
        ON f.measure_id = m.measure_id
    WHERE m.category = 'Readmissions and Deaths'
      AND f.score IS NOT NULL
    GROUP BY
        h.facility_id,
        h.name,
        h.city,
        h.state
),
patient_experience_scores AS (
    SELECT
        h.facility_id,
        AVG(CAST(f.score AS FLOAT)) AS avg_patient_experience_score
    FROM fact_hospital_measures f
    JOIN dim_hospital h
        ON f.facility_id = h.facility_id
    JOIN dim_measure m
        ON f.measure_id = m.measure_id
    WHERE m.category = 'Patient Experience'
      AND f.score IS NOT NULL
    GROUP BY h.facility_id
),
benchmarks AS (
    SELECT
        (
            SELECT AVG(avg_readmission_score)
            FROM readmission_scores
        ) AS national_avg_readmission,

        (
            SELECT AVG(avg_patient_experience_score)
            FROM patient_experience_scores
        ) AS national_avg_patient_experience
)
SELECT TOP 100
    r.facility_id,
    r.hospital_name,
    r.city,
    r.state,
    ROUND(r.avg_readmission_score, 2) AS avg_readmission_score,
    ROUND(p.avg_patient_experience_score, 2) AS avg_patient_experience_score,
    ROUND(b.national_avg_readmission, 2) AS national_avg_readmission,
    ROUND(b.national_avg_patient_experience, 2) AS national_avg_patient_experience
FROM readmission_scores r
JOIN patient_experience_scores p
    ON r.facility_id = p.facility_id
CROSS JOIN benchmarks b
WHERE r.avg_readmission_score > b.national_avg_readmission
  AND p.avg_patient_experience_score < b.national_avg_patient_experience
ORDER BY
    r.avg_readmission_score DESC,
    p.avg_patient_experience_score ASC;