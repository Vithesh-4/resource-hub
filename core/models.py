from dataclasses import dataclass, field
from typing import Dict, Any

# Stores user input and preferences for recommendation
@dataclass
class UserProfile:
    need_type: str = ""
    zip_code: str = ""
    city: str = ""
    state: str = ""
    monthly_income: float = 0.0
    household_size: int = 1
    student_status: bool = False
    urgency_level: int = 3

    def __init__(
        self,
        need_type="",
        zip_code="",
        city="",
        state="",
        monthly_income=0.0,
        household_size=1,
        student_status=False,
        urgency_level=3,
    ):
        # Basic cleaning of inputs
        self.need_type = str(need_type).strip().lower()
        self.zip_code = str(zip_code).strip()
        self.city = str(city).strip()
        self.state = str(state).strip().upper()

        # Convert numeric values safely
        try:
            self.monthly_income = float(monthly_income)
        except:
            self.monthly_income = 0.0

        try:
            self.household_size = int(household_size)
        except:
            self.household_size = 1

        self.student_status = bool(student_status)

        # Handle urgency level (1–5)
        try:
            urgency_val = int(urgency_level)
        except:
            urgency_val = 3

        self.urgency_level = max(1, min(5, urgency_val))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "need_type": self.need_type,
            "zip_code": self.zip_code,
            "city": self.city,
            "state": self.state,
            "monthly_income": self.monthly_income,
            "household_size": self.household_size,
            "student_status": self.student_status,
            "urgency_level": self.urgency_level,
        }

# Represents a single recommended resource with scores
@dataclass
class ResourceRecommendation:
    resource_id: str = ""
    name: str = ""
    category: str = ""
    address: str = ""
    city: str = ""
    state: str = ""
    zip_code: str = ""
    phone: str = ""
    website: str = ""
    eligibility_notes: str = ""
    match_score: float = 0.0
    distance_score: float = 0.0
    urgency_score: float = 0.0
    eligibility_score: float = 0.0
    explanation: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "resource_id": self.resource_id,
            "name": self.name,
            "category": self.category,
            "address": self.address,
            "city": self.city,
            "state": self.state,
            "zip_code": self.zip_code,
            "phone": self.phone,
            "website": self.website,
            "eligibility_notes": self.eligibility_notes,
            "match_score": self.match_score,
            "distance_score": self.distance_score,
            "urgency_score": self.urgency_score,
            "eligibility_score": self.eligibility_score,
            "explanation": self.explanation,
        }

# Simplified result structure used for final output

@dataclass
class RecommendationResult:
    resource_id: str = ""
    name: str = ""
    category: str = ""
    score: float = 0.0
    distance: float = 0.0
    eligibility_score: float = 0.0
    urgency_score: float = 0.0
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "resource_id": self.resource_id,
            "name": self.name,
            "category": self.category,
            "score": self.score,
            "distance": self.distance,
            "eligibility_score": self.eligibility_score,
            "urgency_score": self.urgency_score,
            "details": self.details,
        }