import pytest

from app.categorizer import categorize


@pytest.mark.parametrize(
    ("description", "amount", "expected"),
    [
        ("LOBLAWS #1042", -82.10, "Groceries"),
        ("UBER EATS", -31.00, "Dining"),
        ("UBER TRIP", -18.00, "Transport"),
        ("NETFLIX.COM", -20.99, "Subscriptions"),
        ("RENT PAYMENT - 88 HARBOUR ST", -1850.00, "Housing"),
        ("PAYROLL DEPOSIT - ACME CORP", 2650.00, "Income"),
        ("Something unknown", 50.00, "Income"),
        ("Something unknown", -50.00, "Other"),
        # A store refund stays in the store's category so it nets against the purchase.
        ("BEST BUY #954", 329.99, "Shopping"),
    ],
)
def test_categorize(description, amount, expected):
    assert categorize(description, amount) == expected


def test_keywords_match_whole_words_only():
    assert (
        categorize(
            "METROPOLIS BOOKS",
            -20,
        )
        == "Other"
    )
    assert categorize("PARENT COUNCIL DONATION", -20) == "Other"
