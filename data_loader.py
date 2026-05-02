import sqlite3
import pandas as pd
from pathlib import Path
from core.config import DB_PATH


class DataLoader:
    def __init__(self, db_path=None):
        # Use given DB path or default from config
        self.db_path = str(db_path or DB_PATH)

    def load_data(self):
        db_file = Path(self.db_path)

        # Check if database exists
        if not db_file.exists():
            raise FileNotFoundError(f"Database file not found: {self.db_path}")

        conn = sqlite3.connect(self.db_path)

        try:
            # Get list of tables in DB
            tables = pd.read_sql_query(
                "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;",
                conn
            )["name"].tolist()

            # Ensure resources table exists
            if "resources" not in tables:
                raise ValueError(f"'resources' table not found in {self.db_path}")

            # Load main resources data
            resources_df = pd.read_sql_query('SELECT * FROM resources', conn)

            # Load county data if available
            if "county_context" in tables:
                county_df = pd.read_sql_query('SELECT * FROM county_context', conn)
            else:
                county_df = pd.DataFrame()

            # Clean and standardize data
            resources_df = self._standardize_resources(resources_df)
            county_df = self._standardize_counties(county_df)
            #  NEW: DATA VALIDATION 
            self._validate_resources(resources_df)
            self._validate_counties(county_df)

            return resources_df, county_df

        finally:
            conn.close()

    def _standardize_resources(self, df):
        df = df.copy()

        # Rename columns to consistent names
        rename_map = {
            "eligibility_text": "eligibility",
            "zip": "zip_code",
            "latitude": "lat",
            "longitude": "lon",
        }

        df = df.rename(columns=rename_map)

        # Ensure required columns exist
        required_cols = [
            "resource_id", "name", "category", "subcategory", "eligibility",
            "income_max", "student_only", "household_size_min", "urgency_support",
            "documents_required", "address", "city", "state", "zip_code",
            "lat", "lon", "phone", "website", "hours", "is_online", "source",
            "county", "fips5"
        ]

        for col in required_cols:
            if col not in df.columns:
                df[col] = None

        # Clean string columns
        for col in [
            "name", "category", "subcategory", "eligibility",
            "address", "city", "state", "zip_code",
            "phone", "website", "hours", "source",
            "county", "fips5"
        ]:
            df[col] = df[col].astype("string").str.strip()

        # Normalize values
        df["state"] = df["state"].str.upper()
        df["category"] = df["category"].fillna("").astype(str).str.lower()

        # Extract valid ZIP codes
        df["zip_code"] = df["zip_code"].fillna("").astype(str)\
            .str.extract(r"(\d{5})", expand=False).fillna("")

        # Convert numeric columns
        for col in ["income_max", "student_only", "household_size_min", "lat", "lon", "is_online"]:
            df[col] = pd.to_numeric(df[col], errors="coerce")

        # Remove invalid rows
        df = df[df["name"].notna() & (df["name"].str.strip() != "")]
        df = df[df["category"].notna() & (df["category"].str.strip() != "")]

        return df.reset_index(drop=True)

    def _standardize_counties(self, df):
        # If no data, return empty structure
        if df is None or df.empty:
            return pd.DataFrame(columns=[
                "fips5", "state", "county", "poverty_rate", "unemployment_rate"
            ])

        df = df.copy()

        # Rename columns
        rename_map = {
            "poverty_rate_23": "poverty_rate",
            "unemployment_rate_2023": "unemployment_rate",
        }

        df = df.rename(columns=rename_map)

        # Ensure required columns exist
        for col in ["fips5", "state", "county"]:
            if col not in df.columns:
                df[col] = None

        for col in ["poverty_rate", "unemployment_rate"]:
            if col not in df.columns:
                df[col] = None

        # Clean values
        df["fips5"] = df["fips5"].astype("string").str.strip()
        df["state"] = df["state"].astype("string").str.strip().str.upper()
        df["county"] = df["county"].astype("string").str.strip()

        # Convert numeric fields
        df["poverty_rate"] = pd.to_numeric(df["poverty_rate"], errors="coerce")
        df["unemployment_rate"] = pd.to_numeric(df["unemployment_rate"], errors="coerce")

        return df.reset_index(drop=True)
        #new
    def _validate_resources(self, df):
        if df.empty:
            raise ValueError("Resources dataset is empty")

        missing_names = df["name"].isna().sum()
        if missing_names > 0:
            print(f"Warning: {missing_names} resources missing names")

        missing_zip = df["zip_code"].eq("").sum()
        if missing_zip > 0:
            print(f"Warning: {missing_zip} resources missing ZIP codes")

    def _validate_counties(self, df):
        if df.empty:
            print("Warning: County dataset is empty")
            return

        if "poverty_rate" in df.columns:
            missing = df["poverty_rate"].isna().sum()
            if missing > 0:
                print(f"Warning: {missing} counties missing poverty rate")

        if "unemployment_rate" in df.columns:
            missing = df["unemployment_rate"].isna().sum()
            if missing > 0:
                print(f"Warning: {missing} counties missing unemployment rate")
