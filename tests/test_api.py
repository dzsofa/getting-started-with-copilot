from fastapi.testclient import TestClient
from urllib.parse import quote
from uuid import uuid4

from src.app import app


client = TestClient(app)


def test_get_activities():
    resp = client.get("/activities")
    assert resp.status_code == 200
    data = resp.json()
    # Should return a dict of activities
    assert isinstance(data, dict)
    assert len(data) > 0


def test_signup_and_unregister_flow():
    activities_resp = client.get("/activities")
    activities = activities_resp.json()
    # pick an activity
    activity_name = list(activities.keys())[0]

    # create a unique test email
    test_email = f"test-{uuid4().hex}@example.com"

    # Ensure it's not already registered
    assert test_email not in activities[activity_name]["participants"]

    # Sign up
    signup = client.post(
        f"/activities/{quote(activity_name)}/signup?email={test_email}")
    assert signup.status_code == 200
    assert test_email in signup.json().get("message", "")

    # Verify the participant appears in the activities list
    activities_after = client.get("/activities").json()
    assert test_email in activities_after[activity_name]["participants"]

    # Unregister
    unregister = client.post(
        f"/activities/{quote(activity_name)}/unregister?email={test_email}")
    assert unregister.status_code == 200
    assert test_email in unregister.json().get("message", "")

    # Verify removal
    activities_final = client.get("/activities").json()
    assert test_email not in activities_final[activity_name]["participants"]


def test_duplicate_signup_and_unregister_non_registered():
    activities_resp = client.get("/activities")
    activities = activities_resp.json()
    activity_name = list(activities.keys())[0]

    # unique email for this test
    test_email = f"dup-{uuid4().hex}@example.com"

    # First signup should succeed
    signup1 = client.post(
        f"/activities/{quote(activity_name)}/signup?email={test_email}")
    assert signup1.status_code == 200

    # Duplicate signup should fail with 400
    signup2 = client.post(
        f"/activities/{quote(activity_name)}/signup?email={test_email}")
    assert signup2.status_code == 400
    assert "already signed up" in signup2.json().get("detail", "").lower()

    # Unregister the email so we can test unregistering a non-registered email
    unregister_ok = client.post(
        f"/activities/{quote(activity_name)}/unregister?email={test_email}")
    assert unregister_ok.status_code == 200

    # Now try to unregister again — should fail with 400
    unregister_again = client.post(
        f"/activities/{quote(activity_name)}/unregister?email={test_email}")
    assert unregister_again.status_code == 400
    assert "not registered" in unregister_again.json().get("detail", "").lower()
