# CMS Hospital Quality Snowflake Schema

## Fact Table

### fact_hospital_measures
Stores hospital-level quality measure results by facility, measure, and reporting period.

Columns:
- fact_id
- facility_id
- measure_id
- date_key
- score
- sample_size
- denominator
- start_date
- end_date
- compared_to_national

## Dimension Tables

### dim_hospital
Stores hospital descriptive information including location, type, ownership, emergency services, and overall rating.

### dim_measure
Stores CMS quality measure metadata and assigns each measure to a category.

### dim_geography
Stores state-to-region mapping using U.S. Census regions.

### dim_time
Stores date attributes such as year, quarter, month, and month name.

## Design Explanation

This project uses a snowflake schema because geography is normalized into a separate dimension. The fact table stores measurable hospital quality outcomes, while the dimension tables provide descriptive context for analysis.

This design supports Power BI dashboards and SQL analysis such as:
- Hospital rating comparison by state
- Average ER wait time by region
- Readmission and patient satisfaction analysis
- Hospital ranking by ownership type
- Year-over-year quality trend analysis