from datetime import date

import pandas as pd
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..categorizer import INCOME
from ..database import get_db
from ..models import Budget, Transaction, User
from ..schemas import BudgetStatus, CategoryTotal, MonthlySummary, MonthlyTrendPoint
from ..security import get_current_user
from .transactions import month_bounds

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("/months", response_model=list[str])
def available_months(
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> list[str]:
    """Months that have at least one transaction, newest first."""
    dates = db.scalars(select(Transaction.date).where(Transaction.user_id == user.id)).all()
    return sorted({d.strftime("%Y-%m") for d in dates}, reverse=True)


@router.get("/summary", response_model=MonthlySummary)
def monthly_summary(
    month: str | None = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MonthlySummary:
    month = month or date.today().strftime("%Y-%m")
    start, end = month_bounds(month)
    txs = db.scalars(
        select(Transaction).where(
            Transaction.user_id == user.id, Transaction.date >= start, Transaction.date < end
        )
    ).all()

    income = sum(t.amount for t in txs if t.category == INCOME)
    # Spending per category is netted, so a refund reduces that category's total.
    spending: dict[str, float] = {}
    for t in txs:
        if t.category != INCOME:
            spending[t.category] = spending.get(t.category, 0.0) - t.amount
    spending = {c: round(v, 2) for c, v in spending.items() if v > 0}
    expenses = sum(spending.values())

    budgets = db.scalars(
        select(Budget).where(Budget.user_id == user.id).order_by(Budget.category)
    ).all()
    budget_status = [
        BudgetStatus(
            category=b.category,
            monthly_limit=b.monthly_limit,
            spent=spending.get(b.category, 0.0),
            remaining=round(b.monthly_limit - spending.get(b.category, 0.0), 2),
            percent_used=round(spending.get(b.category, 0.0) / b.monthly_limit * 100, 1),
        )
        for b in budgets
    ]

    top = sorted((t for t in txs if t.amount < 0 and t.category != INCOME), key=lambda t: t.amount)

    return MonthlySummary(
        month=month,
        income=round(income, 2),
        expenses=round(expenses, 2),
        net=round(income - expenses, 2),
        savings_rate=round((income - expenses) / income * 100, 1) if income > 0 else 0.0,
        by_category=[
            CategoryTotal(category=c, total=v)
            for c, v in sorted(spending.items(), key=lambda kv: kv[1], reverse=True)
        ],
        budgets=budget_status,
        top_expenses=top[:5],
    )


@router.get("/trend", response_model=list[MonthlyTrendPoint])
def monthly_trend(
    months: int = Query(6, ge=1, le=24),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[MonthlyTrendPoint]:
    """Income and expenses for the most recent N months that have data."""
    rows = db.execute(
        select(Transaction.date, Transaction.amount, Transaction.category).where(
            Transaction.user_id == user.id
        )
    ).all()
    if not rows:
        return []

    df = pd.DataFrame(rows, columns=["date", "amount", "category"])
    df["month"] = pd.to_datetime(df["date"]).dt.to_period("M")
    is_income = df["category"] == INCOME
    df["income"] = df["amount"].where(is_income, 0.0)
    df["expenses"] = (-df["amount"]).where(~is_income, 0.0)

    monthly = df.groupby("month")[["income", "expenses"]].sum()
    # Fill months with no activity so the chart has no gaps.
    monthly = monthly.reindex(
        pd.period_range(monthly.index.min(), monthly.index.max(), freq="M"), fill_value=0.0
    ).tail(months)

    return [
        MonthlyTrendPoint(
            month=str(period),
            income=round(row.income, 2),
            expenses=round(row.expenses, 2),
            net=round(row.income - row.expenses, 2),
        )
        for period, row in monthly.iterrows()
    ]
