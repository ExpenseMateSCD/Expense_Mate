from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Transaction:
    id: Optional[int]
    amount: float
    category: str
    trans_type: str
    date: str
    description: str = ""

    def validate(self) -> None:
        if self.amount <= 0:
            raise ValueError("Amount must be strictly positive.")
        if self.trans_type not in ("income", "expense"):
            raise ValueError("Transaction type must be 'income' or 'expense'.")
        if not self.category or not self.category.strip():
            raise ValueError("Category cannot be empty.")
        try:
            datetime.strptime(self.date, "%Y-%m-%d")
        except ValueError:
            raise ValueError("Date must follow format YYYY-MM-DD.")


@dataclass
class Budget:
    id: Optional[int]
    category: str
    monthly_limit: float
    month_year: str

    def validate(self) -> None:
        if self.monthly_limit <= 0:
            raise ValueError("Budget monthly limit must be strictly positive.")
        if not self.category or not self.category.strip():
            raise ValueError("Category cannot be empty.")
        try:
            datetime.strptime(self.month_year, "%Y-%m")
        except ValueError:
            raise ValueError("Month-Year must follow format YYYY-MM.")


@dataclass
class AlertStatus:
    category: str
    spent: float
    limit: float
    percentage: float
    level: str
    message: str