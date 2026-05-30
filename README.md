# CMS Hospital Quality Dashboard

## Project Overview

This project analyzes hospital quality and performance data from the Centers for Medicare & Medicaid Services (CMS). The goal is to build an end-to-end analytics pipeline that extracts public CMS hospital datasets, transforms and validates the data using Python, loads the cleaned data into a SQL Server snowflake schema, and visualizes hospital quality trends in Power BI.

The dashboard allows users to compare hospitals by state, region, ownership type, hospital type, patient experience, readmission rates, emergency care performance, and overall hospital rating.

## Business Problem

Healthcare quality data is publicly available, but it is often spread across multiple large CSV files with inconsistent formats, missing values, and measure-specific scoring rules. This project solves that problem by creating a centralized analytical data model that supports hospital performance comparison and healthcare quality reporting.

Key questions answered by this project include:

* Which states and regions have the highest-rated hospitals?
* How do hospitals compare across ownership types?
* Which hospitals have high readmission scores and low patient satisfaction?
* How do emergency care and patient experience measures vary across the country?
* Which hospitals are outliers in quality performance?

## Tech Stack

* **Python**: ETL pipeline development
* **pandas**: Data extraction, cleaning, transformation, validation
* **SQLAlchemy**: Database loading
* **pyodbc**: SQL Server connectivity
* **SQL Server**: Data warehouse storage
* **SQL Server Management Studio (SSMS)**: Database management and SQL execution
* **Power BI**: Dashboard development and reporting
* **DAX**: Measures, KPIs, benchmark calculations, percentile rankings
* **GitHub**: Version control and project documentation

## Data Sources

The project uses public CMS Provider Data Catalog datasets:

1. Hospital General Information
2. Timely and Effective Care - Hospital
3. Complications and Deaths - Hospital
4. Patient survey (HCAHPS) - Hospital
5. Unplanned Hospital Visits - Hospital

The raw CSV files are stored locally in `data/raw/` and are excluded from GitHub using `.gitignore` because they are large public data files.

## Project Architecture

```text
CMS CSV Files
     |
     v
Python ETL Pipeline
     |
     |-- Extract raw CMS CSV files
     |-- Standardize column names
     |-- Handle missing CMS values such as "Not Available"
     |-- Convert scores and dates to correct data types
     |-- Validate records
     |-- Write rejected records to data/rejected/
     v
SQL Server Data Warehouse
     |
     |-- dim_hospital
     |-- dim_measure
     |-- dim_geography
     |-- dim_time
     |-- fact_hospital_measures
     v
Power BI Dashboard
     |
     |-- National Overview
     |-- Hospital Comparison
     |-- Trends & Patterns
     |-- Hospital Detail Drillthrough
```

## Repository Structure

```text
cms-hospital-quality-dashboard/
├── README.md
├── .gitignore
├── data/
│   ├── raw/                 # Raw CMS CSV files, not pushed to GitHub
│   └── rejected/            # Rejected validation records, not pushed to GitHub
├── sql/
│   ├── schema.sql           # SQL Server CREATE TABLE scripts
│   ├── indexes.sql          # Performance indexes
│   └── analysis/
│       ├── 01_top_bottom_hospitals_by_state.sql
│       ├── 02_avg_er_wait_time_by_region.sql
│       ├── 03_readmission_vs_patient_satisfaction.sql
│       ├── 04_yoy_rating_change_by_state.sql
│       ├── 05_hospital_ranking_by_ownership.sql
│       └── 06_state_quality_summary.sql
├── etl/
│   ├── config.py            # SQL Server connection settings
│   ├── etl_pipeline.py      # Main ETL pipeline
│   └── requirements.txt     # Python dependencies
└── docs/
    ├── schema_design.md
    └── dashboard_screenshots/
        ├── national_overview.png
        ├── hospital_comparison.png
        ├── trends_patterns.png
        └── hospital_detail.png
```

## Data Warehouse Design

This project uses a **snowflake schema** with one central fact table and four dimension tables.

### Fact Table

#### `fact_hospital_measures`

Stores hospital-level quality measure results by facility, measure, and reporting period.

Key columns:

* `facility_id`
* `measure_id`
* `date_key`
* `score`
* `sample_size`
* `denominator`
* `start_date`
* `end_date`
* `compared_to_national`

### Dimension Tables

#### `dim_hospital`

Stores hospital descriptive attributes such as name, address, city, state, ownership type, emergency services availability, and overall rating.

#### `dim_measure`

Stores CMS measure metadata, including measure name, description, and category.

Measure categories include:

* Timely Care
* Complications and Deaths
* Patient Experience
* Readmissions and Deaths

#### `dim_geography`

Stores state-to-region mapping using U.S. Census regions:

* Northeast
* South
* Midwest
* West

#### `dim_time`

Stores reporting-period date attributes such as year, quarter, month, and month name.

## Why Snowflake Schema?

A star schema would store geography fields such as state and region directly inside the hospital dimension. This project uses a snowflake schema by separating geography into `dim_geography`.

This design reduces redundancy and supports cleaner regional analysis. A hospital belongs to a state, and each state belongs to a region. By normalizing geography, the model becomes easier to maintain and extend.

## ETL Pipeline

The ETL pipeline is built in Python and performs the following steps:

### Extract

* Reads five CMS CSV files from `data/raw/`
* Loads all files using pandas
* Preserves raw data separately from transformed data

### Transform

* Standardizes column names to lowercase snake_case
* Handles CMS missing values such as `Not Available`, `Not Applicable`, and blank strings
* Converts scores to numeric values
* Parses start and end dates
* Creates date keys for the time dimension
* Maps state abbreviations to U.S. Census regions
* Deduplicates hospital, measure, and fact records
* Validates foreign keys and required fields
* Logs rejected records to `data/rejected/`

### Load

* Connects to SQL Server using SQLAlchemy and pyodbc
* Loads dimension tables first
* Loads the fact table after dimension tables
* Preserves referential integrity using primary and foreign keys

## ETL Results

In the current run, the ETL pipeline successfully loaded:

| Table                    | Row Count |
| ------------------------ | --------: |
| `dim_geography`          |        51 |
| `dim_hospital`           |     5,366 |
| `dim_measure`            |       132 |
| `dim_time`               |         8 |
| `fact_hospital_measures` |   332,591 |

Rejected records were written to `data/rejected/` for auditability and data quality review.

## SQL Analysis Queries

The project includes SQL analysis queries that demonstrate practical analytics and interview-ready SQL skills.

### 1. Top and Bottom Hospitals by State

Uses `ROW_NUMBER()` and `PARTITION BY` to rank hospitals within each state by overall rating.

### 2. Average ER Wait Time by Region

Uses CTEs, joins, and aggregations to compare emergency-care-related scores across Census regions.

### 3. Readmission vs Patient Satisfaction

Identifies hospitals with above-average readmission scores and below-average patient experience scores.

### 4. Year-over-Year Quality Change by State

Uses the `LAG()` window function to compare state-level average quality scores across reporting years.

### 5. Hospital Ranking by Ownership Type

Uses `RANK()` and `PARTITION BY` to rank hospitals within each ownership category based on a simplified composite score.

### 6. State Quality Summary

Creates a state-level summary useful for Power BI maps, KPI validation, and regional analysis.

## Power BI Dashboard

The Power BI dashboard contains four pages.

### Page 1: National Overview

Includes:

* Total hospitals
* Average overall rating
* Average ER wait score
* Total measure records
* Map showing hospital quality by state
* Regional rating comparison
* Slicers for state, hospital type, ownership, and measure category

### Page 2: Hospital Comparison

Includes:

* Hospital comparison matrix
* Conditional formatting for measure scores
* Hospital performance ranking table
* Slicers for state, category, ownership, hospital type, and rating

### Page 3: Trends & Patterns

Includes:

* Hospital rating distribution
* Patient experience vs readmission scatter plot
* Quality score trend over time
* Composite score by ownership type

### Page 4: Hospital Detail Drillthrough

Includes:

* Hospital-level summary cards
* Detailed measure table
* Performance by measure category
* Drillthrough navigation from other report pages

## DAX Measures

The dashboard uses DAX measures such as:

* `Total Hospitals`
* `Total Measure Records`
* `Average Overall Rating`
* `Average Measure Score`
* `National Average Measure Score`
* `Difference from National Average`
* `Benchmark Flag`
* `Hospital Percentile Rank`
* `Average ER Wait Score`
* `Average Patient Experience Score`
* `Average Readmission Score`
* `Hospital Composite Score`

## Measure Interpretation Note

CMS measures do not all follow the same directionality.

For some measures, higher values are better, such as patient experience scores. For other measures, lower values are better, such as readmission rates, mortality rates, and ER wait times.

The current dashboard includes a simplified composite score for exploratory analysis. In a production version, measure directionality would be normalized before creating a final quality index.

## How to Run the Project

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/cms-hospital-quality-dashboard.git
cd cms-hospital-quality-dashboard
```

### 2. Create the required folders

```bash
mkdir -p data/raw data/rejected
```

On Windows PowerShell:

```powershell
mkdir data\raw
mkdir data\rejected
```

### 3. Download CMS datasets

Download the five CMS CSV files and place them in `data/raw/` with these names:

```text
hospital_general_information.csv
timely_and_effective_care.csv
complications_and_deaths.csv
patient_experience_hcahps.csv
unplanned_hospital_visits.csv
```

### 4. Create the SQL Server database

In SSMS, run:

```sql
CREATE DATABASE cms_hospital_quality;
GO
```

Then run:

```text
sql/schema.sql
sql/indexes.sql
```

### 5. Install Python dependencies

```bash
pip install -r etl/requirements.txt
```

### 6. Update database connection settings

Open `etl/config.py` and confirm the SQL Server value.

Common options:

```python
SERVER = "localhost"
SERVER = "localhost\\SQLEXPRESS"
SERVER = ".\\SQLEXPRESS"
```

### 7. Run the ETL pipeline

```bash
python etl/etl_pipeline.py
```

### 8. Connect Power BI

In Power BI Desktop:

```text
Home → Get Data → SQL Server
```

Use:

```text
Server: localhost
Database: cms_hospital_quality
```

Then load the five warehouse tables and build the report visuals.

## Dashboard Screenshots

Add screenshots in the `docs/dashboard_screenshots/` folder.

Example:

```markdown
![National Overview](docs/dashboard_screenshots/national_overview.png)
![Hospital Comparison](docs/dashboard_screenshots/hospital_comparison.png)
![Trends and Patterns](docs/dashboard_screenshots/trends_patterns.png)
![Hospital Detail](docs/dashboard_screenshots/hospital_detail.png)
```

## Key Skills Demonstrated

* End-to-end data pipeline development
* Data cleaning and validation with Python
* SQL Server data warehouse design
* Snowflake schema modeling
* Fact and dimension table design
* Primary keys, foreign keys, constraints, and indexes
* SQL window functions and CTEs
* Power BI dashboard development
* DAX KPI and benchmark measures
* Healthcare quality analytics
* Data quality logging and rejected-record handling

## Future Improvements

Future enhancements could include:

* Normalizing CMS measure directionality before composite scoring
* Adding automated data refresh from CMS APIs
* Building a metadata-driven ETL framework
* Adding unit tests for transformation logic
* Creating a Streamlit or Flask front end for hospital search
* Deploying SQL Server to Azure SQL Database
* Migrating raw data storage to Azure Data Lake
* Scaling transformations with Databricks and Spark
* Automating Power BI refresh through a cloud gateway

For a production-grade architecture, I would migrate the raw and transformed data layers to **Azure Data Lake** and use **Databricks** for scalable data processing before serving curated tables to Power BI.

## Project Status

Completed:

* Data collection
* Snowflake schema design
* SQL Server database setup
* Python ETL pipeline
* SQL analysis queries
* Power BI dashboard design

Next steps:

* Finalize dashboard screenshots
* Polish README visuals
* Add architecture diagram
* Add sample query outputs

## Author

**Shaun Jose**

Business and Data Analytics | SQL | Python | Power BI | Data Engineering
