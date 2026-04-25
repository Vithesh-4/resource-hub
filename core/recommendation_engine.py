import pandas as pd
from core.config import WEIGHTS


# Main engine to generate ranked recommendations based on user input
class RecommendationEngine:

    def __init__(self, resources_df, county_df=None):
        # Store copies so original data is not modified
        self.resources_df = resources_df.copy() if resources_df is not None else pd.DataFrame()
        self.county_df = county_df.copy() if county_df is not None else pd.DataFrame()

    # HELPERS 

    def _safe_str(self, value):
        if pd.isna(value):
            return ""
        return str(value).strip()

    def _safe_float(self, value, default=0.0):
        try:
            if pd.isna(value):
                return default
            text = str(value).strip()
            if text == "":
                return default
            return float(text)
        except:
            return default

    def _safe_int(self, value, default=0):
        try:
            if pd.isna(value):
                return default
            text = str(value).strip()
            if text == "":
                return default
            return int(float(text))
        except:
            return default

    def _zip_prefix(self, value):
        z = self._safe_str(value)
        digits = "".join(ch for ch in z if ch.isdigit())
        return digits[:5]

    # LOCATION FILTER

    # Filters data based on location (zip > city > state)
    def _location_bucket(self, df, user_zip, user_city, user_state):

        if user_zip:
            same_zip = df[df["zip_code"].astype(str).str[:5] == user_zip].copy()
            if not same_zip.empty:
                return same_zip, "Best local match", 1.0

        if user_city and user_state:
            same_city_state = df[
                (df["city"].astype(str).str.strip().str.lower() == user_city) &
                (df["state"].astype(str).str.strip().str.upper() == user_state)
            ].copy()
            if not same_city_state.empty:
                return same_city_state, "Strong city match", 0.85

        if user_state:
            same_state = df[
                df["state"].astype(str).str.strip().str.upper() == user_state
            ].copy()
            if not same_state.empty:
                return same_state, "State-level match", 0.7

        return pd.DataFrame(), "", 0.0

    # MATCH SCORES 

    # Income-based matching
    def _income_match_score(self, row, user_profile):
        monthly_income = self._safe_float(getattr(user_profile, "monthly_income", 0))
        income_max = self._safe_float(row.get("income_max", None), -1)

        if income_max > 0:
            if monthly_income <= income_max:
                return 1.0
            elif monthly_income <= income_max * 1.2:
                return 0.6
            else:
                return 0.2

        return 0.5

    # Student eligibility match
    def _student_match_score(self, row, user_profile):
        student_only = self._safe_int(row.get("student_only", 0))
        is_student = bool(getattr(user_profile, "student_status", False))

        if student_only == 1:
            return 1.0 if is_student else 0.2

        return 0.5

    # Household size match
    def _household_match_score(self, row, user_profile):
        user_size = self._safe_int(getattr(user_profile, "household_size", 1))
        required = self._safe_int(row.get("household_size_min", None), -1)

        if required >= 0:
            return 1.0 if user_size >= required else 0.3

        return 0.5

    # Urgency boost
    def _urgency_boost(self, row, user_profile):
        user_urgency = self._safe_int(getattr(user_profile, "urgency_level", 3))

        if user_urgency >= 5:
            return 0.1
        elif user_urgency >= 3:
            return 0.05
        else:
            return 0.02

    # County-level context score
    def _county_context_score(self, row):
        if self.county_df.empty:
            return 0.5

        fips5 = self._safe_str(row.get("fips5", ""))
        match = self.county_df[self.county_df["fips5"].astype(str) == fips5]

        if match.empty:
            return 0.5

        row0 = match.iloc[0]

        poverty = self._safe_float(row0.get("poverty_rate", 0))
        unemployment = self._safe_float(row0.get("unemployment_rate", 0))

        score = 0.5 + min(poverty / 100, 0.3) + min(unemployment / 100, 0.2)
        return min(score, 1.0)

    # Resource quality (simple heuristic)
    def _resource_type_score(self, row):
        category = str(row.get("category", "")).strip().lower()

        if category == "food_assistance":
            return 1.0
        elif category == "healthcare_clinic":
            return 0.9
        elif category == "housing_support":
            return 0.9
        elif category == "job_training":
            return 0.85

        return 0.6

    #  EXPLANATION 

    def _build_reason(self, row, user_profile, final_score, tier_label):
        reasons = [tier_label]

        if self._income_match_score(row, user_profile) >= 0.9:
            reasons.append("income fit")

        if getattr(user_profile, "urgency_level", 3) >= 4:
            reasons.append("urgent need")

        return f"{'; '.join(reasons)}. Score: {round(final_score, 2)}"

    # MAIN 

    def generate_recommendations(self, user_profile, top_n=10):

        df = self.resources_df.copy()

        if df.empty:
            return pd.DataFrame()

        # Clean category
        df["category"] = df["category"].astype(str).str.strip().str.lower()

        user_need = self._safe_str(getattr(user_profile, "need_type", "")).lower()

        # Filter by category
        if user_need:
            df = df[df["category"] == user_need]

        if df.empty:
            return pd.DataFrame()

        # Get user location
        user_zip = self._zip_prefix(user_profile.zip_code)
        user_city = self._safe_str(user_profile.city).lower()
        user_state = self._safe_str(user_profile.state).upper()

        df, tier_label, location_base = self._location_bucket(df, user_zip, user_city, user_state)

        # Calculate score for each resource
        scores = []
        reasons = []

        for _, row in df.iterrows():

            income_score = self._income_match_score(row, user_profile)
            student_score = self._student_match_score(row, user_profile)
            household_score = self._household_match_score(row, user_profile)
            county_score = self._county_context_score(row)
            resource_score = self._resource_type_score(row)
            urgency = self._urgency_boost(row, user_profile)

            category = str(row.get("category", "")).strip().lower()

            # Get weights for category
            weights = WEIGHTS.get(category, WEIGHTS["food_assistance"])

            # Final weighted score
            final_score = (
                weights["location"] * location_base +
                weights["completeness"] * resource_score +
                weights["eligibility"] * income_score +
                weights["urgency"] * student_score +
                weights["county"] * county_score +
                urgency
            )

            scores.append(round(final_score, 4))
            reasons.append(self._build_reason(row, user_profile, final_score, tier_label))

        df["match_score"] = scores
        df["match_reason"] = reasons

        # Sort and return top results
        df = df.sort_values(by="match_score", ascending=False).head(top_n).reset_index(drop=True)

        return df