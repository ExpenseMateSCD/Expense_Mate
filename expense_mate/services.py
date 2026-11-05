import os
import shutil
from datetime import datetime
from typing import Dict, List, Optional, Union

from .database import DatabaseManager
from .models import AlertStatus, Budget, Transaction
from .repositories import BudgetRepository, TransactionRepository


class TransactionService:
    """Business logic for transaction management and financial summaries."""

    def __init__(
        self,
        repository: Union[TransactionRepository, DatabaseManager],
    ):
        if isinstance(repository, DatabaseManager):
            self.repository = TransactionRepository(repository)
        else:
            self.repository = repository

    def add_transaction(
        self,
        amount: float,
        category: str,
        trans_type: str,
        date: str,
        description: str = "",
    ) -> int:
        transaction = Transaction(
            id=None,
            amount=amount,
            category=category,
            trans_type=trans_type,
            date=date,
            description=description,
        )
        return self.repository.add(transaction)

    def list_transactions(
        self,
        trans_type: Optional[str] = None,
        category: Optional[str] = None,
    ) -> List[Transaction]:
        return self.repository.get_by_filter(
            trans_type=trans_type,
            category=category,
        )

    def get_net_summary(
        self,
        month_year: Optional[str] = None,
    ) -> Dict[str, float]:
        if month_year:
            transactions = self.repository.get_by_month(month_year)
        else:
            transactions = self.repository.get_all()

        income = sum(t.amount for t in transactions if t.trans_type == "income")
        expense = sum(t.amount for t in transactions if t.trans_type == "expense")
        return {
            "total_income": income,
            "total_expense": expense,
            "net_savings": income - expense,
        }


class BudgetService:
    """Business logic for budgets, calculations, and threshold alerts."""

    def __init__(
        self,
        budget_repo: Union[BudgetRepository, DatabaseManager],
        transaction_repo: Optional[Union[TransactionRepository, DatabaseManager]] = None,
    ):
        if isinstance(budget_repo, DatabaseManager):
            self.budget_repo = BudgetRepository(budget_repo)
            self.transaction_repo = (
                TransactionRepository(budget_repo)
                if transaction_repo is None
                else (
                    TransactionRepository(transaction_repo)
                    if isinstance(transaction_repo, DatabaseManager)
                    else transaction_repo
                )
            )
        else:
            self.budget_repo = budget_repo
            if transaction_repo is None:
                raise ValueError("transaction_repo is required when budget_repo is a repository.")
            self.transaction_repo = (
                TransactionRepository(transaction_repo)
                if isinstance(transaction_repo, DatabaseManager)
                else transaction_repo
            )

    def set_budget(
        self,
        category: str,
        monthly_limit: float,
        month_year: str,
    ) -> int:
        budget = Budget(
            id=None,
            category=category,
            monthly_limit=monthly_limit,
            month_year=month_year,
        )
        return self.budget_repo.save(budget)

    def check_budget_status(
        self,
        category: str,
        month_year: str,
    ) -> Optional[AlertStatus]:
        budget = self.budget_repo.get(category, month_year)
        if not budget:
            return None

        month_transactions = self.transaction_repo.get_by_month(month_year)
        spent = sum(
            t.amount
            for t in month_transactions
            if t.category.lower() == category.lower() and t.trans_type == "expense"
        )

        percentage = round((spent / budget.monthly_limit) * 100.0, 2) if budget.monthly_limit > 0 else 0.0

        if percentage >= 100.0:
            level = "CRITICAL"
            msg = (
                f"CRITICAL: Budget limit exceeded for {category}! "
                f"Spent {spent:.2f} of {budget.monthly_limit:.2f} ({percentage:.1f}%)."
            )
        elif percentage >= 80.0:
            level = "WARNING"
            msg = (
                f"WARNING: Approaching budget limit for {category}! "
                f"Spent {spent:.2f} of {budget.monthly_limit:.2f} ({percentage:.1f}%)."
            )
        else:
            level = "NORMAL"
            msg = f"Healthy: Spent {spent:.2f} of {budget.monthly_limit:.2f} ({percentage:.1f}%)."

        return AlertStatus(
            category=category,
            spent=spent,
            limit=budget.monthly_limit,
            percentage=percentage,
            level=level,
            message=msg,
        )

    def get_all_budget_statuses(self, month_year: str) -> List[AlertStatus]:
        budgets = self.budget_repo.get_for_month(month_year)
        statuses: List[AlertStatus] = []

        for b in budgets:
            st = self.check_budget_status(b.category, month_year)
            if st:
                statuses.append(st)

        return statuses


class CurrencyService:
    """Business logic for multi-currency conversions."""

    EXCHANGE_RATES = {
        "PKR": 1.0,
        "USD": 0.0036,
        "EUR": 0.0033,
        "GBP": 0.0028,
        "AED": 0.0132,
        "SAR": 0.0135,
    }

    def __init__(self, custom_rates: Optional[Dict[str, float]] = None):
        self.rates = custom_rates or self.EXCHANGE_RATES

    def convert_amount(
        self,
        amount: float,
        from_curr: str,
        to_curr: str,
    ) -> float:
        from_curr, to_curr = from_curr.upper(), to_curr.upper()

        if from_curr not in self.rates or to_curr not in self.rates:
            raise ValueError(f"Supported currencies: {list(self.rates.keys())}")

        amount_in_base = amount / self.rates[from_curr]
        return round(amount_in_base * self.rates[to_curr], 2)


class BackupService:
    """Manages database file backup and timestamping."""

    def __init__(self, db_path: str = "expense_mate.db"):
        self.db_path = db_path

    def create_database_backup(
        self,
        backup_dir: str = "backups",
        db_path: Optional[str] = None,
    ) -> str:
        target_db = db_path or self.db_path
        try:
            if not os.path.exists(backup_dir):
                os.makedirs(backup_dir)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = os.path.join(
                backup_dir,
                f"expense_mate_backup_{timestamp}.db",
            )

            shutil.copyfile(target_db, backup_path)
            return backup_path

        except (OSError, shutil.Error) as exc:
            raise RuntimeError(
                f"Unable to create database backup: {exc}"
            ) from exc


class ExpenseService:
    """Backward-compatible composite service delegating to specialized services."""

    EXCHANGE_RATES = CurrencyService.EXCHANGE_RATES

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.transaction_repo = TransactionRepository(db_manager)
        self.budget_repo = BudgetRepository(db_manager)

        self.transaction_service = TransactionService(self.transaction_repo)
        self.budget_service = BudgetService(self.budget_repo, self.transaction_repo)
        self.currency_service = CurrencyService()
        self.backup_service = BackupService(db_manager.db_path)

    def add_transaction(
        self,
        amount: float,
        category: str,
        trans_type: str,
        date: str,
        description: str = "",
    ) -> int:
        return self.transaction_service.add_transaction(
            amount, category, trans_type, date, description
        )

    def list_transactions(
        self,
        trans_type: Optional[str] = None,
        category: Optional[str] = None,
    ) -> List[Transaction]:
        return self.transaction_service.list_transactions(trans_type, category)

    def get_net_summary(
        self,
        month_year: Optional[str] = None,
    ) -> Dict[str, float]:
        return self.transaction_service.get_net_summary(month_year)

    def set_budget(
        self,
        category: str,
        monthly_limit: float,
        month_year: str,
    ) -> int:
        return self.budget_service.set_budget(category, monthly_limit, month_year)

    def check_budget_status(
        self,
        category: str,
        month_year: str,
    ) -> Optional[AlertStatus]:
        return self.budget_service.check_budget_status(category, month_year)

    def get_all_budget_statuses(self, month_year: str) -> List[AlertStatus]:
        return self.budget_service.get_all_budget_statuses(month_year)

    def convert_amount(
        self,
        amount: float,
        from_curr: str,
        to_curr: str,
    ) -> float:
        return self.currency_service.convert_amount(amount, from_curr, to_curr)

    def create_database_backup(self, backup_dir: str = "backups") -> str:
        return self.backup_service.create_database_backup(
            backup_dir, self.db.db_path
        )
