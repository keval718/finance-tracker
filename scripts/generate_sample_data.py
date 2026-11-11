"""Generate a realistic six-month bank export for demos. Deterministic (fixed seed).

Usage: python scripts/generate_sample_data.py > sample_data/sample_transactions.csv
"""

import csv
import random
import sys
from datetime import date, timedelta

random.seed(42)

START, END = date(2026, 6, 1), date(2026, 11, 10)

# (description, low, high, chance per day)
VARIABLE = [
    ("LOBLAWS #1042", 45, 140, 0.16),
    ("NO FRILLS TORONTO", 25, 90, 0.10),
    ("COSTCO WHOLESALE", 120, 260, 0.04),
    ("TIM HORTONS #3321", 3, 12, 0.35),
    ("STARBUCKS COFFEE", 5, 14, 0.15),
    ("UBER EATS", 22, 55, 0.10),
    ("SUSHI ON BLOOR RESTAURANT", 30, 85, 0.05),
    ("PRESTO FARE LOAD", 20, 50, 0.08),
    ("UBER TRIP", 12, 38, 0.07),
    ("SHELL GAS STATION", 45, 80, 0.05),
    ("AMAZON.CA ORDER", 15, 130, 0.09),
    ("SHOPPERS DRUG MART", 8, 45, 0.06),
    ("CINEPLEX ODEON", 16, 42, 0.03),
    ("CANADIAN TIRE", 20, 110, 0.03),
    ("LCBO #217", 18, 60, 0.05),
]

# (day of month, description, amount)
FIXED = [
    (1, "RENT PAYMENT - 88 HARBOUR ST", -1850.00),
    (3, "ROGERS INTERNET", -79.99),
    (5, "TORONTO HYDRO", None),
    (8, "NETFLIX.COM", -20.99),
    (8, "SPOTIFY PREMIUM", -11.99),
    (12, "GOODLIFE FITNESS GYM", -54.99),
    (15, "PAYROLL DEPOSIT - ACME CORP", 2650.00),
    (20, "FIDO MOBILE", -55.00),
    (28, "MONTHLY SERVICE FEE", -4.95),
    (30, "PAYROLL DEPOSIT - ACME CORP", 2650.00),
]

rows = []
day = START
while day <= END:
    for dom, desc, amount in FIXED:
        if day.day == dom or (dom == 30 and day.month == 2 and day.day == 28):
            if amount is None:
                amount = -round(random.uniform(60, 115), 2)
            rows.append((day, desc, amount))
    for desc, low, high, chance in VARIABLE:
        if random.random() < chance:
            rows.append((day, desc, -round(random.uniform(low, high), 2)))
    day += timedelta(days=1)

rows += [
    (date(2026, 7, 18), "AIR CANADA", -412.60),
    (date(2026, 7, 19), "AIRBNB * MONTREAL", -388.00),
    (date(2026, 8, 22), "BEST BUY #954", -329.99),
    (date(2026, 8, 29), "BEST BUY #954", 329.99),  # return
    (date(2026, 9, 9), "DENTAL CLINIC - DR PATEL", -180.00),
    (date(2026, 10, 14), "TICKETMASTER CONCERT", -156.50),
    (date(2026, 10, 2), "E-TRANSFER RECEIVED - SAM", 120.00),
]
rows.sort(key=lambda r: r[0])

writer = csv.writer(sys.stdout, lineterminator="\n")
writer.writerow(["Date", "Description", "Amount"])
for d, desc, amount in rows:
    writer.writerow([d.isoformat(), desc, f"{amount:.2f}"])
