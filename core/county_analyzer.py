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
        poverty = row.get("poverty_rate_23")
        unemployment = row.get("unemployment_rate_2023")
        snap = row.get("snap_recipients_est_2022")
# Higher poverty means higher need
        if pd.notna(poverty):
            if float(poverty) >= 18:
                score += 12
                notes.append("High poverty context")
            elif float(poverty) >= 10:
                score += 6
                notes.append("Moderate poverty context")
# Higher unemployment increases need
        if pd.notna(unemployment):
            if float(unemployment) >= 6:
                score += 10
                notes.append("Higher unemployment context")
            elif float(unemployment) >= 4:
                score += 5
                notes.append("Moderate unemployment context")
# SNAP usage indicates economic difficulty
        if pd.notna(snap):
            if float(snap) > 50000:
                score += 8
                notes.append("Higher SNAP utilization context")

        summary = ", ".join(notes) if notes else "Average county context"
        return score, summary