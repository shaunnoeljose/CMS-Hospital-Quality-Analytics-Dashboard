USE cms_hospital_quality;
GO

-- Drop tables if they already exist
IF OBJECT_ID('fact_hospital_measures', 'U') IS NOT NULL
    DROP TABLE fact_hospital_measures;

IF OBJECT_ID('dim_hospital', 'U') IS NOT NULL
    DROP TABLE dim_hospital;

IF OBJECT_ID('dim_measure', 'U') IS NOT NULL
    DROP TABLE dim_measure;

IF OBJECT_ID('dim_time', 'U') IS NOT NULL
    DROP TABLE dim_time;

IF OBJECT_ID('dim_geography', 'U') IS NOT NULL
    DROP TABLE dim_geography;
GO

CREATE TABLE dim_geography (
    state VARCHAR(2) PRIMARY KEY,
    region VARCHAR(20) NOT NULL,

    CONSTRAINT chk_region
        CHECK (region IN ('Northeast', 'South', 'Midwest', 'West'))
);
GO

CREATE TABLE dim_hospital (
    facility_id VARCHAR(20) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    address VARCHAR(255),
    city VARCHAR(100),
    state VARCHAR(2) NOT NULL,
    zip VARCHAR(10),
    county VARCHAR(100),
    phone VARCHAR(20),
    type VARCHAR(100),
    ownership VARCHAR(150),
    emergency_services BIT,
    overall_rating INT,

    CONSTRAINT fk_hospital_geography
        FOREIGN KEY (state)
        REFERENCES dim_geography(state),

    CONSTRAINT chk_overall_rating
        CHECK (
            overall_rating IS NULL
            OR overall_rating BETWEEN 1 AND 5
        )
);
GO

CREATE TABLE dim_measure (
    measure_id VARCHAR(50) PRIMARY KEY,
    measure_name VARCHAR(500) NOT NULL,
    measure_description VARCHAR(MAX),
    category VARCHAR(100) NOT NULL,

    CONSTRAINT chk_measure_category
        CHECK (
            category IN (
                'Timely Care',
                'Complications and Deaths',
                'Patient Experience',
                'Readmissions and Deaths'
            )
        )
);
GO

CREATE TABLE dim_time (
    date_key INT PRIMARY KEY,
    full_date DATE NOT NULL UNIQUE,
    year INT NOT NULL,
    quarter INT NOT NULL,
    month INT NOT NULL,
    month_name VARCHAR(20) NOT NULL,

    CONSTRAINT chk_quarter
        CHECK (quarter BETWEEN 1 AND 4),

    CONSTRAINT chk_month
        CHECK (month BETWEEN 1 AND 12)
);
GO

CREATE TABLE fact_hospital_measures (
    fact_id BIGINT IDENTITY(1,1) PRIMARY KEY,

    facility_id VARCHAR(20) NOT NULL,
    measure_id VARCHAR(50) NOT NULL,
    date_key INT NOT NULL,

    score DECIMAL(12,4),
    sample_size INT,
    denominator INT,

    start_date DATE,
    end_date DATE,
    compared_to_national VARCHAR(255),

    CONSTRAINT fk_fact_hospital
        FOREIGN KEY (facility_id)
        REFERENCES dim_hospital(facility_id),

    CONSTRAINT fk_fact_measure
        FOREIGN KEY (measure_id)
        REFERENCES dim_measure(measure_id),

    CONSTRAINT fk_fact_time
        FOREIGN KEY (date_key)
        REFERENCES dim_time(date_key),

    CONSTRAINT chk_sample_size
        CHECK (sample_size IS NULL OR sample_size >= 0),

    CONSTRAINT chk_denominator
        CHECK (denominator IS NULL OR denominator >= 0),

    CONSTRAINT chk_date_range
        CHECK (
            start_date IS NULL
            OR end_date IS NULL
            OR start_date <= end_date
        ),

    CONSTRAINT uq_fact_hospital_measure_period
        UNIQUE (facility_id, measure_id, start_date, end_date)
);
GO