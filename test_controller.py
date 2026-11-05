"""Unit test suite for ExpenseMateController."""

import os
import tempfile
import unittest

from expense_mate.controllers import ExpenseMateController


class TestExpenseMateController(unittest.TestCase):
    def setUp(self):
        self.db_fd, self.db_path = tempfile.mkstemp(suffix=".db")
        self.controller = ExpenseMateController(db_path=self.db_path)

    def tearDown(self):
        os.close(self.db_fd)
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_controller_validations(self):
        # Invalid type
        with self.assertRaises(ValueError):
            self.controller.validate_transaction_data("transfer", 100, "Food", "2026-10-01")

        # Invalid amount
        with self.assertRaises(ValueError):
            self.controller.validate_transaction_data("expense", -50, "Food", "2026-10-01")

        # Empty category
        with self.assertRaises(ValueError):
            self.controller.validate_transaction_data("expense", 50, "   ", "2026-10-01")

        # Invalid date
        with self.assertRaises(ValueError):
            self.controller.validate_transaction_data("expense", 50, "Food", "01-10-2026")

        # Invalid month
        with self.assertRaises(ValueError):
            self.controller.validate_month_format("2026/10")

        # Invalid currency amount
        with self.assertRaises(ValueError):
            self.controller.validate_currency_data(-10, "USD", "PKR")

    def test_controller_add_and_list_transaction(self):
        res1 = self.controller.add_transaction(
            amount=2500.0,
            category="Salary",
            trans_type="income",
            date="2026-10-01",
            description="Freelance project",
        )
        self.assertGreater(res1["transaction_id"], 0)
        self.assertIsNone(res1["alert"])

        tx_list = self.controller.list_transactions()
        self.assertEqual(len(tx_list), 1)
        self.assertEqual(tx_list[0].category, "Salary")

    def test_controller_budget_alert_generation(self):
        self.controller.set_budget("Dining", 1000.0, "2026-10")

        # Expense triggers alert calculation in controller
        res1 = self.controller.add_transaction(
            amount=850.0,
            category="Dining",
            trans_type="expense",
            date="2026-10-05",
        )
        self.assertIsNotNone(res1["alert"])
        self.assertEqual(res1["alert"].level, "WARNING")

        statuses = self.controller.get_budget_statuses("2026-10")
        self.assertEqual(len(statuses), 1)
        self.assertEqual(statuses[0].category, "Dining")

    def test_controller_summary_and_analytics(self):
        self.controller.add_transaction(10000.0, "IncomeSource", "income", "2026-10-01")
        self.controller.add_transaction(2000.0, "Bills", "expense", "2026-10-02")

        summary = self.controller.get_financial_summary("2026-10")
        self.assertEqual(summary["total_income"], 10000.0)
        self.assertEqual(summary["total_expense"], 2000.0)
        self.assertEqual(summary["net_savings"], 8000.0)

        analytics = self.controller.get_category_analytics("expense", "2026-10")
        self.assertIn("breakdown", analytics)
        self.assertIn("chart", analytics)
        self.assertEqual(analytics["breakdown"]["Bills"], 2000.0)
        self.assertIn("Bills", analytics["chart"])

    def test_controller_currency_conversion(self):
        result = self.controller.convert_currency(100.0, "USD", "PKR")
        self.assertAlmostEqual(result, 27777.78, delta=1.0)


if __name__ == "__main__":
    unittest.main()
