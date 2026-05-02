import pandas as pd


class CountyAnalyzer:
    def __init__(self, county_df):
        # Store a copy so original dataframe is not modified
        self.county_df = county_df.copy()

    def get_county_row(self, fips5):
        if not fips5:
            return None
# Find matching county row using FIPS code

        match = self.county_df[self.county_df["fips5"].astype(str) == str(fips5)]
        if match.empty:
            return None
            # Return the first matching row
        return match.iloc[0]

    def compute_need_score(self, fips5):
        # Get county information
        row = self.get_county_row(fips5)
        if row is None:
            return 0, "No county context available"

        score = 0
        notes = []
# Extract values
        poverty = row.get("poverty_rate")
        unemployment = row.get("unemployment_rate")
        snap = row.get("snap_recipients_est_2022")
        
        # NEW: Normalization function
        
        def normalize(value, max_value):
            if pd.isna(value) or max_value == 0:
                return 0
            return min(float(value) / max_value, 1.0)

        #  Normalize indicators
        poverty_score = normalize(poverty, 20)
        unemployment_score = normalize(unemployment, 10)
        snap_score = normalize(snap, 100000)

        #  Weighted scoring (NEW LOGIC)
        score = (
            0.5 * poverty_score +
            0.3 * unemployment_score +
            0.2 * snap_score
        ) * 20   # scale for readability

        #  Generate explanation
        if poverty_score > 0.7:
            notes.append("High poverty context")
        elif poverty_score > 0.4:
            notes.append("Moderate poverty context")

        if unemployment_score > 0.6:
            notes.append("Higher unemployment context")
        elif unemployment_score > 0.3:
            notes.append("Moderate unemployment context")

        if snap_score > 0.5:
            notes.append("Higher SNAP utilization context")

        summary = ", ".join(notes) if notes else "Average county context"
        return score, summary
