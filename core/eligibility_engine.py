import pandas as pd


class EligibilityEngine:
    def check_row_eligibility(self, row, user_profile):
        # Get category of resource
        category = str(row.get("category", "")).strip().lower()

        # Food assistance is generally open to most people
        if category == "food_assistance":
            return 20, "Generally Accessible", ["SNAP-authorized food access location"]

        score = 0
        reasons = []

        # Check if program is student-only
        student_only = row.get("student_only")
        if pd.notna(student_only):
            try:
                val = int(student_only)
                if val == 1:
                    if user_profile.student_status:
                        score += 25
                        reasons.append("Matches student eligibility")
                    else:
                        score -= 35
                        reasons.append("Program appears limited to students")
                else:
                    score += 5
            except Exception:
                pass   # ignore bad data

        # Check income eligibility
        income_max = row.get("income_max")
        if pd.notna(income_max):
            try:
                user_income = float(user_profile.monthly_income)
                limit = float(income_max)

                if user_income <= limit:
                    score += 30
                    reasons.append("Income appears within listed limit")
                else:
                    score -= 20
                    reasons.append("Income may exceed listed limit")
            except Exception:
                reasons.append("Income could not be evaluated")
        else:
            score += 8
            reasons.append("No hard income limit listed")

        # Check household size requirement
        household_min = row.get("household_size_min")
        if pd.notna(household_min):
            try:
                if int(user_profile.household_size) >= int(household_min):
                    score += 15
                    reasons.append("Household size fits requirement")
                else:
                    score -= 10
                    reasons.append("Household size may not meet requirement")
            except Exception:
                reasons.append("Household size rule unclear")
        else:
            score += 5

        # Final eligibility status
        if score >= 45:
            status = "Likely Eligible"
        elif score >= 15:
            status = "Possibly Eligible"
        else:
            status = "Eligibility Unclear"

        return score, status, reasons