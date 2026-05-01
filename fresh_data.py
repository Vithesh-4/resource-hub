import pandas as pd
import sqlite3
import hashlib
import re
from pathlib import Path


# PATHS
BASE_DIR = Path(__file__).resolve().parent

IN_DIR = BASE_DIR / "data_input"
OUT_DIR = BASE_DIR / "data"

OUT_DIR.mkdir(parents=True, exist_ok=True)

MASTER_FILE = IN_DIR / "resource_hub_master.csv"
COUNTY_FILE = IN_DIR / "county_context_index.csv"
ZIP_TO_FIPS_FILE = IN_DIR / "zip_to_fips.csv"

# Auto-detect housing file
housing_matches = list(IN_DIR.glob("Public_Housing*.csv"))

# Auto-detect training file
training_matches_xlsx = list(IN_DIR.glob("*AJC*.xlsx"))
training_matches_csv = list(IN_DIR.glob("*AJC*.csv"))

# Your new HRSA clinic file
CLINIC_FILE = IN_DIR / "Health_Center_Service_Delivery_and_LookAlike_Sites.csv"

OUT_CSV = OUT_DIR / "resource_hub_merged.csv"
OUT_DB = OUT_DIR / "resource_hub_fresh.db"


# FILE CHECKS
if not MASTER_FILE.exists():
    raise FileNotFoundError(f"Master file not found: {MASTER_FILE}")

if not COUNTY_FILE.exists():
    raise FileNotFoundError(f"County context file not found: {COUNTY_FILE}")

if not housing_matches:
    raise FileNotFoundError("No housing CSV found in data_input folder")
HOUSING_FILE = housing_matches[0]

if training_matches_xlsx:
    TRAINING_FILE = training_matches_xlsx[0]
elif training_matches_csv:
    TRAINING_FILE = training_matches_csv[0]
else:
    raise FileNotFoundError("No training file found in data_input folder")

BASE_COLS = [
    "resource_id", "name", "category", "subcategory", "eligibility_text",
    "income_max", "student_only", "household_size_min", "urgency_support",
    "documents_required", "address", "city", "state", "zip", "latitude",
    "longitude", "phone", "website", "hours", "is_online", "source"
]

EXTRA_COLS = ["county", "fips5"]
FINAL_COLS = BASE_COLS + EXTRA_COLS

#Helpers
def clean_zip(z):
    if pd.isna(z):
        return None
    s = re.sub(r"\D", "", str(z))
    if not s:
        return None
    return s[:5].zfill(5)

def clean_phone(p):
    if pd.isna(p):
        return None

    s = str(p).strip()

    # remove extensions like x1234 or ext 1234
    s = re.split(r"(?:ext\.?|x)\s*\d+", s, flags=re.IGNORECASE)[0]

    digits = re.sub(r"\D", "", s)

    return digits if digits else None

def safe_float(x):
    try:
        if pd.isna(x):
            return None
        return float(x)
    except Exception:
        return None

def make_id(source, name, address, zip5):
    key = f"{source}|{name}|{address}|{zip5}".lower().strip()
    h = hashlib.sha1(key.encode("utf-8")).hexdigest()[:16]
    return f"RH_{h}"

def ensure_schema(df):
    for c in BASE_COLS:
        if c not in df.columns:
            df[c] = None

    for c in EXTRA_COLS:
        if c not in df.columns:
            df[c] = None

    df = df[FINAL_COLS].copy()

    df["zip"] = df["zip"].apply(clean_zip)
    df["phone"] = df["phone"].apply(clean_phone)
    df["latitude"] = df["latitude"].apply(safe_float)
    df["longitude"] = df["longitude"].apply(safe_float)
    df["income_max"] = pd.to_numeric(df["income_max"], errors="coerce")
    df["household_size_min"] = pd.to_numeric(df["household_size_min"], errors="coerce")

    for col in ["student_only", "urgency_support", "is_online"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)

    for col in [
        "resource_id", "name", "category", "subcategory", "eligibility_text",
        "documents_required", "address", "city", "state", "website",
        "hours", "source", "county", "fips5"
    ]:
        df[col] = df[col].astype("string").str.strip()

    return df

def dedupe(df):
    df = df.drop_duplicates(subset=["resource_id"], keep="first").copy()

    key = (
        df["category"].fillna("") + "|" +
        df["name"].fillna("") + "|" +
        df["address"].fillna("") + "|" +
        df["zip"].fillna("")
    ).str.lower()

    df["_dup_key"] = key
    df = df.drop_duplicates(subset=["_dup_key"], keep="first").drop(columns=["_dup_key"])
    return df


# LOADERS
def load_master():
    df = pd.read_csv(MASTER_FILE, dtype={"zip": str}, low_memory=False)
    return ensure_schema(df)

def load_housing():
    df = pd.read_csv(HOUSING_FILE, dtype={"STD_ZIP5": str}, low_memory=False)

    out = pd.DataFrame()
    out["name"] = (
        df["FORMAL_PARTICIPANT_NAME"].astype("string").fillna("").str.strip()
        + " - " +
        df["PROJECT_NAME"].astype("string").fillna("").str.strip()
    ).str.strip()

    out["category"] = "housing_support"
    out["subcategory"] = "public_housing"
    out["eligibility_text"] = "Contact housing authority for eligibility and application details."
    out["income_max"] = None
    out["student_only"] = 0
    out["household_size_min"] = None
    out["urgency_support"] = 1
    out["documents_required"] = None

    out["address"] = df["STD_ADDR"]
    out["city"] = df["STD_CITY"]
    out["state"] = df["STD_ST"]
    out["zip"] = df["STD_ZIP5"]
    out["latitude"] = df["LAT"]
    out["longitude"] = df["LON"]
    out["phone"] = df["HA_PHN_NUM"] if "HA_PHN_NUM" in df.columns else None

    out["website"] = None
    out["hours"] = None
    out["is_online"] = 0
    out["source"] = "hud_housing"
    out["county"] = None
    out["fips5"] = None

    out["resource_id"] = [
        make_id("hud_housing", str(n), str(a), str(clean_zip(z)))
        for n, a, z in zip(out["name"], out["address"], out["zip"])
    ]

    return ensure_schema(out)

def load_training():
    if TRAINING_FILE.suffix.lower() == ".xlsx":
        df = pd.read_excel(TRAINING_FILE, dtype={"Zip Code": str})
    else:
        df = pd.read_csv(TRAINING_FILE, dtype={"Zip Code": str}, low_memory=False)

    out = pd.DataFrame()
    out["name"] = df["Name of Center"].astype("string").str.strip()
    out["category"] = "job_training"
    out["subcategory"] = "american_job_center"
    out["eligibility_text"] = "Contact center for program eligibility and enrollment details."
    out["income_max"] = None
    out["student_only"] = 0
    out["household_size_min"] = None
    out["urgency_support"] = 0
    out["documents_required"] = None

    out["address"] = df["Address1"]
    out["city"] = df["City"]
    out["state"] = df["State"]
    out["zip"] = df["Zip Code"]
    out["latitude"] = df["Latitiude"]
    out["longitude"] = df["Longitude"]
    out["phone"] = df["Phone"]
    out["website"] = df["Web Site URL"]

    out["hours"] = None
    out["is_online"] = 0
    out["source"] = "american_job_centers"
    out["county"] = None
    out["fips5"] = None

    out["resource_id"] = [
        make_id("american_job_centers", str(n), str(a), str(clean_zip(z)))
        for n, a, z in zip(out["name"], out["address"], out["zip"])
    ]

    return ensure_schema(out)

def load_clinics():
    if not CLINIC_FILE.exists():
        print(f"[INFO] Clinic file not found, skipping: {CLINIC_FILE}")
        return pd.DataFrame(columns=FINAL_COLS)

    df = pd.read_csv(
        CLINIC_FILE,
        dtype={
            "Site Postal Code": str,
            "State and County Federal Information Processing Standard Code": str
        },
        low_memory=False
    )

    out = pd.DataFrame()

    out["name"] = df["Site Name"].astype("string").str.strip()
    out["category"] = "healthcare_clinic"
    out["subcategory"] = df["Health Center Type"].astype("string").str.strip()

    out["eligibility_text"] = (
        "HRSA-supported health center site offering community-based care. "
        "Contact the clinic for services, eligibility, sliding-fee, and appointment details."
    )

    out["income_max"] = None
    out["student_only"] = 0
    out["household_size_min"] = None
    out["urgency_support"] = 1
    out["documents_required"] = None

    out["address"] = df["Site Address"]
    out["city"] = df["Site City"]
    out["state"] = df["Site State Abbreviation"]
    out["zip"] = df["Site Postal Code"]

    # HRSA file uses X = longitude, Y = latitude
    out["latitude"] = df["Geocoding Artifact Address Primary Y Coordinate"]
    out["longitude"] = df["Geocoding Artifact Address Primary X Coordinate"]

    out["phone"] = df["Site Telephone Number"]
    out["website"] = df["Site Web Address"]
    out["hours"] = df["Operating Hours per Week"].astype("string")
    out["is_online"] = 0
    out["source"] = "hrsa_health_centers"

    out["county"] = (
        df["Complete County Name"]
        .astype("string")
        .str.replace(" County", "", regex=False)
        .str.strip()
    )
    out["fips5"] = (
        df["State and County Federal Information Processing Standard Code"]
        .astype("string")
        .str.strip()
    )

    out["resource_id"] = [
        make_id("hrsa_health_centers", str(n), str(a), str(clean_zip(z)))
        for n, a, z in zip(out["name"], out["address"], out["zip"])
    ]

    return ensure_schema(out)

def load_county_context():
    df = pd.read_csv(COUNTY_FILE, dtype={"fips5": str}, low_memory=False)

    if "state" in df.columns:
        df["state"] = df["state"].astype("string").str.strip().str.upper()
    if "county" in df.columns:
        df["county"] = df["county"].astype("string").str.strip()
    if "fips5" in df.columns:
        df["fips5"] = df["fips5"].astype("string").str.strip()

    return df

def enrich_with_zip_to_fips(resources, county_df):
    if not ZIP_TO_FIPS_FILE.exists():
        return resources

    z2f = pd.read_csv(
        ZIP_TO_FIPS_FILE,
        dtype={"zip": str, "fips5": str},
        low_memory=False
    )

    if "zip" not in z2f.columns or "fips5" not in z2f.columns:
        raise ValueError("zip_to_fips.csv must contain columns: zip and fips5")

    z2f["zip"] = z2f["zip"].apply(clean_zip)
    z2f["fips5"] = z2f["fips5"].astype("string").str.strip()

    resources = resources.merge(
        z2f[["zip", "fips5"]],
        on="zip",
        how="left",
        suffixes=("", "_new")
    )
    resources["fips5"] = resources["fips5"].fillna(resources["fips5_new"])
    resources = resources.drop(columns=["fips5_new"])

    if "fips5" in county_df.columns and "county" in county_df.columns:
        county_lookup = county_df[["fips5", "county"]].drop_duplicates(subset=["fips5"])
        resources = resources.merge(
            county_lookup,
            on="fips5",
            how="left",
            suffixes=("", "_new")
        )
        resources["county"] = resources["county"].fillna(resources["county_new"])
        resources = resources.drop(columns=["county_new"])

    return ensure_schema(resources)

# DATABASE BUILD
def build_database(resources, county):
    conn = sqlite3.connect(OUT_DB)
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS resources (
        resource_id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        category TEXT NOT NULL,
        subcategory TEXT,
        eligibility_text TEXT,
        income_max REAL,
        student_only INTEGER,
        household_size_min INTEGER,
        urgency_support INTEGER,
        documents_required TEXT,
        address TEXT,
        city TEXT,
        state TEXT,
        zip TEXT,
        latitude REAL,
        longitude REAL,
        phone TEXT,
        website TEXT,
        hours TEXT,
        is_online INTEGER,
        source TEXT NOT NULL,
        county TEXT,
        fips5 TEXT
    )
    """)

    cur.execute("DELETE FROM resources")
    conn.commit()

    resources.to_sql("resources", conn, if_exists="append", index=False)
    county.to_sql("county_context", conn, if_exists="replace", index=False)

    cur.execute("CREATE INDEX IF NOT EXISTS idx_resources_zip ON resources(zip)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_resources_category ON resources(category)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_resources_state_zip ON resources(state, zip)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_resources_lat_lon ON resources(latitude, longitude)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_resources_fips5 ON resources(fips5)")

    if "fips5" in county.columns:
        cur.execute("CREATE INDEX IF NOT EXISTS idx_county_fips5 ON county_context(fips5)")

    conn.commit()
    conn.close()


# main
def main():
    print("MASTER_FILE:", MASTER_FILE)
    print("HOUSING_FILE:", HOUSING_FILE)
    print("TRAINING_FILE:", TRAINING_FILE)
    print("CLINIC_FILE:", CLINIC_FILE)
    print("COUNTY_FILE:", COUNTY_FILE)

    master = load_master()
    housing = load_housing()
    training = load_training()
    clinics = load_clinics()
    county = load_county_context()

    print("Master rows loaded:", len(master))
    print("Housing rows loaded:", len(housing))
    print("Training rows loaded:", len(training))
    print("Clinic rows loaded:", len(clinics))

    merged = pd.concat([master, housing, training, clinics], ignore_index=True)
    merged = ensure_schema(merged)
    merged = dedupe(merged)
    merged = enrich_with_zip_to_fips(merged, county)

    merged.to_csv(OUT_CSV, index=False)
    build_database(merged, county)

    print(f"Merged dataset created: {OUT_CSV}")
    print(f"Database created: {OUT_DB}")

if __name__ == "__main__":
    main()