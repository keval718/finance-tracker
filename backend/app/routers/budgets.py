from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..categorizer import CATEGORIES, INCOME
from ..database import get_db
from ..models import Budget, User
from ..schemas import BudgetIn, BudgetOut
from ..security import get_current_user

router = APIRouter(prefix="/api/budgets", tags=["budgets"])


@router.get("", response_model=list[BudgetOut])
def list_budgets(
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> list[Budget]:
    return list(
        db.scalars(select(Budget).where(Budget.user_id == user.id).order_by(Budget.category)).all()
    )


@router.put("", response_model=BudgetOut)
def upsert_budget(
    payload: BudgetIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Budget:
    """Create the budget for a category, or update it if one already exists."""
    if payload.category not in CATEGORIES or payload.category == INCOME:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Not a spending category")
    budget = db.scalar(
        select(Budget).where(Budget.user_id == user.id, Budget.category == payload.category)
    )
    if budget is None:
        budget = Budget(user_id=user.id, category=payload.category)
        db.add(budget)
    budget.monthly_limit = round(payload.monthly_limit, 2)
    db.commit()
    return budget


@router.delete("/{budget_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_budget(
    budget_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    budget = db.get(Budget, budget_id)
    if budget is None or budget.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Budget not found")
    db.delete(budget)
    db.commit()
