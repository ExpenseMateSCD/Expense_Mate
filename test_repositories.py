import os
import tempfile
import unittest

from expense_mate.database import DatabaseManager
from expense_mate.models import Budget, Transaction
from expense_mate.repositories import BudgetRepository, TransactionRepository


class TestRepositories(unittest.TestCase):
    def setUp(self):
        self.db_fd, self.db_path = tempfile.mkstemp(suffix=".db")
        self.database = DatabaseManager(self.db_path)
        self.transactions = TransactionRepository(self.database)
        self.budgets = BudgetRepository(self.database)

    def tearDown(self):
        os.close(self.db_fd)
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_transaction_repository_preserves_records(self):
        transaction_id = self.transactions.add(
            Transaction(
                id=None,
                amount=250.0,
                category="Food",
                trans_type="expense",
                date="2026-09-10",
                description="Lunch",
            )
        )

        records = self.transactions.get_by_month("2026-09")

        self.assertGreater(transaction_id, 0)
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].category, "Food")
        self.assertEqual(records[0].description, "Lunch")

    def test_budget_repository_updates_existing_monthly_budget(self):
        budget = Budget(
            id=None,
            category="Food",
            monthly_limit=10000.0,
            month_year="2026-09",
        )
        self.budgets.save(budget)
        self.budgets.save(
            Budget(
                id=None,
                category="Food",
                monthly_limit=12000.0,
                month_year="2026-09",
            )
        )

        stored = self.budgets.get("Food", "2026-09")

        self.assertIsNotNone(stored)
        self.assertEqual(stored.monthly_limit, 12000.0)
        self.assertEqual(len(self.budgets.get_for_month("2026-09")), 1)


if __name__ == "__main__":
    unittest.main()
