USE cms_hospital_quality;
GO

-- ============================================================
-- State-level quality summary
-- Useful for Power BI overview page
-- ============================================================

SELECT
    h.state,
    g.region,
    COUNT(DISTINCT h.facility_id) AS hospital_count,
    ROUND(AVG(CAST(h.overall_rating AS FLOAT)), 2) AS avg_overall_rating,
    COUNT(f.fact_id) AS measure_record_count,
    ROUND(AVG(CAST(f.score AS FLOAT)), 2) AS avg_measure_score,
    MIN(f.score) AS min_measure_score,
    MAX(f.score) AS max_measure_score
FROM dim_hospital h
JOIN dim_geography g
    ON h.state = g.state
LEFT JOIN fact_hospital_measures f
    ON h.facility_id = f.facility_id
GROUP BY
    h.state,
    g.region
ORDER BY
    avg_overall_rating DESC,
    hospital_count DESC;