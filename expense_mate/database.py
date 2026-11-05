import sqlite3
from contextlib import contextmanager
from typing import Iterator


class DatabaseManager:
    """Owns the SQLite connection and schema lifecycle.

    CRUD operations remain available as compatibility wrappers for the
    Assignment 01 API. New code should use the repository classes directly.
    """

    def __init__(self, db_path: str = "expense_mate.db"):
        self.db_path = db_path
        self._init_schema()

    @contextmanager
    def get_connection(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row

        try:
            yield conn
        finally:
            conn.close()

    def _init_schema(self) -> None:
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS transactions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        amount REAL NOT NULL,
                        category TEXT NOT NULL,
                        trans_type TEXT NOT NULL,
                        date TEXT NOT NULL,
                        description TEXT DEFAULT ''
                    );
                """)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS budgets (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        category TEXT NOT NULL,
                        monthly_limit REAL NOT NULL,
                        month_year TEXT NOT NULL,
                        UNIQUE(category, month_year)
                    );
                """)
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_trans_date ON transactions(date);")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_trans_cat ON transactions(category);")
                conn.commit()
        except sqlite3.Error as exc:
            raise RuntimeError(f"Unable to initialize database schema: {exc}") from exc

    def _repositories(self):
        from .repositories import BudgetRepository, TransactionRepository

        return TransactionRepository(self), BudgetRepository(self)

    def insert_transaction(self, transaction) -> int:
        """Compatibility wrapper; prefer TransactionRepository.add."""
        try:
            return self._repositories()[0].add(transaction)
        except (sqlite3.Error, ValueError) as exc:
            raise ValueError(f"Failed to save transaction: {exc}") from exc

    def get_all_transactions(self):
        """Compatibility wrapper; prefer TransactionRepository.get_all."""
        try:
            return self._repositories()[0].get_all()
        except sqlite3.Error as exc:
            raise RuntimeError(f"Unable to read transactions: {exc}") from exc

    def upsert_budget(self, budget) -> int:
        """Compatibility wrapper; prefer BudgetRepository.save."""
        try:
            return self._repositories()[1].save(budget)
        except (sqlite3.Error, ValueError) as exc:
            raise ValueError(f"Failed to save budget: {exc}") from exc

    def get_budget(self, category: str, month_year: str):
        """Compatibility wrapper; prefer BudgetRepository.get."""
        try:
            return self._repositories()[1].get(category, month_year)
        except sqlite3.Error as exc:
            raise RuntimeError(f"Unable to fetch budget: {exc}") from exc

    def get_budgets_for_month(self, month_year: str):
        """Compatibility wrapper; prefer BudgetRepository.get_for_month."""
        try:
            return self._repositories()[1].get_for_month(month_year)
        except sqlite3.Error as exc:
            raise RuntimeError(f"Unable to fetch budgets: {exc}") from exc