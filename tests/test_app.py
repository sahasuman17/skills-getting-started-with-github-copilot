import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add the src directory to the path so we can import app
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app import app

client = TestClient(app)


class TestActivitiesEndpoint:
    """Test suite for /activities endpoint"""

    def test_get_activities_returns_200(self):
        """Test that GET /activities returns status code 200"""
        response = client.get("/activities")
        assert response.status_code == 200

    def test_get_activities_returns_dict(self):
        """Test that GET /activities returns a dictionary"""
        response = client.get("/activities")
        assert isinstance(response.json(), dict)

    def test_get_activities_contains_expected_activities(self):
        """Test that activities list contains expected activities"""
        response = client.get("/activities")
        activities = response.json()
        expected_activities = ["Chess Club", "Programming Class", "Gym Class"]
        for activity in expected_activities:
            assert activity in activities

    def test_activity_has_required_fields(self):
        """Test that each activity has required fields"""
        response = client.get("/activities")
        activities = response.json()
        required_fields = {"description", "schedule", "max_participants", "participants"}
        
        for activity_name, details in activities.items():
            assert required_fields.issubset(set(details.keys())), \
                f"Activity '{activity_name}' missing required fields"


class TestSignupEndpoint:
    """Test suite for POST /activities/{activity_name}/signup endpoint"""

    def test_signup_success(self):
        """Test successful signup"""
        response = client.post(
            "/activities/Chess Club/signup?email=test@mergington.edu"
        )
        assert response.status_code == 200
        assert "Signed up" in response.json()["message"]

    def test_signup_duplicate_email_returns_400(self):
        """Test that duplicate signup returns 400 error"""
        email = "duplicate@mergington.edu"
        # First signup
        client.post(f"/activities/Chess Club/signup?email={email}")
        # Duplicate signup
        response = client.post(f"/activities/Chess Club/signup?email={email}")
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"]

    def test_signup_nonexistent_activity_returns_404(self):
        """Test that signup for nonexistent activity returns 404"""
        response = client.post(
            "/activities/Nonexistent Club/signup?email=test@mergington.edu"
        )
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]

    def test_signup_full_activity_returns_400(self):
        """Test that signup for full activity returns 400"""
        # Find an activity and fill it up
        response = client.get("/activities")
        activities = response.json()
        
        # Use an activity with low max_participants
        full_activity = None
        for activity_name, details in activities.items():
            if len(details["participants"]) >= details["max_participants"]:
                full_activity = activity_name
                break
        
        if full_activity:
            response = client.post(
                f"/activities/{full_activity}/signup?email=overcapacity@mergington.edu"
            )
            assert response.status_code == 400
            assert "full" in response.json()["detail"]

    def test_signup_adds_participant_to_list(self):
        """Test that signup adds participant to activity"""
        email = "newparticipant@mergington.edu"
        activity_name = "Art Club"
        
        # Get initial count
        response = client.get("/activities")
        initial_count = len(response.json()[activity_name]["participants"])
        
        # Sign up
        client.post(f"/activities/{activity_name}/signup?email={email}")
        
        # Check count increased
        response = client.get("/activities")
        new_count = len(response.json()[activity_name]["participants"])
        assert new_count == initial_count + 1


class TestUnregisterEndpoint:
    """Test suite for POST /activities/{activity_name}/unregister endpoint"""

    def test_unregister_success(self):
        """Test successful unregister"""
        email = "unregister@mergington.edu"
        activity_name = "Drama Club"
        
        # Sign up first
        client.post(f"/activities/{activity_name}/signup?email={email}")
        
        # Now unregister
        response = client.post(
            f"/activities/{activity_name}/unregister?email={email}"
        )
        assert response.status_code == 200
        assert "Unregistered" in response.json()["message"]

    def test_unregister_nonexistent_activity_returns_404(self):
        """Test that unregister from nonexistent activity returns 404"""
        response = client.post(
            "/activities/Nonexistent Club/unregister?email=test@mergington.edu"
        )
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]

    def test_unregister_not_signed_up_returns_400(self):
        """Test that unregister without signup returns 400"""
        response = client.post(
            "/activities/Chess Club/unregister?email=never_signed_up@mergington.edu"
        )
        assert response.status_code == 400
        assert "not signed up" in response.json()["detail"]

    def test_unregister_removes_participant_from_list(self):
        """Test that unregister removes participant from activity"""
        email = "remove_me@mergington.edu"
        activity_name = "Swimming Club"
        
        # Sign up
        client.post(f"/activities/{activity_name}/signup?email={email}")
        
        # Get count before unregister
        response = client.get("/activities")
        count_before = len(response.json()[activity_name]["participants"])
        
        # Unregister
        client.post(f"/activities/{activity_name}/unregister?email={email}")
        
        # Check count decreased
        response = client.get("/activities")
        count_after = len(response.json()[activity_name]["participants"])
        assert count_after == count_before - 1


class TestRootEndpoint:
    """Test suite for GET / endpoint"""

    def test_root_redirects_to_static_index(self):
        """Test that root endpoint redirects to static index"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"
