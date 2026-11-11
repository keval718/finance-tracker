from datetime import date

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    email: EmailStr


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TransactionCreate(BaseModel):
    date: date
    description: str = Field(min_length=1, max_length=255)
    amount: float
    category: str | None = None


class TransactionUpdate(BaseModel):
    category: str


class TransactionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    date: date
    description: str
    amount: float
    category: str


class TransactionPage(BaseModel):
    items: list[TransactionOut]
    total: int
    page: int
    page_size: int


class ImportResult(BaseModel):
    imported: int
    skipped_duplicates: int
    skipped_invalid: int


class BudgetIn(BaseModel):
    category: str
    monthly_limit: float = Field(gt=0)


class BudgetOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    category: str
    monthly_limit: float


class CategoryTotal(BaseModel):
    category: str
    total: float


class BudgetStatus(BaseModel):
    category: str
    monthly_limit: float
    spent: float
    remaining: float
    percent_used: float


class MonthlySummary(BaseModel):
    month: str
    income: float
    expenses: float
    net: float
    savings_rate: float
    by_category: list[CategoryTotal]
    budgets: list[BudgetStatus]
    top_expenses: list[TransactionOut]


class MonthlyTrendPoint(BaseModel):
    month: str
    income: float
    expenses: float
    net: float
