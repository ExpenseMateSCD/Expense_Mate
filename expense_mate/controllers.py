from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from .analytics import AnalyticsService, ChartFormatter
from .database import DatabaseManager
from .importer_exporter import DataPortabilityManager
from .models import AlertStatus, Transaction
from .repositories import BudgetRepository, TransactionRepository
from .services import BackupService, BudgetService, CurrencyService, TransactionService


class ExpenseMateController:
    """Controller layer mediating between the UI/Presentation and Services.

    Receives user requests/actions, validates basic inputs, calls services,
    and returns structured results following Controller -> Services -> Repository.
    """

    def __init__(
        self,
        db_path: str = "expense_mate.db",
        transaction_service: Optional[TransactionService] = None,
        budget_service: Optional[BudgetService] = None,
        analytics_service: Optional[AnalyticsService] = None,
        chart_formatter: Optional[ChartFormatter] = None,
        currency_service: Optional[CurrencyService] = None,
        backup_service: Optional[BackupService] = None,
        portability_manager: Optional[DataPortabilityManager] = None,
    ):
        if (
            transaction_service is None
            or budget_service is None
            or analytics_service is None
            or portability_manager is None
        ):
            db = DatabaseManager(db_path)
            trans_repo = TransactionRepository(db)
            budget_repo = BudgetRepository(db)

            self.transaction_service = transaction_service or TransactionService(trans_repo)
            self.budget_service = budget_service or BudgetService(budget_repo, trans_repo)
            self.analytics_service = analytics_service or AnalyticsService(trans_repo)
            self.chart_formatter = chart_formatter or ChartFormatter()
            self.currency_service = currency_service or CurrencyService()
            self.backup_service = backup_service or BackupService(db_path)
            self.portability_manager = portability_manager or DataPortabilityManager(trans_repo)
        else:
            self.transaction_service = transaction_service
            self.budget_service = budget_service
            self.analytics_service = analytics_service
            self.chart_formatter = chart_formatter or ChartFormatter()
            self.currency_service = currency_service or CurrencyService()
            self.backup_service = backup_service or BackupService(db_path)
            self.portability_manager = portability_manager

    # ---------------- Validation Helpers ---------------- #

    def validate_transaction_data(
        self,
        trans_type: str,
        amount_text: Any,
        category: str,
        date_str: str,
    ) -> float:
        errors = []
        normalized_type = str(trans_type).strip().lower()

        if normalized_type not in ("income", "expense"):
            errors.append("Transaction type must be 'income' or 'expense'.")

        try:
            amount = float(amount_text)
            if amount <= 0:
                errors.append("Amount must be strictly positive.")
        except (TypeError, ValueError):
            errors.append("Amount must be a valid number.")
            amount = 0.0

        if not category or not str(category).strip():
            errors.append("Category cannot be empty.")

        try:
            parsed_date = datetime.strptime(str(date_str).strip(), "%Y-%m-%d")
            if parsed_date.strftime("%Y-%m-%d") != str(date_str).strip():
                raise ValueError
        except ValueError:
            errors.append("Date must follow format YYYY-MM-DD.")

        if errors:
            raise ValueError("; ".join(errors))

        return amount

    def validate_currency_data(
        self,
        amount_text: Any,
        from_curr: str,
        to_curr: str,
    ) -> float:
        errors = []
        try:
            amount = float(amount_text)
            if amount < 0:
                errors.append("Amount cannot be negative.")
        except (TypeError, ValueError):
            errors.append("Amount must be a valid number.")
            amount = 0.0

        if not from_curr or not str(from_curr).strip():
            errors.append("From currency cannot be empty.")

        if not to_curr or not str(to_curr).strip():
            errors.append("To currency cannot be empty.")

        if errors:
            raise ValueError("; ".join(errors))

        return amount

    def validate_month_format(self, month_year: str) -> str:
        cleaned = str(month_year).strip()
        try:
            parsed = datetime.strptime(cleaned, "%Y-%m")
            if parsed.strftime("%Y-%m") != cleaned:
                raise ValueError
        except ValueError:
            raise ValueError("Invalid month format. Please use YYYY-MM.")
        return cleaned

    # ---------------- Application Actions ---------------- #

    def add_transaction(
        self,
        amount: float,
        category: str,
        trans_type: str,
        date: str,
        description: str = "",
    ) -> Dict[str, Any]:
        """Feature 1: Add Transaction with automatic budget alert evaluation."""
        valid_amount = self.validate_transaction_data(
            trans_type=trans_type,
            amount_text=amount,
            category=category,
            date_str=date,
        )

        tid = self.transaction_service.add_transaction(
            amount=valid_amount,
            category=category.strip(),
            trans_type=trans_type.strip().lower(),
            date=date.strip(),
            description=description.strip(),
        )

        alert: Optional[AlertStatus] = None
        if trans_type.strip().lower() == "expense":
            month_year = date.strip()[:7]
            alert = self.budget_service.check_budget_status(
                category=category.strip(),
                month_year=month_year,
            )

        return {
            "transaction_id": tid,
            "alert": alert,
        }

    def list_transactions(
        self,
        trans_type: Optional[str] = None,
        category: Optional[str] = None,
    ) -> List[Transaction]:
        return self.transaction_service.list_transactions(
            trans_type=trans_type,
            category=category,
        )

    def get_financial_summary(
        self,
        month_year: Optional[str] = None,
    ) -> Dict[str, float]:
        if month_year:
            self.validate_month_format(month_year)
        return self.transaction_service.get_net_summary(month_year)

    def set_budget(
        self,
        category: str,
        monthly_limit: float,
        month_year: str,
    ) -> int:
        """Set or update monthly budget for a category."""
        if not category or not category.strip():
            raise ValueError("Category cannot be empty.")
        if monthly_limit <= 0:
            raise ValueError("Budget limit must be a positive number.")
        valid_month = self.validate_month_format(month_year)

        return self.budget_service.set_budget(
            category=category.strip(),
            monthly_limit=monthly_limit,
            month_year=valid_month,
        )

    def get_budget_statuses(
        self,
        month_year: str,
    ) -> List[AlertStatus]:
        """Feature 2: Monthly Budget Summary and Alerts."""
        valid_month = self.validate_month_format(month_year)
        return self.budget_service.get_all_budget_statuses(valid_month)

    def get_category_analytics(
        self,
        trans_type: str = "expense",
        month_year: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Category breakdown computation and ASCII chart generation."""
        if month_year:
            self.validate_month_format(month_year)

        breakdown = self.analytics_service.get_category_breakdown(
            trans_type=trans_type,
            month_year=month_year,
        )
        chart = self.chart_formatter.generate_ascii_bar_chart(
            data=breakdown,
            title=f"{trans_type.capitalize()} Category Breakdown",
        )
        return {
            "breakdown": breakdown,
            "chart": chart,
        }

    def get_monthly_trends(self) -> Dict[str, Dict[str, float]]:
        return self.analytics_service.get_monthly_trends()

    def convert_currency(
        self,
        amount: float,
        from_curr: str,
        to_curr: str,
    ) -> float:
        valid_amt = self.validate_currency_data(amount, from_curr, to_curr)
        return self.currency_service.convert_amount(
            amount=valid_amt,
            from_curr=from_curr,
            to_curr=to_curr,
        )

    def export_csv(
        self,
        file_path: str = "expenses_export.csv",
    ) -> int:
        if not file_path or not file_path.strip():
            raise ValueError("CSV path cannot be empty.")
        return self.portability_manager.export_to_csv(file_path.strip())

    def import_csv(
        self,
        file_path: str,
    ) -> Tuple[int, int, List[str]]:
        if not file_path or not file_path.strip():
            raise ValueError("CSV path cannot be empty.")
        return self.portability_manager.import_from_csv(file_path.strip())

    def backup_database(
        self,
        backup_dir: str = "backups",
    ) -> str:
        return self.backup_service.create_database_backup(backup_dir=backup_dir)
