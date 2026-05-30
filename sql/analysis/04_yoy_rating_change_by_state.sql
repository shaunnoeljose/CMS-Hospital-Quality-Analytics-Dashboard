USE cms_hospital_quality;
GO

-- ============================================================
-- Year-over-year change in average measure score by state
-- Uses LAG window function
--
-- Since dim_hospital stores the latest overall rating only,
-- this query calculates YoY change using fact measure scores.
-- ============================================================

WITH state_year_scores AS (
    SELECT
        h.state,
        t.year,
        AVG(CAST(f.score AS FLOAT)) AS avg_quality_score,
        COUNT(*) AS measure_record_count
    FROM fact_hospital_measures f
    JOIN dim_hospital h
        ON f.facility_id = h.facility_id
    JOIN dim_time t
        ON f.date_key = t.date_key
    WHERE f.score IS NOT NULL
    GROUP BY
        h.state,
        t.year
),
with_prior_year AS (
    SELECT
        state,
        year,
        avg_quality_score,
        measure_record_count,

        LAG(avg_quality_score) OVER (
            PARTITION BY state
            ORDER BY year
        ) AS prior_year_avg_quality_score
    FROM state_year_scores
)
SELECT
    state,
    year,
    measure_record_count,
    ROUND(avg_quality_score, 2) AS avg_quality_score,
    ROUND(prior_year_avg_quality_score, 2) AS prior_year_avg_quality_score,
    ROUND(avg_quality_score - prior_year_avg_quality_score, 2) AS yoy_change
FROM with_prior_year
ORDER BY state, year;