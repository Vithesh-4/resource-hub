import streamlit as st
import pandas as pd

from core.data_loader import DataLoader
from core.models import UserProfile
from core.recommendation_engine import RecommendationEngine
# Import config values
try:
    from core.config import TOP_N_RESULTS, MAX_CANDIDATES
except Exception:
    TOP_N_RESULTS = 10
    MAX_CANDIDATES = 10000
# Streamlit page setup
st.set_page_config(page_title="Resource Hub", layout="wide")
# styling for UI
st.markdown("""
<style>
.big-title {
    font-size: 38px;
    font-weight: 800;
    color: #1d3557;
}
.subtitle {
    font-size: 17px;
    color: #444;
    margin-bottom: 20px;
}
.rec-card {
    background: #ffffff;
    padding: 18px;
    border-radius: 14px;
    border: 1px solid #e6ecf5;
    margin-bottom: 12px;
}
.score-pill {
    display: inline-block;
    padding: 6px 12px;
    border-radius: 999px;
    background: #e8f1ff;
    color: #1d4ed8;
    font-weight: 600;
    font-size: 14px;
}
.small-muted {
    color: #666;
    font-size: 14px;
}
</style>
""", unsafe_allow_html=True)
# App title and subtitle
st.markdown('<div class="big-title">Resource Hub</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="subtitle">Find personalized community support resources based on your needs, location, and eligibility.</div>',
    unsafe_allow_html=True
)
# Mapping for category display names
CATEGORY_LABELS = {
    "food_assistance": "Food Assistance",
    "housing_support": "Housing Support",
    "job_training": "Job Training",
    "healthcare_clinic": "Healthcare Clinic",
}

# Load data from database 
@st.cache_data
def load_resources():
    loader = DataLoader()
    return loader.load_data()

# Normalize user location inputs
def normalize_location_inputs(city_value, state_value):
    city_value = "" if pd.isna(city_value) else str(city_value).strip()
    state_value = "" if pd.isna(state_value) else str(state_value).strip().upper()
# If user enters state in city field
    if not state_value and len(city_value) == 2 and city_value.isalpha():
        state_value = city_value.upper()
        city_value = ""

    return city_value, state_value


# Clean text
def safe_text(value):
    if pd.isna(value):
        return ""
    text = str(value).strip()
    if not text or text.lower() in {"nan", "none", "<na>"}:
        return ""
    return text

# Load resources and county data
resources_df, county_df = load_resources()
# Stop app if no data loaded
if resources_df.empty:
    st.error("No resource data was loaded.")
    st.stop()
#category dropdown
available_categories = sorted(resources_df["category"].dropna().astype(str).unique().tolist())
category_options = [c for c in available_categories if c in CATEGORY_LABELS] + [
    c for c in available_categories if c not in CATEGORY_LABELS
]
# Sidebar input section
with st.sidebar:
    st.header("Your Information")

    need_type = st.selectbox(
        "What kind of help do you need?",
        category_options,
        format_func=lambda x: CATEGORY_LABELS.get(x, x.replace("_", " ").title())
    )
# Location inputs
    zip_code = st.text_input("ZIP Code", "07307")
    city = st.text_input("City", "Jersey City")
    state = st.text_input("State (Example: NJ)", "NJ")
  # User details
    monthly_income = st.number_input("Monthly Income ($)", min_value=0.0, value=1200.0, step=100.0)
    household_size = st.number_input("Household Size", min_value=1, value=1, step=1)
    is_student = st.checkbox("I am a student", value=False)
    urgency_level = st.slider("Urgency Level", min_value=1, max_value=5, value=3)
 # Button to trigger recommendations
    find_btn = st.button("Find Resources")

if find_btn:
    city, state = normalize_location_inputs(city, state)
 # Build user profile object
    try:
        user_profile = UserProfile(
            need_type=safe_text(need_type).lower(),
            zip_code=safe_text(zip_code),
            city=safe_text(city),
            state=safe_text(state).upper(),
            monthly_income=float(monthly_income),
            household_size=int(household_size),
            student_status=bool(is_student),
            urgency_level=int(urgency_level)
        )
    except Exception as e:
        st.error(f"Could not build user profile: {e}")
        st.stop()

    recommendation_engine = RecommendationEngine(resources_df, county_df)
# Generate recommendations
    try:
        recommendations = recommendation_engine.generate_recommendations(
            user_profile=user_profile,
            top_n=TOP_N_RESULTS
        )
    except Exception as e:
        st.error(f"Recommendation generation failed: {e}")
        st.stop()

    st.subheader("Top Recommended Resources")

    if recommendations.empty:
        st.warning("No strong local matches were found. Try another ZIP, city, or state.")
    else:
 # Compute average score       
        if "match_score" in recommendations.columns:
            avg_score = round(float(recommendations["match_score"].fillna(0).mean()), 2)
        else:
            avg_score = 0.0
# Display summary metrics
        col1, col2, col3 = st.columns(3)
        col1.metric("Results Found", len(recommendations))
        col2.metric("Average Match Score", avg_score)
        col3.metric("Selected Need", CATEGORY_LABELS.get(str(need_type), str(need_type).replace("_", " ").title()))

        st.markdown("---")
# Display each recommendation
        for _, row in recommendations.iterrows():
            name = safe_text(row.get("name", "Unnamed Resource")) or "Unnamed Resource"
            category = safe_text(row.get("category", ""))
            subcategory = safe_text(row.get("subcategory", ""))
            address = safe_text(row.get("address", ""))
            city_val = safe_text(row.get("city", ""))
            state_val = safe_text(row.get("state", ""))
            zip_val = safe_text(row.get("zip_code", ""))
            phone = safe_text(row.get("phone", ""))  
            website = safe_text(row.get("website", ""))
            eligibility = safe_text(row.get("eligibility", ""))
            hours = safe_text(row.get("hours", ""))
            reason = safe_text(row.get("match_reason", ""))
            score = row.get("match_score", 0)
# Format score
            try:
                score_display = round(float(score), 2) if pd.notna(score) else 0.0
            except Exception:
                score_display = 0.0

            full_location = ", ".join([x for x in [address, city_val, state_val, zip_val] if x])
#card
            st.markdown('<div class="rec-card">', unsafe_allow_html=True)
            st.markdown(f"### {name}")
            st.markdown(
                f"<span class='score-pill'>Match Score: {score_display}</span>",
                unsafe_allow_html=True
            )

            if category:
                st.write(f"**Category:** {CATEGORY_LABELS.get(category, category.replace('_', ' ').title())}")

            if subcategory:
                st.write(f"**Subcategory:** {subcategory}")

            if full_location:
                st.write(f"**Location:** {full_location}")

            if phone:
                st.write(f"**Phone:** {phone}")

            if website:
                st.write(f"**Website:** {website}")

            if hours:
                st.write(f"**Hours:** {hours}")

            if eligibility:
                st.write(f"**Eligibility:** {eligibility}")

            if reason:
                st.write(f"**Why this matched:** {reason}")
            st.markdown('</div>', unsafe_allow_html=True)
#  table view
        display_cols = [c for c in [
            "name", "category", "subcategory", "city", "state", "zip_code",
            "match_score", "match_reason", "eligibility", "phone", "website", "source"
        ] if c in recommendations.columns]

        st.subheader("Recommendations Table")
        st.dataframe(recommendations[display_cols], use_container_width=True)
else:
    st.info("Fill in your details and click Find Resources.")