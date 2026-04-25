from pathlib import Path
# Base directory of the project
BASE_DIR = Path(__file__).resolve().parent.parent
# Data folder where database and CSV files are stored
DATA_DIR = BASE_DIR / "data"
# Path to the SQLite database file
DB_PATH = DATA_DIR / "resource_hub_fresh.db"
# Number of top results to show to user
TOP_N_RESULTS = 10
MAX_CANDIDATES = 10000

# Weights used for scoring different types of resources
# I adjusted these based on importance of each factor
WEIGHTS = {
    "food_assistance": {
        "location": 0.30,
        "completeness": 0.15,
        "urgency": 0.25,
        "eligibility": 0.20,
        "county": 0.10,
    },
    "healthcare_clinic": {
        "location": 0.35,
        "completeness": 0.20,
        "urgency": 0.20,
        "eligibility": 0.15,
        "county": 0.10,
    },
    "housing_support": {
        "location": 0.25,
        "completeness": 0.15,
        "urgency": 0.30,
        "eligibility": 0.20,
        "county": 0.10,
    },
    "job_training": {
        "location": 0.25,
        "completeness": 0.20,
        "urgency": 0.20,
        "eligibility": 0.25,
        "county": 0.10,
    },
}