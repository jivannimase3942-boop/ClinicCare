def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "status" in data


def test_user_registration(client):
    payload = {
        "email": "newpatient@test.com",
        "password": "Password123",
        "full_name": "New Test Patient",
        "phone": "+1999888777",
        "role": "PATIENT",
        "gender": "female",
        "blood_group": "A+"
    }
    response = client.post("/api/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    assert "access_token" in data["data"]
    assert data["data"]["user"]["email"] == "newpatient@test.com"


def test_duplicate_registration_fails(client, seed_test_data):
    payload = {
        "email": "patient@hospital.com",
        "password": "Password123",
        "full_name": "Duplicate Patient"
    }
    response = client.post("/api/auth/register", json=payload)
    assert response.status_code == 400


def test_user_login_success(client, seed_test_data):
    payload = {
        "email": "patient@hospital.com",
        "password": "Patient@123"
    }
    response = client.post("/api/auth/login", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "access_token" in data["data"]


def test_user_login_invalid_password(client, seed_test_data):
    payload = {
        "email": "patient@hospital.com",
        "password": "WrongPassword"
    }
    response = client.post("/api/auth/login", json=payload)
    assert response.status_code == 401


def test_get_current_user_me(client, seed_test_data):
    login_resp = client.post("/api/auth/login", json={"email": "patient@hospital.com", "password": "Patient@123"})
    token = login_resp.json()["data"]["access_token"]

    response = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["email"] == "patient@hospital.com"
