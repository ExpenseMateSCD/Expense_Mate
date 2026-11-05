import csv
from typing import List, Tuple, Union

from .database import DatabaseManager
from .models import Transaction
from .repositories import TransactionRepository


class DataPortabilityManager:
    """Handles CSV export and import for transactions via the repository layer."""

    def __init__(
        self,
        repository: Union[TransactionRepository, DatabaseManager],
    ):
        if isinstance(repository, DatabaseManager):
            self.db = repository
            self.repository = TransactionRepository(repository)
        else:
            self.repository = repository
            self.db = repository.database

    def export_to_csv(self, file_path: str) -> int:
        try:
            transactions = self.repository.get_all()

            with open(
                file_path,
                mode="w",
                newline="",
                encoding="utf-8",
            ) as f:
                writer = csv.writer(f)
                writer.writerow([
                    "ID",
                    "Amount",
                    "Category",
                    "Type",
                    "Date",
                    "Description",
                ])

                for t in transactions:
                    writer.writerow([
                        t.id,
                        t.amount,
                        t.category,
                        t.trans_type,
                        t.date,
                        t.description,
                    ])

            return len(transactions)

        except (OSError, csv.Error, RuntimeError) as exc:
            raise RuntimeError(
                f"Unable to export transactions to CSV: {exc}"
            ) from exc

    def import_from_csv(
        self,
        file_path: str,
    ) -> Tuple[int, int, List[str]]:
        success_count, error_count, errors = 0, 0, []

        try:
            with open(
                file_path,
                mode="r",
                newline="",
                encoding="utf-8",
            ) as f:
                reader = csv.DictReader(f)

                for line_no, row in enumerate(reader, start=2):
                    try:
                        amount = float(row.get("Amount", 0))
                        category = row.get("Category", "").strip()
                        trans_type = row.get("Type", "").strip().lower()
                        date = row.get("Date", "").strip()
                        description = row.get("Description", "").strip()

                        t = Transaction(
                            id=None,
                            amount=amount,
                            category=category,
                            trans_type=trans_type,
                            date=date,
                            description=description,
                        )

                        self.repository.add(t)
                        success_count += 1

                    except Exception as e:
                        error_count += 1
                        errors.append(f"Row {line_no}: {str(e)}")

            return success_count, error_count, errors

        except (OSError, csv.Error) as exc:
            raise RuntimeError(
                f"Unable to import CSV file: {exc}"
            ) from exc
