import logging
import re
from pathlib import Path

import pandas as pd
from sqlalchemy import text

from config import get_engine


# ============================================================
# Paths
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[1]
RAW_DIR = BASE_DIR / "data" / "raw"
REJECTED_DIR = BASE_DIR / "data" / "rejected"

REJECTED_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# Logging
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)


# ============================================================
# Source files
# ============================================================

FILES = {
    "hospital_general": RAW_DIR / "hospital_general_information.csv",
    "timely_care": RAW_DIR / "timely_and_effective_care.csv",
    "complications": RAW_DIR / "complications_and_deaths.csv",
    "patient_experience": RAW_DIR / "patient_experience_hcahps.csv",
    "readmissions": RAW_DIR / "unplanned_hospital_visits.csv",
}


MEASURE_FILE_CATEGORIES = {
    "timely_care": "Timely Care",
    "complications": "Complications and Deaths",
    "patient_experience": "Patient Experience",
    "readmissions": "Readmissions and Deaths",
}


STATE_TO_REGION = {
    # Northeast
    "CT": "Northeast", "ME": "Northeast", "MA": "Northeast",
    "NH": "Northeast", "RI": "Northeast", "VT": "Northeast",
    "NJ": "Northeast", "NY": "Northeast", "PA": "Northeast",

    # Midwest
    "IL": "Midwest", "IN": "Midwest", "MI": "Midwest",
    "OH": "Midwest", "WI": "Midwest", "IA": "Midwest",
    "KS": "Midwest", "MN": "Midwest", "MO": "Midwest",
    "NE": "Midwest", "ND": "Midwest", "SD": "Midwest",

    # South
    "DE": "South", "FL": "South", "GA": "South",
    "MD": "South", "NC": "South", "SC": "South",
    "VA": "South", "DC": "South", "WV": "South",
    "AL": "South", "KY": "South", "MS": "South",
    "TN": "South", "AR": "South", "LA": "South",
    "OK": "South", "TX": "South",

    # West
    "AZ": "West", "CO": "West", "ID": "West",
    "MT": "West", "NV": "West", "NM": "West",
    "UT": "West", "WY": "West", "AK": "West",
    "CA": "West", "HI": "West", "OR": "West",
    "WA": "West"
}


# ============================================================
# Helper functions
# ============================================================

def standardize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Converts CMS column names to lowercase snake_case.
    Example: 'Facility ID' -> 'facility_id'
    """
    df = df.copy()
    df.columns = [
        re.sub(r"_+", "_", re.sub(r"[^a-zA-Z0-9]+", "_", col.strip().lower())).strip("_")
        for col in df.columns
    ]
    return df


def clean_missing_values(df: pd.DataFrame) -> pd.DataFrame:
    """
    Converts CMS missing-value strings to pandas NA.
    """
    missing_values = [
        "Not Available",
        "Not Applicable",
        "Not Available ",
        "Not Applicable ",
        "N/A",
        "NA",
        "",
        " "
    ]

    return df.replace(missing_values, pd.NA)


def find_column(df: pd.DataFrame, candidates: list[str]) -> str | None:
    """
    Returns the first available column from a list of possible CMS column names.
    """
    for col in candidates:
        if col in df.columns:
            return col
    return None


def to_numeric_score(series: pd.Series) -> pd.Series:
    """
    Converts CMS score values to numeric.
    Handles values like:
    '91'
    '91%'
    '168 minutes'
    'Not Available'
    """
    cleaned = (
        series.astype("string")
        .str.replace("%", "", regex=False)
        .str.extract(r"([-+]?\d*\.?\d+)", expand=False)
    )

    return pd.to_numeric(cleaned, errors="coerce")


def to_int(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce").astype("Int64")


def create_date_key(date_series: pd.Series) -> pd.Series:
    return date_series.dt.strftime("%Y%m%d").astype("Int64")


def save_rejected(df: pd.DataFrame, filename: str, reason: str):
    if df.empty:
        return

    rejected = df.copy()
    rejected["rejection_reason"] = reason

    path = REJECTED_DIR / filename
    rejected.to_csv(path, index=False)

    logging.warning(f"Rejected {len(rejected)} records → {path}")


# ============================================================
# Extract
# ============================================================

def extract_files() -> dict[str, pd.DataFrame]:
    extracted = {}

    for name, path in FILES.items():
        if not path.exists():
            raise FileNotFoundError(f"Missing file: {path}")

        df = pd.read_csv(path, dtype=str)
        df = standardize_columns(df)
        df = clean_missing_values(df)

        extracted[name] = df
        logging.info(f"Extracted {name}: {len(df):,} rows, {len(df.columns):,} columns")

    return extracted


# ============================================================
# Dimension transforms
# ============================================================

def build_dim_geography() -> pd.DataFrame:
    df = pd.DataFrame(
        [{"state": state, "region": region} for state, region in STATE_TO_REGION.items()]
    )

    logging.info(f"Built dim_geography: {len(df):,} rows")
    return df


def build_dim_hospital(hospital_df: pd.DataFrame) -> pd.DataFrame:
    column_map = {
        "facility_id": find_column(hospital_df, ["facility_id", "provider_id"]),
        "name": find_column(hospital_df, ["facility_name", "hospital_name"]),
        "address": find_column(hospital_df, ["address"]),
        "city": find_column(hospital_df, ["city_town", "city"]),
        "state": find_column(hospital_df, ["state"]),
        "zip": find_column(hospital_df, ["zip_code", "zip"]),
        "county": find_column(hospital_df, ["county_parish", "county"]),
        "phone": find_column(hospital_df, ["telephone_number", "phone_number", "phone"]),
        "type": find_column(hospital_df, ["hospital_type", "type"]),
        "ownership": find_column(hospital_df, ["hospital_ownership", "ownership"]),
        "emergency_services": find_column(hospital_df, ["emergency_services"]),
        "overall_rating": find_column(hospital_df, ["hospital_overall_rating", "overall_rating"]),
    }

    missing = [target for target, source in column_map.items() if source is None and target in ["facility_id", "name", "state"]]
    if missing:
        raise ValueError(f"Missing required hospital columns: {missing}")

    dim = pd.DataFrame()

    for target, source in column_map.items():
        if source is not None:
            dim[target] = hospital_df[source]
        else:
            dim[target] = pd.NA

    dim["facility_id"] = dim["facility_id"].astype("string").str.strip()
    dim["name"] = dim["name"].astype("string").str.strip()
    dim["state"] = dim["state"].astype("string").str.strip().str.upper()

    dim["emergency_services"] = (
        dim["emergency_services"]
        .astype("string")
        .str.strip()
        .str.lower()
        .map({"yes": True, "no": False, "true": True, "false": False})
    )

    dim["overall_rating"] = pd.to_numeric(dim["overall_rating"], errors="coerce").astype("Int64")

    rejected = dim[
        dim["facility_id"].isna()
        | dim["name"].isna()
        | dim["state"].isna()
        | ~dim["state"].isin(STATE_TO_REGION.keys())
    ]

    save_rejected(
        rejected,
        "rejected_dim_hospital.csv",
        "Missing facility_id/name/state or invalid state"
    )

    dim = dim.drop(rejected.index)
    dim = dim.drop_duplicates(subset=["facility_id"])

    logging.info(f"Built dim_hospital: {len(dim):,} rows")
    return dim


def build_measure_and_fact_inputs(extracted: dict[str, pd.DataFrame]):
    measure_frames = []
    fact_frames = []

    for file_key, category in MEASURE_FILE_CATEGORIES.items():
        df = extracted[file_key].copy()

        facility_col = find_column(df, ["facility_id", "provider_id"])
        measure_id_col = find_column(df, ["measure_id", "hcahps_measure_id"])
        measure_name_col = find_column(df, ["measure_name", "hcahps_question", "measure"])
        score_col = find_column(df, [
            "score",
            "hcahps_answer_percent",
            "patient_survey_star_rating",
            "linear_mean_value"
        ])
        sample_col = find_column(df, [
            "sample_size",
            "number_of_completed_surveys",
            "number_of_patients",
            "footnote"
        ])
        denominator_col = find_column(df, ["denominator"])
        start_col = find_column(df, ["start_date", "measure_start_date"])
        end_col = find_column(df, ["end_date", "measure_end_date"])
        compared_col = find_column(df, ["compared_to_national", "comparison_to_national"])

        required = {
            "facility_id": facility_col,
            "measure_id": measure_id_col,
            "measure_name": measure_name_col,
            "score": score_col,
            "start_date": start_col,
            "end_date": end_col,
        }

        missing = [key for key, value in required.items() if value is None]
        if missing:
            logging.warning(f"{file_key} is missing columns needed for facts: {missing}")
            continue

        measure_df = pd.DataFrame({
            "measure_id": df[measure_id_col],
            "measure_name": df[measure_name_col],
            "measure_description": df[measure_name_col],
            "category": category
        })

        measure_frames.append(measure_df)

        fact_df = pd.DataFrame({
            "facility_id": df[facility_col],
            "measure_id": df[measure_id_col],
            "score": to_numeric_score(df[score_col]),
            "sample_size": to_int(df[sample_col]) if sample_col else pd.NA,
            "denominator": to_int(df[denominator_col]) if denominator_col else pd.NA,
            "start_date": pd.to_datetime(df[start_col], errors="coerce"),
            "end_date": pd.to_datetime(df[end_col], errors="coerce"),
            "compared_to_national": df[compared_col] if compared_col else pd.NA,
            "source_file": file_key
        })

        fact_frames.append(fact_df)

        logging.info(f"Prepared measure/fact input from {file_key}: {len(fact_df):,} rows")

    dim_measure = pd.concat(measure_frames, ignore_index=True)
    fact = pd.concat(fact_frames, ignore_index=True)

    dim_measure["measure_id"] = dim_measure["measure_id"].astype("string").str.strip()
    dim_measure["measure_name"] = dim_measure["measure_name"].astype("string").str.strip()
    dim_measure["measure_description"] = dim_measure["measure_description"].astype("string").str.strip()

    dim_measure = dim_measure.dropna(subset=["measure_id", "measure_name"])
    dim_measure = dim_measure.drop_duplicates(subset=["measure_id"])

    fact["facility_id"] = fact["facility_id"].astype("string").str.strip()
    fact["measure_id"] = fact["measure_id"].astype("string").str.strip()
    fact["date_key"] = create_date_key(fact["start_date"])

    logging.info(f"Built dim_measure: {len(dim_measure):,} rows")
    logging.info(f"Built raw fact table candidate: {len(fact):,} rows")

    return dim_measure, fact


def build_dim_time(fact_df: pd.DataFrame) -> pd.DataFrame:
    dates = fact_df["start_date"].dropna().drop_duplicates()

    dim = pd.DataFrame({"full_date": dates})
    dim["date_key"] = create_date_key(dim["full_date"])
    dim["year"] = dim["full_date"].dt.year
    dim["quarter"] = dim["full_date"].dt.quarter
    dim["month"] = dim["full_date"].dt.month
    dim["month_name"] = dim["full_date"].dt.month_name()

    dim = dim[["date_key", "full_date", "year", "quarter", "month", "month_name"]]
    dim = dim.drop_duplicates(subset=["date_key"])

    logging.info(f"Built dim_time: {len(dim):,} rows")
    return dim


def validate_fact_table(
    fact_df: pd.DataFrame,
    dim_hospital: pd.DataFrame,
    dim_measure: pd.DataFrame,
    dim_time: pd.DataFrame
) -> pd.DataFrame:
    valid_facilities = set(dim_hospital["facility_id"].astype(str))
    valid_measures = set(dim_measure["measure_id"].astype(str))
    valid_dates = set(dim_time["date_key"].dropna().astype(int))

    invalid = fact_df[
        fact_df["facility_id"].isna()
        | fact_df["measure_id"].isna()
        | fact_df["date_key"].isna()
        | fact_df["score"].isna()
        | ~fact_df["facility_id"].astype(str).isin(valid_facilities)
        | ~fact_df["measure_id"].astype(str).isin(valid_measures)
        | ~fact_df["date_key"].dropna().astype("Int64").isin(valid_dates)
    ]

    save_rejected(
        invalid,
        "rejected_fact_hospital_measures.csv",
        "Missing key fields, invalid foreign key, invalid date, or non-numeric score"
    )

    valid = fact_df.drop(invalid.index)

    valid = valid[
        [
            "facility_id",
            "measure_id",
            "date_key",
            "score",
            "sample_size",
            "denominator",
            "start_date",
            "end_date",
            "compared_to_national"
        ]
    ]

    valid = valid.drop_duplicates(
        subset=["facility_id", "measure_id", "start_date", "end_date"]
    )

    logging.info(f"Validated fact_hospital_measures: {len(valid):,} rows")
    return valid


# ============================================================
# Load
# ============================================================

def clear_existing_data(engine):
    logging.info("Clearing existing data from SQL Server tables...")

    with engine.begin() as conn:
        conn.execute(text("DELETE FROM fact_hospital_measures;"))
        conn.execute(text("DELETE FROM dim_hospital;"))
        conn.execute(text("DELETE FROM dim_measure;"))
        conn.execute(text("DELETE FROM dim_time;"))
        conn.execute(text("DELETE FROM dim_geography;"))

    logging.info("Existing data cleared")


def load_table(df: pd.DataFrame, table_name: str, engine):
    df.to_sql(
        table_name,
        con=engine,
        if_exists="append",
        index=False,
        chunksize=500
    )

    logging.info(f"Loaded {table_name}: {len(df):,} rows")


# ============================================================
# Main ETL
# ============================================================

def run_etl():
    logging.info("Starting CMS Hospital Quality ETL pipeline")

    engine = get_engine()

    extracted = extract_files()

    dim_geography = build_dim_geography()
    dim_hospital = build_dim_hospital(extracted["hospital_general"])
    dim_measure, fact_candidate = build_measure_and_fact_inputs(extracted)
    dim_time = build_dim_time(fact_candidate)

    fact_hospital_measures = validate_fact_table(
        fact_candidate,
        dim_hospital,
        dim_measure,
        dim_time
    )

    clear_existing_data(engine)

    # Load dimensions first
    load_table(dim_geography, "dim_geography", engine)
    load_table(dim_hospital, "dim_hospital", engine)
    load_table(dim_measure, "dim_measure", engine)
    load_table(dim_time, "dim_time", engine)

    # Load fact table last
    load_table(fact_hospital_measures, "fact_hospital_measures", engine)

    logging.info("CMS Hospital Quality ETL pipeline completed successfully")


if __name__ == "__main__":
    run_etl()