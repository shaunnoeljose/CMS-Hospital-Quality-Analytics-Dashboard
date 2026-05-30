USE cms_hospital_quality;
GO

-- ============================================================
-- Average emergency care wait time by Census region
-- Uses joins, aggregation, and national comparison
--
-- Note:
-- CMS timely-care measure names vary by file version.
-- This query searches for measures related to emergency department
-- or ED wait time.
-- ============================================================

WITH er_measures AS (
    SELECT
        measure_id,
        measure_name
    FROM dim_measure
    WHERE category = 'Timely Care'
      AND (
            LOWER(measure_name) LIKE '%emergency%'
         OR LOWER(measure_name) LIKE '%ed%'
         OR LOWER(measure_name) LIKE '%wait%'
      )
),
regional_wait_times AS (
    SELECT
        g.region,
        COUNT(*) AS measure_record_count,
        COUNT(DISTINCT h.facility_id) AS hospital_count,
        AVG(CAST(f.score AS FLOAT)) AS avg_er_wait_score
    FROM fact_hospital_measures f
    JOIN dim_hospital h
        ON f.facility_id = h.facility_id
    JOIN dim_geography g
        ON h.state = g.state
    JOIN er_measures m
        ON f.measure_id = m.measure_id
    WHERE f.score IS NOT NULL
    GROUP BY g.region
),
national_average AS (
    SELECT
        AVG(CAST(f.score AS FLOAT)) AS national_avg_er_wait_score
    FROM fact_hospital_measures f
    JOIN er_measures m
        ON f.measure_id = m.measure_id
    WHERE f.score IS NOT NULL
)
SELECT
    r.region,
    r.hospital_count,
    r.measure_record_count,
    ROUND(r.avg_er_wait_score, 2) AS avg_er_wait_score,
    ROUND(n.national_avg_er_wait_score, 2) AS national_avg_er_wait_score,
    ROUND(r.avg_er_wait_score - n.national_avg_er_wait_score, 2) AS difference_from_national
FROM regional_wait_times r
CROSS JOIN national_average n
ORDER BY r.avg_er_wait_score DESC;