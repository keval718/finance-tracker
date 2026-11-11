def test_register_login_and_me(client):
    r = client.post(
        "/api/auth/register", json={"email": "A@Example.com", "password": "password123"}
    )
    assert r.status_code == 201
    assert r.json()["email"] == "a@example.com"

    r = client.post(
        "/api/auth/login", data={"username": "a@example.com", "password": "password123"}
    )
    assert r.status_code == 200
    token = r.json()["access_token"]

    r = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r.json()["email"] == "a@example.com"


def test_duplicate_email_rejected(client):
    payload = {"email": "a@example.com", "password": "password123"}
    assert client.post("/api/auth/register", json=payload).status_code == 201
    assert client.post("/api/auth/register", json=payload).status_code == 409


def test_short_password_rejected(client):
    r = client.post("/api/auth/register", json={"email": "a@example.com", "password": "short"})
    assert r.status_code == 422


def test_wrong_password_rejected(client):
    client.post("/api/auth/register", json={"email": "a@example.com", "password": "password123"})
    r = client.post("/api/auth/login", data={"username": "a@example.com", "password": "nope-nope"})
    assert r.status_code == 401


def test_protected_routes_need_a_valid_token(client):
    assert client.get("/api/transactions").status_code == 401
    r = client.get("/api/transactions", headers={"Authorization": "Bearer not-a-token"})
    assert r.status_code == 401
