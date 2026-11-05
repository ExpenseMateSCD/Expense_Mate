"""Unit test suite for rewritten Service classes in ExpenseMate."""

import os
import tempfile
import unittest

from expense_mate.analytics import AnalyticsService, ChartFormatter
from expense_mate.database import DatabaseManager
from expense_mate.models import Budget, Transaction
from expense_mate.repositories import BudgetRepository, TransactionRepository
from expense_mate.services import (
    BackupService,
    BudgetService,
    CurrencyService,
    TransactionService,
)


class TestServices(unittest.TestCase):
    def setUp(self):
        self.db_fd, self.db_path = tempfile.mkstemp(suffix=".db")
        self.db = DatabaseManager(self.db_path)
        self.trans_repo = TransactionRepository(self.db)
        self.budget_repo = BudgetRepository(self.db)

        self.trans_service = TransactionService(self.trans_repo)
        self.budget_service = BudgetService(self.budget_repo, self.trans_repo)
        self.currency_service = CurrencyService()
        self.backup_service = BackupService(self.db_path)
        self.analytics_service = AnalyticsService(self.trans_repo)

    def tearDown(self):
        os.close(self.db_fd)
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    # ---------------- TransactionService Tests ---------------- #

    def test_transaction_service_add_and_list(self):
        tid1 = self.trans_service.add_transaction(
            amount=5000.0,
            category="Salary",
            trans_type="income",
            date="2026-10-01",
            description="October salary",
        )
        tid2 = self.trans_service.add_transaction(
            amount=150.0,
            category="Food",
            trans_type="expense",
            date="2026-10-02",
            description="Lunch",
        )

        self.assertGreater(tid1, 0)
        self.assertGreater(tid2, 0)

        all_tx = self.trans_service.list_transactions()
        self.assertEqual(len(all_tx), 2)

        income_tx = self.trans_service.list_transactions(trans_type="income")
        self.assertEqual(len(income_tx), 1)
        self.assertEqual(income_tx[0].category, "Salary")

        food_tx = self.trans_service.list_transactions(category="Food")
        self.assertEqual(len(food_tx), 1)
        self.assertEqual(food_tx[0].amount, 150.0)

    def test_transaction_service_net_summary(self):
        self.trans_service.add_transaction(10000.0, "Salary", "income", "2026-10-01")
        self.trans_service.add_transaction(2000.0, "Rent", "expense", "2026-10-02")
        self.trans_service.add_transaction(1000.0, "Groceries", "expense", "2026-10-05")

        summary = self.trans_service.get_net_summary("2026-10")
        self.assertEqual(summary["total_income"], 10000.0)
        self.assertEqual(summary["total_expense"], 3000.0)
        self.assertEqual(summary["net_savings"], 7000.0)

    # ---------------- BudgetService Tests ---------------- #

    def test_budget_service_threshold_levels(self):
        self.budget_service.set_budget("Shopping", 1000.0, "2026-10")

        # 50% spending -> NORMAL
        self.trans_service.add_transaction(500.0, "Shopping", "expense", "2026-10-02")
        status_normal = self.budget_service.check_budget_status("Shopping", "2026-10")
        self.assertIsNotNone(status_normal)
        self.assertEqual(status_normal.level, "NORMAL")
        self.assertEqual(status_normal.percentage, 50.0)

        # 85% spending -> WARNING
        self.trans_service.add_transaction(350.0, "Shopping", "expense", "2026-10-05")
        status_warning = self.budget_service.check_budget_status("Shopping", "2026-10")
        self.assertEqual(status_warning.level, "WARNING")
        self.assertEqual(status_warning.percentage, 85.0)

        # 110% spending -> CRITICAL
        self.trans_service.add_transaction(250.0, "Shopping", "expense", "2026-10-10")
        status_critical = self.budget_service.check_budget_status("Shopping", "2026-10")
        self.assertEqual(status_critical.level, "CRITICAL")
        self.assertAlmostEqual(status_critical.percentage, 110.0, places=2)

    def test_budget_service_get_all_statuses(self):
        self.budget_service.set_budget("Food", 2000.0, "2026-10")
        self.budget_service.set_budget("Travel", 1500.0, "2026-10")

        self.trans_service.add_transaction(1000.0, "Food", "expense", "2026-10-03")
        self.trans_service.add_transaction(1500.0, "Travel", "expense", "2026-10-04")

        statuses = self.budget_service.get_all_budget_statuses("2026-10")
        self.assertEqual(len(statuses), 2)
        categories = {s.category for s in statuses}
        self.assertEqual(categories, {"Food", "Travel"})

    # ---------------- CurrencyService Tests ---------------- #

    def test_currency_service_conversions(self):
        usd_to_pkr = self.currency_service.convert_amount(100.0, "USD", "PKR")
        self.assertAlmostEqual(usd_to_pkr, 27777.78, delta=1.0)

        pkr_to_eur = self.currency_service.convert_amount(10000.0, "PKR", "EUR")
        self.assertEqual(pkr_to_eur, 33.0)

        with self.assertRaises(ValueError):
            self.currency_service.convert_amount(100.0, "XYZ", "PKR")

    # ---------------- BackupService Tests ---------------- #

    def test_backup_service_creates_file(self):
        temp_backup_dir = tempfile.mkdtemp()
        try:
            backup_file = self.backup_service.create_database_backup(
                backup_dir=temp_backup_dir,
                db_path=self.db_path,
            )
            self.assertTrue(os.path.exists(backup_file))
            self.assertGreater(os.path.getsize(backup_file), 0)
        finally:
            if os.path.exists(temp_backup_dir):
                for f in os.listdir(temp_backup_dir):
                    os.remove(os.path.join(temp_backup_dir, f))
                os.rmdir(temp_backup_dir)

    # ---------------- AnalyticsService & ChartFormatter Tests ---------------- #

    def test_analytics_service_and_chart_formatter(self):
        self.trans_service.add_transaction(400.0, "Utilities", "expense", "2026-10-01")
        self.trans_service.add_transaction(600.0, "Entertainment", "expense", "2026-10-02")

        breakdown = self.analytics_service.get_category_breakdown("expense", "2026-10")
        self.assertEqual(breakdown["Utilities"], 400.0)
        self.assertEqual(breakdown["Entertainment"], 600.0)

        chart = ChartFormatter.generate_ascii_bar_chart(breakdown, title="Test Breakdown")
        self.assertIn("Test Breakdown", chart)
        self.assertIn("Utilities", chart)
        self.assertIn("Entertainment", chart)
        self.assertIn("█", chart)

        empty_chart = ChartFormatter.generate_ascii_bar_chart({}, title="Empty")
        self.assertIn("No data available", empty_chart)


if __name__ == "__main__":
    unittest.main()
