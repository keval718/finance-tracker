import pytest

from app.importer import CSVFormatError, parse_csv


def test_signed_amount_column():
    rows, skipped = parse_csv(
        b"Date,Description,Amount\n2026-03-01,Coffee,-4.50\n2026-03-02,Pay,1000\n"
    )
    assert skipped == 0
    assert [(r.date.isoformat(), r.description, r.amount) for r in rows] == [
        ("2026-03-01", "Coffee", -4.5),
        ("2026-03-02", "Pay", 1000.0),
    ]


def test_debit_credit_columns_and_alternate_headers():
    csv = (
        b"Transaction Date,Details,Debit,Credit\n03/01/2026,Coffee,4.50,\n03/02/2026,Pay,,1000.00\n"
    )
    rows, _ = parse_csv(csv)
    assert [r.amount for r in rows] == [-4.5, 1000.0]
    assert rows[0].date.isoformat() == "2026-03-01"


def test_currency_formatting_is_cleaned():
    rows, _ = parse_csv(
        b'Date,Description,Amount\n2026-03-01,TV,"$1,234.50"\n2026-03-02,Fee,(45.00)\n'
    )
    assert [r.amount for r in rows] == [1234.5, -45.0]


def test_invalid_rows_are_counted_and_skipped():
    csv = b"Date,Description,Amount\nnot-a-date,Coffee,-4.50\n2026-03-02,,5\n2026-03-03,Ok,abc\n2026-03-04,Good,-1\n"
    rows, skipped = parse_csv(csv)
    assert len(rows) == 1
    assert skipped == 3


def test_identical_rows_get_distinct_fingerprints():
    rows, _ = parse_csv(
        b"Date,Description,Amount\n2026-03-01,Coffee,-4.50\n2026-03-01,Coffee,-4.50\n"
    )
    assert len({r.fingerprint for r in rows}) == 2


@pytest.mark.parametrize(
    "content",
    [
        b"",
        b"Date,Description\n2026-03-01,Coffee\n",
        b"Foo,Bar\n1,2\n",
        b"Date,Description,Amount\n",
    ],
)
def test_unusable_files_raise(content):
    with pytest.raises(CSVFormatError):
        parse_csv(content)
