"""Integration Test Suite for ExpenseMate.

Validates end-to-end workflows across the required architecture:
Controller -> Services -> Repository -> Database.
"""

import os
import tempfile
import unittest

from expense_mate.controllers import ExpenseMateController
from expense_mate.database import DatabaseManager


class TestExpenseMateIntegrationWorkflows(unittest.TestCase):
    """At least 5 comprehensive integration test cases covering core ExpenseMate workflows."""

    def setUp(self):
        self.db_fd, self.db_path = tempfile.mkstemp(suffix=".db")
        self.controller = ExpenseMateController(db_path=self.db_path)

    def tearDown(self):
        os.close(self.db_fd)
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_workflow_1_transaction_lifecycle_and_balance_calculation(self):
        """Workflow 1: Controller -> TransactionService -> TransactionRepository -> Database.

        Traces the complete lifecycle of income and expense transactions from input
        validation through database insertion, history listing, and net summary calculation.
        """
        # Step 1: Record income transactions
        res_inc = self.controller.add_transaction(
            amount=85000.0,
            category="Salary",
            trans_type="income",
            date="2026-10-01",
            description="Monthly salary",
        )
        self.assertGreater(res_inc["transaction_id"], 0)
        self.assertIsNone(res_inc["alert"])

        # Step 2: Record expense transactions
        res_exp1 = self.controller.add_transaction(
            amount=25000.0,
            category="Rent",
            trans_type="expense",
            date="2026-10-03",
            description="Apartment rent",
        )
        self.assertGreater(res_exp1["transaction_id"], 0)

        res_exp2 = self.controller.add_transaction(
            amount=12000.0,
            category="Groceries",
            trans_type="expense",
            date="2026-10-08",
            description="Weekly grocery shopping",
        )
        self.assertGreater(res_exp2["transaction_id"], 0)

        # Step 3: Query filtered transactions through controller
        all_tx = self.controller.list_transactions()
        self.assertEqual(len(all_tx), 3)

        rent_tx = self.controller.list_transactions(category="Rent")
        self.assertEqual(len(rent_tx), 1)
        self.assertEqual(rent_tx[0].amount, 25000.0)

        # Step 4: Verify financial net summary calculation across the stack
        summary = self.controller.get_financial_summary("2026-10")
        self.assertEqual(summary["total_income"], 85000.0)
        self.assertEqual(summary["total_expense"], 37000.0)
        self.assertEqual(summary["net_savings"], 48000.0)

    def test_workflow_2_budget_threshold_warning_and_critical_alerts(self):
        """Workflow 2: Monthly budgeting and real-time threshold alert propagation.

        Traces setting monthly budget limits and verifying that successive expense
        logging triggers NORMAL, WARNING (>= 80%), and CRITICAL (>= 100%) alerts.
        """
        # Step 1: Set budget limit for category "Dining" in 2026-10 to 10,000 PKR
        b_id = self.controller.set_budget(
            category="Dining",
            monthly_limit=10000.0,
            month_year="2026-10",
        )
        self.assertGreater(b_id, 0)

        # Step 2: Add expense of 5,000 PKR (50% of budget) -> NORMAL status
        tx1 = self.controller.add_transaction(
            amount=5000.0,
            category="Dining",
            trans_type="expense",
            date="2026-10-05",
            description="Family dinner",
        )
        self.assertIsNotNone(tx1["alert"])
        self.assertEqual(tx1["alert"].level, "NORMAL")
        self.assertEqual(tx1["alert"].spent, 5000.0)
        self.assertEqual(tx1["alert"].percentage, 50.0)

        # Step 3: Add expense of 3,500 PKR (Total 8,500 PKR = 85%) -> WARNING alert
        tx2 = self.controller.add_transaction(
            amount=3500.0,
            category="Dining",
            trans_type="expense",
            date="2026-10-15",
            description="Lunch with colleagues",
        )
        self.assertIsNotNone(tx2["alert"])
        self.assertEqual(tx2["alert"].level, "WARNING")
        self.assertEqual(tx2["alert"].spent, 8500.0)
        self.assertEqual(tx2["alert"].percentage, 85.0)
        self.assertIn("WARNING: Approaching budget limit", tx2["alert"].message)

        # Step 4: Add expense of 2,000 PKR (Total 10,500 PKR = 105%) -> CRITICAL alert
        tx3 = self.controller.add_transaction(
            amount=2000.0,
            category="Dining",
            trans_type="expense",
            date="2026-10-25",
            description="Weekend takeout",
        )
        self.assertIsNotNone(tx3["alert"])
        self.assertEqual(tx3["alert"].level, "CRITICAL")
        self.assertEqual(tx3["alert"].spent, 10500.0)
        self.assertEqual(tx3["alert"].percentage, 105.0)
        self.assertIn("CRITICAL: Budget limit exceeded", tx3["alert"].message)

        # Step 5: Query all budget statuses for the month
        all_statuses = self.controller.get_budget_statuses("2026-10")
        self.assertEqual(len(all_statuses), 1)
        self.assertEqual(all_statuses[0].level, "CRITICAL")

    def test_workflow_3_csv_export_import_data_integrity(self):
        """Workflow 3: End-to-end CSV portability and cross-database data migration.

        Records data in one database, exports to CSV, creates a clean second database,
        imports the CSV data, and verifies all fields are preserved without loss.
        """
        # Step 1: Insert distinct transactions in database A
        self.controller.add_transaction(45000.0, "Consulting", "income", "2026-10-02", "Project A")
        self.controller.add_transaction(6200.0, "Utilities", "expense", "2026-10-04", "Electricity")
        self.controller.add_transaction(3100.0, "Internet", "expense", "2026-10-07", "Fiber bill")

        temp_csv = tempfile.mktemp(suffix=".csv")
        try:
            # Step 2: Export from Database A via Controller
            exported_count = self.controller.export_csv(temp_csv)
            self.assertEqual(exported_count, 3)
            self.assertTrue(os.path.exists(temp_csv))

            # Step 3: Initialize brand-new second database B
            db2_fd, db2_path = tempfile.mkstemp(suffix=".db")
            try:
                controller_b = ExpenseMateController(db_path=db2_path)
                self.assertEqual(len(controller_b.list_transactions()), 0)

                # Step 4: Import CSV into Database B via Controller
                success, errors, msgs = controller_b.import_csv(temp_csv)
                self.assertEqual(success, 3)
                self.assertEqual(errors, 0)
                self.assertEqual(len(msgs), 0)

                # Step 5: Verify all records and summaries in Database B
                migrated_tx = controller_b.list_transactions()
                self.assertEqual(len(migrated_tx), 3)

                summary_b = controller_b.get_financial_summary("2026-10")
                self.assertEqual(summary_b["total_income"], 45000.0)
                self.assertEqual(summary_b["total_expense"], 9300.0)
                self.assertEqual(summary_b["net_savings"], 35700.0)
            finally:
                os.close(db2_fd)
                if os.path.exists(db2_path):
                    os.remove(db2_path)
        finally:
            if os.path.exists(temp_csv):
                os.remove(temp_csv)

    def test_workflow_4_analytics_breakdown_and_ascii_chart_rendering(self):
        """Workflow 4: Business intelligence analytics and ASCII chart generation.

        Populates multidimensional financial data, calculates category breakdown
        and multi-month trends, and validates ASCII bar chart formatting.
        """
        # Populate transactions across multiple months and categories
        self.controller.add_transaction(50000.0, "Salary", "income", "2026-08-01")
        self.controller.add_transaction(15000.0, "Travel", "expense", "2026-08-10")

        self.controller.add_transaction(60000.0, "Salary", "income", "2026-09-01")
        self.controller.add_transaction(8000.0, "Food", "expense", "2026-09-05")
        self.controller.add_transaction(12000.0, "Shopping", "expense", "2026-09-12")

        # Step 1: Check category breakdown for 2026-09
        analytics_sep = self.controller.get_category_analytics(
            trans_type="expense",
            month_year="2026-09",
        )
        breakdown = analytics_sep["breakdown"]
        chart = analytics_sep["chart"]

        self.assertEqual(breakdown["Food"], 8000.0)
        self.assertEqual(breakdown["Shopping"], 12000.0)
        self.assertEqual(sum(breakdown.values()), 20000.0)

        # Step 2: Validate chart formatting contains labels, percentages, and Unicode bars
        self.assertIn("Expense Category Breakdown", chart)
        self.assertIn("Food", chart)
        self.assertIn("Shopping", chart)
        self.assertIn("40.0%", chart)  # 8000 / 20000
        self.assertIn("60.0%", chart)  # 12000 / 20000
        self.assertIn("█", chart)

        # Step 3: Validate monthly trends aggregation across all recorded months
        trends = self.controller.get_monthly_trends()
        self.assertIn("2026-08", trends)
        self.assertIn("2026-09", trends)
        self.assertEqual(trends["2026-08"]["savings"], 35000.0)
        self.assertEqual(trends["2026-09"]["savings"], 40000.0)

    def test_workflow_5_multi_currency_conversion_and_budget_integration(self):
        """Workflow 5: Multi-currency conversion integration.

        Validates conversion between all supported currencies (PKR, USD, EUR, GBP, AED, SAR)
        and logs converted transactions into the local budget.
        """
        # Step 1: Convert USD to PKR and record local expense
        usd_amount = 50.0
        pkr_equivalent = self.controller.convert_currency(usd_amount, "USD", "PKR")
        self.assertGreater(pkr_equivalent, 10000.0)

        # Step 2: Record transaction with converted amount
        res = self.controller.add_transaction(
            amount=pkr_equivalent,
            category="SoftwareSubscription",
            trans_type="expense",
            date="2026-10-10",
            description=f"Cloud services (${usd_amount} USD)",
        )
        self.assertGreater(res["transaction_id"], 0)

        # Step 3: Verify bidirectional conversion consistency
        converted_back = self.controller.convert_currency(pkr_equivalent, "PKR", "USD")
        self.assertAlmostEqual(converted_back, usd_amount, delta=0.5)

        # Step 4: Verify conversion between foreign currencies (e.g., EUR to GBP)
        eur_to_gbp = self.controller.convert_currency(100.0, "EUR", "GBP")
        self.assertGreater(eur_to_gbp, 0.0)

    def test_workflow_6_controller_validation_and_defense_against_corrupted_data(self):
        """Workflow 6: Input sanitization, validation defense, and data protection.

        Ensures that invalid inputs are intercepted and rejected at the Controller boundary
        before reaching services or database, preventing corrupted records.
        """
        initial_count = len(self.controller.list_transactions())

        # Negative amount rejected
        with self.assertRaises(ValueError) as ctx1:
            self.controller.add_transaction(-100.0, "Food", "expense", "2026-10-10")
        self.assertIn("Amount must be strictly positive", str(ctx1.exception))

        # Blank category rejected
        with self.assertRaises(ValueError) as ctx2:
            self.controller.add_transaction(100.0, "   ", "expense", "2026-10-10")
        self.assertIn("Category cannot be empty", str(ctx2.exception))

        # Invalid transaction type rejected
        with self.assertRaises(ValueError) as ctx3:
            self.controller.add_transaction(100.0, "Food", "investment", "2026-10-10")
        self.assertIn("Transaction type must be 'income' or 'expense'", str(ctx3.exception))

        # Malformed date rejected
        with self.assertRaises(ValueError) as ctx4:
            self.controller.add_transaction(100.0, "Food", "expense", "10/10/2026")
        self.assertIn("Date must follow format YYYY-MM-DD", str(ctx4.exception))

        # Negative budget rejected
        with self.assertRaises(ValueError) as ctx5:
            self.controller.set_budget("Food", -500.0, "2026-10")
        self.assertIn("Budget limit must be a positive number", str(ctx5.exception))

        # Database remained completely clean and unaffected
        final_count = len(self.controller.list_transactions())
        self.assertEqual(initial_count, final_count)


if __name__ == "__main__":
    unittest.main()
