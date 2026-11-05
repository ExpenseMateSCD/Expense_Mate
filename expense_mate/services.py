import os
import shutil
from datetime import datetime
from typing import Optional, List, Dict

from .models import Transaction, Budget, AlertStatus
from .database import DatabaseManager


class ExpenseService:
    EXCHANGE_RATES = {
        "PKR": 1.0,
        "USD": 0.0036,
        "EUR": 0.0033,
        "GBP": 0.0028,
        "AED": 0.0132,
        "SAR": 0.0135,
    }

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def add_transaction(self, amount: float, category: str, trans_type: str, date: str, description: str = "") -> int:
        t = Transaction(id=None, amount=amount, category=category, trans_type=trans_type, date=date, description=description)
        return self.db.insert_transaction(t)

    def list_transactions(self, trans_type: Optional[str] = None, category: Optional[str] = None) -> List[Transaction]:
        all_t = self.db.get_all_transactions()
        filtered = []
        for t in all_t:
            if trans_type and t.trans_type.lower() != trans_type.lower():
                continue
            if category and t.category.lower() != category.lower():
                continue
            filtered.append(t)
        return filtered

    def get_net_summary(self, month_year: Optional[str] = None) -> Dict[str, float]:
        transactions = self.db.get_all_transactions()
        if month_year:
            transactions = [t for t in transactions if t.date.startswith(month_year)]

        income = sum(t.amount for t in transactions if t.trans_type == "income")
        expense = sum(t.amount for t in transactions if t.trans_type == "expense")
        return {
            "total_income": income,
            "total_expense": expense,
            "net_savings": income - expense
        }

    def set_budget(self, category: str, monthly_limit: float, month_year: str) -> int:
        b = Budget(id=None, category=category, monthly_limit=monthly_limit, month_year=month_year)
        return self.db.upsert_budget(b)

    def check_budget_status(self, category: str, month_year: str) -> Optional[AlertStatus]:
        budget = self.db.get_budget(category, month_year)
        if not budget:
            return None

        transactions = self.db.get_all_transactions()
        spent = sum(
            t.amount for t in transactions
            if t.category.lower() == category.lower()
            and t.trans_type == "expense"
            and t.date.startswith(month_year)
        )

        percentage = (spent / budget.monthly_limit) * 100.0

        if percentage >= 100.0:
            level = "CRITICAL"
            msg = f"CRITICAL: Budget limit exceeded for {category}! Spent {spent:.2f} of {budget.monthly_limit:.2f} ({percentage:.1f}%)."
        elif percentage >= 80.0:
            level = "WARNING"
            msg = f"WARNING: Approaching budget limit for {category}! Spent {spent:.2f} of {budget.monthly_limit:.2f} ({percentage:.1f}%)."
        else:
            level = "NORMAL"
            msg = f"Healthy: Spent {spent:.2f} of {budget.monthly_limit:.2f} ({percentage:.1f}%)."

        return AlertStatus(
            category=category,
            spent=spent,
            limit=budget.monthly_limit,
            percentage=percentage,
            level=level,
            message=msg
        )

    def get_all_budget_statuses(self, month_year: str) -> List[AlertStatus]:
        budgets = self.db.get_budgets_for_month(month_year)
        statuses = []

        for b in budgets:
            st = self.check_budget_status(b.category, month_year)
            if st:
                statuses.append(st)

        return statuses

    def convert_amount(self, amount: float, from_curr: str, to_curr: str) -> float:
        from_curr, to_curr = from_curr.upper(), to_curr.upper()

        if from_curr not in self.EXCHANGE_RATES or to_curr not in self.EXCHANGE_RATES:
            raise ValueError(f"Supported currencies: {list(self.EXCHANGE_RATES.keys())}")

        amount_in_base = amount / self.EXCHANGE_RATES[from_curr]

        return round(
            amount_in_base * self.EXCHANGE_RATES[to_curr],
            2
        )

    def create_database_backup(self, backup_dir: str = "backups") -> str:
        try:
            if not os.path.exists(backup_dir):
                os.makedirs(backup_dir)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = os.path.join(
                backup_dir,
                f"expense_mate_backup_{timestamp}.db"
            )

            shutil.copyfile(self.db.db_path, backup_path)

            return backup_path

        except (OSError, shutil.Error) as exc:
            raise RuntimeError(
                f"Unable to create database backup: {exc}"
            ) from exc