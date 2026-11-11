from .conftest import upload

CSV = """Date,Description,Amount
2026-01-10,LOBLAWS,-100.00
2026-03-01,RENT PAYMENT,-1500.00
2026-03-05,LOBLAWS #12,-80.00
2026-03-06,BEST BUY,-300.00
2026-03-08,BEST BUY,300.00
2026-03-09,AMAZON.CA,-50.00
2026-03-15,PAYROLL DEPOSIT,3000.00
"""


def test_budget_upsert_and_delete(client, auth):
    r = client.put(
        "/api/budgets", headers=auth, json={"category": "Groceries", "monthly_limit": 400}
    )
    assert r.status_code == 200
    budget_id = r.json()["id"]

    r = client.put(
        "/api/budgets", headers=auth, json={"category": "Groceries", "monthly_limit": 500}
    )
    assert r.json() == {"id": budget_id, "category": "Groceries", "monthly_limit": 500.0}
    assert len(client.get("/api/budgets", headers=auth).json()) == 1

    for bad in (
        {"category": "Income", "monthly_limit": 100},
        {"category": "Groceries", "monthly_limit": 0},
    ):
        assert client.put("/api/budgets", headers=auth, json=bad).status_code == 422

    assert client.delete(f"/api/budgets/{budget_id}", headers=auth).status_code == 204
    assert client.get("/api/budgets", headers=auth).json() == []


def test_monthly_summary(client, auth):
    upload(client, auth, CSV)
    client.put("/api/budgets", headers=auth, json={"category": "Groceries", "monthly_limit": 200})
    client.put("/api/budgets", headers=auth, json={"category": "Dining", "monthly_limit": 100})

    s = client.get("/api/analytics/summary", headers=auth, params={"month": "2026-03"}).json()
    assert s["income"] == 3000.0
    # The Best Buy purchase and refund cancel out, leaving only Amazon in Shopping.
    assert s["by_category"] == [
        {"category": "Housing", "total": 1500.0},
        {"category": "Groceries", "total": 80.0},
        {"category": "Shopping", "total": 50.0},
    ]
    assert s["expenses"] == 1630.0
    assert s["net"] == 1370.0
    assert s["savings_rate"] == 45.7

    budgets = {b["category"]: b for b in s["budgets"]}
    assert budgets["Groceries"] == {
        "category": "Groceries",
        "monthly_limit": 200.0,
        "spent": 80.0,
        "remaining": 120.0,
        "percent_used": 40.0,
    }
    assert budgets["Dining"]["spent"] == 0.0
    assert s["top_expenses"][0]["description"] == "RENT PAYMENT"


def test_summary_for_empty_month(client, auth):
    s = client.get("/api/analytics/summary", headers=auth, params={"month": "2020-01"}).json()
    assert (s["income"], s["expenses"], s["savings_rate"], s["by_category"]) == (0.0, 0.0, 0.0, [])


def test_trend_fills_gaps_and_months_list(client, auth):
    assert client.get("/api/analytics/trend", headers=auth).json() == []

    upload(client, auth, CSV)
    trend = client.get("/api/analytics/trend", headers=auth).json()
    assert [p["month"] for p in trend] == ["2026-01", "2026-02", "2026-03"]
    assert trend[1] == {"month": "2026-02", "income": 0.0, "expenses": 0.0, "net": 0.0}
    assert trend[2] == {"month": "2026-03", "income": 3000.0, "expenses": 1630.0, "net": 1370.0}

    assert len(client.get("/api/analytics/trend", headers=auth, params={"months": 1}).json()) == 1
    assert client.get("/api/analytics/months", headers=auth).json() == ["2026-03", "2026-01"]
