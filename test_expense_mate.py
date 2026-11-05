"""
Automated Unit and Integration Test Suite for ExpenseMate.
"""

import os
import unittest
import tempfile
from expense_mate.models import Transaction
from expense_mate.database import DatabaseManager
from expense_mate.services import ExpenseService
from expense_mate.analytics import AnalyticsEngine
from expense_mate.importer_exporter import DataPortabilityManager

class TestExpenseMate(unittest.TestCase):
    def setUp(self):
        self.temp_db_fd, self.temp_db_path = tempfile.mkstemp(suffix=".db")
        self.db = DatabaseManager(self.temp_db_path)
        self.services = ExpenseService(self.db)
        self.analytics = AnalyticsEngine(self.db)
        self.portability = DataPortabilityManager(self.db)

    def tearDown(self):
        os.close(self.temp_db_fd)
        if os.path.exists(self.temp_db_path):
            os.remove(self.temp_db_path)

    def test_transaction_validation_valid(self):
        t = Transaction(id=None, amount=150.0, category="Groceries", trans_type="expense", date="2026-09-24")
        t.validate()

    def test_transaction_validation_negative_amount(self):
        t = Transaction(id=None, amount=-50.0, category="Groceries", trans_type="expense", date="2026-09-24")
        with self.assertRaises(ValueError):
            t.validate()

    def test_transaction_validation_invalid_date(self):
        t = Transaction(id=None, amount=50.0, category="Groceries", trans_type="expense", date="24-09-2026")
        with self.assertRaises(ValueError):
            t.validate()

    def test_insert_and_get_all_transactions(self):
        tid1 = self.services.add_transaction(50000.0, "Salary", "income", "2026-09-01", "Monthly salary")
        tid2 = self.services.add_transaction(12000.0, "Rent", "expense", "2026-09-05", "Apartment rent")
        self.assertTrue(tid1 > 0)
        self.assertTrue(tid2 > 0)

        all_t = self.db.get_all_transactions()
        self.assertEqual(len(all_t), 2)

    def test_net_summary_calculation(self):
        self.services.add_transaction(100000.0, "Salary", "income", "2026-09-01")
        self.services.add_transaction(20000.0, "Rent", "expense", "2026-09-05")
        self.services.add_transaction(10000.0, "Food", "expense", "2026-09-10")

        summary = self.services.get_net_summary("2026-09")
        self.assertEqual(summary["total_income"], 100000.0)
        self.assertEqual(summary["total_expense"], 30000.0)
        self.assertEqual(summary["net_savings"], 70000.0)

    def test_budget_threshold_alerts(self):
        self.services.set_budget("Food", 10000.0, "2026-09")

        self.services.add_transaction(5000.0, "Food", "expense", "2026-09-02")
        st1 = self.services.check_budget_status("Food", "2026-09")
        self.assertEqual(st1.level, "NORMAL")
        self.assertEqual(st1.percentage, 50.0)

        self.services.add_transaction(3500.0, "Food", "expense", "2026-09-15")
        st2 = self.services.check_budget_status("Food", "2026-09")
        self.assertEqual(st2.level, "WARNING")
        self.assertEqual(st2.percentage, 85.0)

        self.services.add_transaction(2000.0, "Food", "expense", "2026-09-20")
        st3 = self.services.check_budget_status("Food", "2026-09")
        self.assertEqual(st3.level, "CRITICAL")
        self.assertEqual(st3.percentage, 105.0)

    def test_currency_conversion(self):
        conv = self.services.convert_amount(100.0, "USD", "PKR")
        self.assertAlmostEqual(conv, 27777.78, delta=1.0)

        conv2 = self.services.convert_amount(27777.78, "PKR", "USD")
        self.assertAlmostEqual(conv2, 100.0, delta=1.0)

    def test_csv_export_and_import(self):
        self.services.add_transaction(500.0, "Utilities", "expense", "2026-09-10", "Electricity")
        self.services.add_transaction(1500.0, "Freelance", "income", "2026-09-12", "Logo design")

        temp_csv = tempfile.mktemp(suffix=".csv")
        try:
            exp_count = self.portability.export_to_csv(temp_csv)
            self.assertEqual(exp_count, 2)

            new_db_fd, new_db_path = tempfile.mkstemp(suffix=".db")
            try:
                new_db = DatabaseManager(new_db_path)
                new_port = DataPortabilityManager(new_db)
                succ, errs, msgs = new_port.import_from_csv(temp_csv)
                self.assertEqual(succ, 2)
                self.assertEqual(errs, 0)
                self.assertEqual(len(new_db.get_all_transactions()), 2)
            finally:
                os.close(new_db_fd)
                if os.path.exists(new_db_path):
                    os.remove(new_db_path)
        finally:
            if os.path.exists(temp_csv):
                os.remove(temp_csv)

    def test_analytics_breakdown(self):
        self.services.add_transaction(200.0, "Food", "expense", "2026-09-01")
        self.services.add_transaction(300.0, "Food", "expense", "2026-09-05")
        self.services.add_transaction(500.0, "Transport", "expense", "2026-09-08")

        breakdown = self.analytics.get_category_breakdown("expense", "2026-09")
        self.assertEqual(breakdown["Food"], 500.0)
        self.assertEqual(breakdown["Transport"], 500.0)


if __name__ == "__main__":
    unittest.main()

