from core.config import WEIGHTS
import pandas as pd


# Normalize value between 0 and 1
def normalize(value, max_val):
    if max_val is None:
        return 0
    if max_val == 0:
        return 0
    return min(value / max_val, 1)


class RankingEngine:

    # Score based on location match (zip > city > state)
    def compute_location_score(self, row, user_profile):
        score = 0

        row_zip = str(row.get("zip_code", "")).strip()
        row_city = str(row.get("city", "")).strip().lower()
        row_state = str(row.get("state", "")).strip().upper()

        user_zip = str(getattr(user_profile, "zip_code", "")).strip()
        user_city = str(getattr(user_profile, "city", "")).strip().lower()
        user_state = str(getattr(user_profile, "state", "")).strip().upper()

        if user_zip and row_zip == user_zip:
            score += 1.0
        elif user_city and row_city == user_city:
            score += 0.7
        elif user_state and row_state == user_state:
            score += 0.5
        else:
            score += 0.2

        return score


    # Check how complete the resource information is
    def compute_completeness_score(self, row):
        fields = ["phone", "website", "hours", "address"]

        present = sum(
            1 for f in fields
            if pd.notna(row.get(f)) and str(row.get(f)).strip() != ""
        )

        return present / len(fields)


    # Score based on urgency support
    def compute_urgency_score(self, row, user_profile):
        urgency_support = row.get("urgency_support", 0)
        user_urgency = getattr(user_profile, "urgency_level", 3)

        try:
            urgency_support = int(urgency_support)
        except:
            urgency_support = 0

        if urgency_support == 1 and user_urgency >= 4:
            return 1.0
        elif user_urgency >= 3:
            return 0.7
        else:
            return 0.5


    # Normalize eligibility score 
    def compute_eligibility_score(self, eligibility_score):
        try:
            return max(min(float(eligibility_score) / 100, 1), 0)
        except:
            return 0


    # Normalize county score
    def compute_county_score(self, county_score):
        try:
            return normalize(float(county_score), 30)
        except:
            return 0


    # Combine all scores using weights
    def compute_final_score(self, category, scores):
        category = str(category).strip().lower()

        # Get weights for category
        if category in WEIGHTS:
            weights = WEIGHTS[category]
        else:
            weights = WEIGHTS["food_assistance"]

        final = 0
        for key, value in scores.items():
            final += value * weights.get(key, 0)
            
        return round(final, 4)