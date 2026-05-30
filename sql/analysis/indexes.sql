USE cms_hospital_quality;
GO

CREATE INDEX idx_fact_facility_id
ON fact_hospital_measures (facility_id);
GO

CREATE INDEX idx_fact_measure_id
ON fact_hospital_measures (measure_id);
GO

CREATE INDEX idx_fact_date_key
ON fact_hospital_measures (date_key);
GO

CREATE INDEX idx_fact_facility_measure
ON fact_hospital_measures (facility_id, measure_id);
GO

CREATE INDEX idx_hospital_state
ON dim_hospital (state);
GO

CREATE INDEX idx_hospital_overall_rating
ON dim_hospital (overall_rating);
GO

CREATE INDEX idx_hospital_type
ON dim_hospital (type);
GO

CREATE INDEX idx_hospital_ownership
ON dim_hospital (ownership);
GO

CREATE INDEX idx_measure_category
ON dim_measure (category);
GO

CREATE INDEX idx_geography_region
ON dim_geography (region);
GO