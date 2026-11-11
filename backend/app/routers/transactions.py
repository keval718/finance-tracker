import hashlib
import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..categorizer import CATEGORIES, categorize
from ..database import get_db
from ..importer import CSVFormatError, parse_csv
from ..models import Transaction, User
from ..schemas import (
    ImportResult,
    TransactionCreate,
    TransactionOut,
    TransactionPage,
    TransactionUpdate,
)
from ..security import get_current_user

router = APIRouter(prefix="/api/transactions", tags=["transactions"])

MAX_UPLOAD_BYTES = 5 * 1024 * 1024


def month_bounds(month: str) -> tuple[date, date]:
    """Turn "2026-03" into (first day of that month, first day of the next)."""
    try:
        year, mon = (int(part) for part in month.split("-"))
        start = date(year, mon, 1)
    except ValueError:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "month must be YYYY-MM") from None
    end = date(year + 1, 1, 1) if mon == 12 else date(year, mon + 1, 1)
    return start, end


def _validate_category(category: str) -> str:
    if category not in CATEGORIES:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, f"Unknown category: {category}")
    return category


@router.get("/categories", response_model=list[str])
def list_categories() -> list[str]:
    return CATEGORIES


@router.get("", response_model=TransactionPage)
def list_transactions(
    month: str | None = None,
    category: str | None = None,
    search: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TransactionPage:
    query = select(Transaction).where(Transaction.user_id == user.id)
    if month:
        start, end = month_bounds(month)
        query = query.where(Transaction.date >= start, Transaction.date < end)
    if category:
        query = query.where(Transaction.category == category)
    if search:
        query = query.where(Transaction.description.ilike(f"%{search}%"))

    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    items = db.scalars(
        query.order_by(Transaction.date.desc(), Transaction.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    return TransactionPage(items=items, total=total, page=page, page_size=page_size)


@router.post("", response_model=TransactionOut, status_code=status.HTTP_201_CREATED)
def create_transaction(
    payload: TransactionCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Transaction:
    category = (
        _validate_category(payload.category)
        if payload.category
        else categorize(payload.description, payload.amount)
    )
    tx = Transaction(
        user_id=user.id,
        date=payload.date,
        description=payload.description.strip(),
        amount=round(payload.amount, 2),
        category=category,
        # Manual entries are never deduplicated, so they get a random fingerprint.
        fingerprint=hashlib.sha256(uuid.uuid4().bytes).hexdigest(),
    )
    db.add(tx)
    db.commit()
    return tx


@router.post("/import", response_model=ImportResult)
async def import_csv(
    file: UploadFile,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ImportResult:
    content = await file.read(MAX_UPLOAD_BYTES + 1)
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, "File is larger than 5 MB")
    try:
        rows, skipped_invalid = parse_csv(content)
    except CSVFormatError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc

    existing = set(
        db.scalars(select(Transaction.fingerprint).where(Transaction.user_id == user.id)).all()
    )
    new = [
        Transaction(
            user_id=user.id,
            date=row.date,
            description=row.description,
            amount=row.amount,
            category=categorize(row.description, row.amount),
            fingerprint=row.fingerprint,
        )
        for row in rows
        if row.fingerprint not in existing
    ]
    db.add_all(new)
    db.commit()
    return ImportResult(
        imported=len(new),
        skipped_duplicates=len(rows) - len(new),
        skipped_invalid=skipped_invalid,
    )


def _get_owned(tx_id: int, user: User, db: Session) -> Transaction:
    tx = db.get(Transaction, tx_id)
    # Same response for "does not exist" and "belongs to someone else".
    if tx is None or tx.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Transaction not found")
    return tx


@router.patch("/{tx_id}", response_model=TransactionOut)
def update_category(
    tx_id: int,
    payload: TransactionUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Transaction:
    tx = _get_owned(tx_id, user, db)
    tx.category = _validate_category(payload.category)
    db.commit()
    return tx


@router.delete("/{tx_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_transaction(
    tx_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    db.delete(_get_owned(tx_id, user, db))
    db.commit()
