USE cms_hospital_quality;
GO

-- ============================================================
-- Top and bottom hospitals by overall rating within each state
-- Uses ROW_NUMBER window function
-- ============================================================

WITH ranked_hospitals AS (
    SELECT
        h.facility_id,
        h.name AS hospital_name,
        h.city,
        h.state,
        h.type AS hospital_type,
        h.ownership,
        h.overall_rating,

        ROW_NUMBER() OVER (
            PARTITION BY h.state
            ORDER BY h.overall_rating DESC, h.name
        ) AS top_rank,

        ROW_NUMBER() OVER (
            PARTITION BY h.state
            ORDER BY h.overall_rating ASC, h.name
        ) AS bottom_rank
    FROM dim_hospital h
    WHERE h.overall_rating IS NOT NULL
)
SELECT
    state,
    hospital_name,
    city,
    hospital_type,
    ownership,
    overall_rating,
    CASE
        WHEN top_rank <= 5 THEN 'Top 5'
        WHEN bottom_rank <= 5 THEN 'Bottom 5'
    END AS ranking_group
FROM ranked_hospitals
WHERE top_rank <= 5
   OR bottom_rank <= 5
ORDER BY state, ranking_group DESC, overall_rating DESC;