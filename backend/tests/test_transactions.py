from .conftest import register_and_login, upload

CSV = """Date,Description,Amount
2026-03-01,RENT PAYMENT,-1500.00
2026-03-05,LOBLAWS #12,-80.25
2026-03-05,TIM HORTONS,-4.50
2026-03-05,TIM HORTONS,-4.50
2026-03-15,PAYROLL DEPOSIT,3000.00
2026-04-02,NETFLIX.COM,-20.99
"""


def test_import_categorizes_and_is_idempotent(client, auth):
    r = upload(client, auth, CSV)
    assert r.json() == {"imported": 6, "skipped_duplicates": 0, "skipped_invalid": 0}

    # Importing the same file again adds nothing.
    r = upload(client, auth, CSV)
    assert r.json() == {"imported": 0, "skipped_duplicates": 6, "skipped_invalid": 0}

    # A file that overlaps only adds the new row.
    r = upload(client, auth, CSV + "2026-04-03,UBER TRIP,-15.00\n")
    assert r.json()["imported"] == 1

    items = client.get("/api/transactions", headers=auth).json()["items"]
    by_desc = {i["description"]: i["category"] for i in items}
    assert by_desc["RENT PAYMENT"] == "Housing"
    assert by_desc["PAYROLL DEPOSIT"] == "Income"
    assert by_desc["UBER TRIP"] == "Transport"


def test_import_rejects_bad_file(client, auth):
    r = upload(client, auth, "Foo,Bar\n1,2\n")
    assert r.status_code == 400


def test_filters_and_pagination(client, auth):
    upload(client, auth, CSV)
    get = lambda **params: client.get("/api/transactions", headers=auth, params=params).json()  # noqa: E731

    assert get()["total"] == 6
    assert get(month="2026-03")["total"] == 5
    assert get(category="Dining")["total"] == 2
    assert get(search="netflix")["total"] == 1

    page = get(page=2, page_size=4)
    assert len(page["items"]) == 2
    # Newest first.
    assert get()["items"][0]["description"] == "NETFLIX.COM"

    r = client.get("/api/transactions", headers=auth, params={"month": "2026-13"})
    assert r.status_code == 422


def test_create_update_delete(client, auth):
    r = client.post(
        "/api/transactions",
        headers=auth,
        json={"date": "2026-03-09", "description": "Starbucks", "amount": -6.25},
    )
    assert r.status_code == 201
    tx = r.json()
    assert tx["category"] == "Dining"

    r = client.patch(f"/api/transactions/{tx['id']}", headers=auth, json={"category": "Groceries"})
    assert r.json()["category"] == "Groceries"

    r = client.patch(f"/api/transactions/{tx['id']}", headers=auth, json={"category": "Nope"})
    assert r.status_code == 422

    assert client.delete(f"/api/transactions/{tx['id']}", headers=auth).status_code == 204
    assert client.get("/api/transactions", headers=auth).json()["total"] == 0


def test_users_cannot_see_or_change_each_others_data(client, auth):
    upload(client, auth, CSV)
    tx_id = client.get("/api/transactions", headers=auth).json()["items"][0]["id"]

    other = register_and_login(client, "other@example.com")
    assert client.get("/api/transactions", headers=other).json()["total"] == 0
    r = client.patch(f"/api/transactions/{tx_id}", headers=other, json={"category": "Dining"})
    assert r.status_code == 404
    assert client.delete(f"/api/transactions/{tx_id}", headers=other).status_code == 404

    # The same file imports cleanly for the second user: dedup is per user.
    assert upload(client, other, CSV).json()["imported"] == 6
