# Basic tests for UserProfile class

from core.models import UserProfile

def test_user_profile():
    user = UserProfile(zip_code="07307")
    assert user.zip_code == "07307"

def test_income():
    user = UserProfile(monthly_income=2000)
    assert user.monthly_income == 2000

def test_household():
    user = UserProfile(household_size=3)
    assert user.household_size == 3

def test_student():
    user = UserProfile(student_status=True)
    assert user.student_status is True

def test_urgency():
    user = UserProfile(urgency_level=5)
    assert user.urgency_level == 5