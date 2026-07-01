from app import app


def test_health_endpoint():
    client = app.test_client()
    response = client.get("/api/health")
    payload = response.get_json()
    assert response.status_code == 200
    assert payload["success"] is True


def test_seeded_college_modules():
    client = app.test_client()
    assert client.get("/api/students").get_json()["students"]
    assert client.get("/api/faculty").get_json()["faculty"]
    assert client.get("/api/courses").get_json()["courses"]
    assert client.get("/api/notices").get_json()["notices"]


def test_create_student_and_stats():
    client = app.test_client()
    response = client.post(
        "/api/students",
        json={
            "rollNo": "KCDS24AIML099",
            "name": "Test Student",
            "department": "AIML",
            "year": "2nd Year",
            "phone": "9999999999",
            "email": "test@student.edu",
            "attendance": 88,
            "feeDue": 5000,
        },
    )
    payload = response.get_json()
    assert response.status_code == 201
    assert payload["student"]["rollNo"] == "KCDS24AIML099"
    stats = client.get("/api/stats").get_json()["stats"]
    assert stats["studentCount"] >= 4


def test_create_faculty_validation():
    client = app.test_client()
    response = client.post("/api/faculty", json={})
    assert response.status_code == 400
    assert response.get_json()["success"] is False


def test_create_notice():
    client = app.test_client()
    response = client.post(
        "/api/notices",
        json={"title": "Holiday", "audience": "All", "priority": "Low", "message": "College holiday tomorrow."},
    )
    assert response.status_code == 201
    assert response.get_json()["notice"]["status"] == "Published"
