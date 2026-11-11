"""Parse bank CSV exports into normalized transaction rows.

Banks disagree on column names and layouts, so this module accepts the common
variants: a single signed "amount" column, or separate "debit" / "credit"
columns, with flexible header names and date formats.
"""

import hashlib
import io
from collections import Counter
from dataclasses import dataclass
from datetime import date

import pandas as pd

DATE_COLUMNS = ["date", "transaction date", "posted date", "posting date"]
DESCRIPTION_COLUMNS = ["description", "details", "memo", "payee", "merchant", "name"]
AMOUNT_COLUMNS = ["amount", "value", "transaction amount"]
DEBIT_COLUMNS = ["debit", "withdrawal", "withdrawals", "money out"]
CREDIT_COLUMNS = ["credit", "deposit", "deposits", "money in"]

MAX_ROWS = 20_000


class CSVFormatError(ValueError):
    """Raised when the file cannot be understood as a transaction export."""


@dataclass(frozen=True)
class ParsedRow:
    date: date
    description: str
    amount: float
    fingerprint: str


def _find(columns: list[str], candidates: list[str]) -> str | None:
    return next((c for c in candidates if c in columns), None)


def _to_number(series: pd.Series) -> pd.Series:
    """Convert strings like "$1,234.50" or "(45.00)" to floats."""
    cleaned = (
        series.astype(str)
        .str.strip()
        .str.replace(r"[$,\s]", "", regex=True)
        .str.replace(r"^\((.*)\)$", r"-\1", regex=True)
    )
    return pd.to_numeric(cleaned, errors="coerce")


def parse_csv(content: bytes) -> tuple[list[ParsedRow], int]:
    """Return (valid rows, number of rows skipped as invalid)."""
    try:
        df = pd.read_csv(io.BytesIO(content), dtype=str, encoding="utf-8-sig")
    except Exception as exc:  # pandas raises several unrelated error types here
        raise CSVFormatError(f"Could not read file as CSV: {exc}") from exc

    if df.empty:
        raise CSVFormatError("The CSV file has no rows.")
    if len(df) > MAX_ROWS:
        raise CSVFormatError(f"File has more than {MAX_ROWS:,} rows.")

    df.columns = [str(c).strip().lower() for c in df.columns]
    columns = list(df.columns)

    date_col = _find(columns, DATE_COLUMNS)
    desc_col = _find(columns, DESCRIPTION_COLUMNS)
    amount_col = _find(columns, AMOUNT_COLUMNS)
    debit_col = _find(columns, DEBIT_COLUMNS)
    credit_col = _find(columns, CREDIT_COLUMNS)

    if date_col is None or desc_col is None:
        raise CSVFormatError("CSV needs a date column and a description column.")
    if amount_col is None and debit_col is None and credit_col is None:
        raise CSVFormatError("CSV needs an amount column, or debit/credit columns.")

    out = pd.DataFrame()
    out["date"] = pd.to_datetime(df[date_col], errors="coerce", format="mixed").dt.date
    out["description"] = df[desc_col].fillna("").str.strip().str.slice(0, 255)
    if amount_col is not None:
        out["amount"] = _to_number(df[amount_col])
    else:
        debit = _to_number(df[debit_col]).fillna(0).abs() if debit_col else 0
        credit = _to_number(df[credit_col]).fillna(0).abs() if credit_col else 0
        out["amount"] = credit - debit
        # A row with neither a debit nor a credit value is not a transaction.
        out.loc[out["amount"] == 0, "amount"] = float("nan")

    valid = out.dropna(subset=["date", "amount"])
    valid = valid[valid["description"] != ""]
    skipped = len(out) - len(valid)

    # Two identical rows in one file are real (two coffees on the same day), so
    # the fingerprint includes how many times this exact row has been seen.
    # Re-importing the same file then produces the same fingerprints and is skipped.
    seen: Counter[tuple] = Counter()
    rows: list[ParsedRow] = []
    for d, desc, amount in valid.itertuples(index=False):
        amount = round(float(amount), 2)
        key = (d.isoformat(), desc.lower(), amount)
        seen[key] += 1
        raw = "|".join(map(str, (*key, seen[key])))
        rows.append(ParsedRow(d, desc, amount, hashlib.sha256(raw.encode()).hexdigest()))
    return rows, skipped
