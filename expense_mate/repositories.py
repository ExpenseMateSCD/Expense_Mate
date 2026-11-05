from typing import List, Optional, TYPE_CHECKING

from .models import Budget, Transaction

if TYPE_CHECKING:
    from .database import DatabaseManager


class TransactionRepository:
    """Data-access operations for transactions."""

    def __init__(self, database: "DatabaseManager"):
        self.database = database

    def add(self, transaction: Transaction) -> int:
        transaction.validate()
        with self.database.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO transactions
                    (amount, category, trans_type, date, description)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    transaction.amount,
                    transaction.category.strip(),
                    transaction.trans_type,
                    transaction.date,
                    transaction.description.strip(),
                ),
            )
            conn.commit()
            return cursor.lastrowid

    def get_all(self) -> List[Transaction]:
        with self.database.get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM transactions ORDER BY date DESC, id DESC"
            ).fetchall()
        return [self._to_model(row) for row in rows]

    def get_by_month(self, month_year: str) -> List[Transaction]:
        with self.database.get_connection() as conn:
            rows = conn.execute(
                """
                SELECT * FROM transactions
                WHERE date LIKE ?
                ORDER BY date DESC, id DESC
                """,
                (f"{month_year}%",),
            ).fetchall()
        return [self._to_model(row) for row in rows]

    @staticmethod
    def _to_model(row) -> Transaction:
        return Transaction(
            id=row["id"],
            amount=row["amount"],
            category=row["category"],
            trans_type=row["trans_type"],
            date=row["date"],
            description=row["description"],
        )


class BudgetRepository:
    """Data-access operations for monthly budgets."""

    def __init__(self, database: "DatabaseManager"):
        self.database = database

    def save(self, budget: Budget) -> int:
        budget.validate()
        with self.database.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO budgets (category, monthly_limit, month_year)
                VALUES (?, ?, ?)
                ON CONFLICT(category, month_year) DO UPDATE SET
                    monthly_limit = excluded.monthly_limit
                """,
                (
                    budget.category.strip(),
                    budget.monthly_limit,
                    budget.month_year,
                ),
            )
            conn.commit()
            return cursor.lastrowid

    def get(self, category: str, month_year: str) -> Optional[Budget]:
        with self.database.get_connection() as conn:
            row = conn.execute(
                """
                SELECT * FROM budgets
                WHERE category = ? AND month_year = ?
                """,
                (category.strip(), month_year),
            ).fetchone()
        return self._to_model(row) if row else None

    def get_for_month(self, month_year: str) -> List[Budget]:
        with self.database.get_connection() as conn:
            rows = conn.execute(
                """
                SELECT * FROM budgets
                WHERE month_year = ?
                ORDER BY category
                """,
                (month_year,),
            ).fetchall()
        return [self._to_model(row) for row in rows]

    @staticmethod
    def _to_model(row) -> Budget:
        return Budget(
            id=row["id"],
            category=row["category"],
            monthly_limit=row["monthly_limit"],
            month_year=row["month_year"],
        )
