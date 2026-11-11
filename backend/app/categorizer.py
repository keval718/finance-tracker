"""Rule-based transaction categorizer.

Each category has a list of keywords. A transaction gets the first category
whose keyword appears in its description. Rules are checked in order, so more
specific categories are listed before broader ones.
"""

import re

INCOME = "Income"
UNCATEGORIZED = "Other"

RULES: dict[str, list[str]] = {
    "Housing": ["rent", "mortgage", "property tax", "condo fee"],
    "Utilities": [
        "hydro",
        "electric",
        "water bill",
        "enbridge",
        "internet",
        "rogers",
        "bell",
        "telus",
        "fido",
    ],
    "Groceries": [
        "loblaws",
        "no frills",
        "metro",
        "sobeys",
        "walmart",
        "costco",
        "freshco",
        "whole foods",
        "grocery",
        "farm boy",
    ],
    "Dining": [
        "restaurant",
        "tim hortons",
        "starbucks",
        "mcdonald",
        "uber eats",
        "doordash",
        "skip the dishes",
        "pizza",
        "cafe",
        "sushi",
        "subway",
    ],
    "Transport": [
        "uber",
        "lyft",
        "presto",
        "ttc",
        "shell",
        "esso",
        "petro",
        "gas station",
        "parking",
        "via rail",
    ],
    "Subscriptions": [
        "netflix",
        "spotify",
        "disney",
        "prime video",
        "youtube premium",
        "icloud",
        "github",
        "chatgpt",
        "claude",
    ],
    "Shopping": [
        "amazon",
        "best buy",
        "ikea",
        "winners",
        "h&m",
        "zara",
        "canadian tire",
        "apple store",
    ],
    "Health": [
        "pharmacy",
        "shoppers drug",
        "rexall",
        "dental",
        "clinic",
        "goodlife",
        "gym",
        "physio",
    ],
    "Entertainment": ["cineplex", "steam", "playstation", "ticketmaster", "concert", "bowling"],
    "Travel": ["air canada", "westjet", "airbnb", "hotel", "expedia", "booking.com"],
    "Fees": ["service fee", "interest charge", "atm fee", "overdraft", "nsf"],
}

INCOME_KEYWORDS = [
    "payroll",
    "salary",
    "deposit",
    "e-transfer received",
    "refund",
    "interest paid",
    "dividend",
]

CATEGORIES: list[str] = [*RULES.keys(), INCOME, UNCATEGORIZED]


def _matches(keyword: str, text: str) -> bool:
    # Whole-word match, so "metro" does not match "metropolis".
    return re.search(rf"(?<![a-z0-9]){re.escape(keyword)}(?![a-z0-9])", text) is not None


def categorize(description: str, amount: float) -> str:
    text = description.lower()
    for category, keywords in RULES.items():
        if any(_matches(k, text) for k in keywords):
            # A refund from a store is still income-side, but keeping it in the
            # store's category nets it against the original purchase.
            return category
    if amount > 0 or any(_matches(k, text) for k in INCOME_KEYWORDS):
        return INCOME
    return UNCATEGORIZED
