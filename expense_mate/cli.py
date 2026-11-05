from datetime import datetime

from .database import DatabaseManager
from .services import ExpenseService
from .analytics import AnalyticsEngine
from .importer_exporter import DataPortabilityManager


class ExpenseMateCLI:
    def __init__(self, db_path: str = "expense_mate.db"):
        self.db = DatabaseManager(db_path)
        self.services = ExpenseService(self.db)
        self.analytics = AnalyticsEngine(self.db)
        self.portability = DataPortabilityManager(self.db)

    def print_header(self, text: str) -> None:
        print("\n" + "=" * 60)
        print(f"   {text}")
        print("=" * 60)

    def show_error(self, message: str) -> None:
        print(f"\n[!] Error: {message}")

    def prompt_float(self, prompt: str) -> float:
        while True:
            try:
                value = input(prompt).strip()
                if not value:
                    raise ValueError("Value cannot be empty.")
                return float(value)
            except ValueError as exc:
                self.show_error(f"Please enter a valid number. {exc}")

    def validate_transaction_data(self, trans_type: str, amount_text: str, category: str, date_str: str) -> float:
        errors = []
        normalized_type = trans_type.strip().lower()

        if normalized_type not in ("income", "expense"):
            errors.append("Transaction type must be 'income' or 'expense'.")

        try:
            amount = float(amount_text)
            if amount <= 0:
                errors.append("Amount must be strictly positive.")
        except (TypeError, ValueError):
            errors.append("Amount must be a valid number.")
            amount = 0.0

        if not category or not category.strip():
            errors.append("Category cannot be empty.")

        try:
            parsed_date = datetime.strptime(date_str, "%Y-%m-%d")
            if parsed_date.strftime("%Y-%m-%d") != date_str:
                raise ValueError
        except ValueError:
            errors.append("Date must follow format YYYY-MM-DD.")

        if errors:
            raise ValueError("; ".join(errors))

        return amount

    def validate_currency_data(self, amount_text: str, from_curr: str, to_curr: str) -> float:
        errors = []

        try:
            amount = float(amount_text)
            if amount < 0:
                errors.append("Amount cannot be negative.")
        except (TypeError, ValueError):
            errors.append("Amount must be a valid number.")
            amount = 0.0

        if not from_curr or not from_curr.strip():
            errors.append("From currency cannot be empty.")

        if not to_curr or not to_curr.strip():
            errors.append("To currency cannot be empty.")

        if errors:
            raise ValueError("; ".join(errors))

        return amount

    def run(self) -> None:
        while True:
            try:
                self.print_header("EXPENSEMATE - PERSONAL EXPENSE MANAGER")
                print(" 1. Add Transaction (Income / Expense)")
                print(" 2. View All Transactions")
                print(" 3. View Financial Summary & Net Balance")
                print(" 4. Manage Monthly Budgets & View Alerts")
                print(" 5. Visual Analytics & Category Breakdown")
                print(" 6. Monthly Spending & Savings Trends")
                print(" 7. Export Transactions to CSV")
                print(" 8. Import Transactions from CSV")
                print(" 9. Multi-Currency Converter")
                print("10. Backup Database")
                print(" 0. Exit")
                print("-" * 60)

                choice = input("Enter option [0-10]: ").strip()

                if choice == "1":
                    try:
                        while True:
                            trans_type = input("Type (income / expense): ").strip().lower()

                            if trans_type in ("income", "expense"):
                                break

                            self.show_error(
                                "Invalid type. Please enter exactly 'income' or 'expense'."
                            )

                        while True:
                            amount_text = input("Amount: ").strip()

                            try:
                                amount = float(amount_text)

                                if amount <= 0:
                                    raise ValueError

                                break

                            except ValueError:
                                self.show_error(
                                    "Invalid amount. Please enter a positive number greater than 0."
                                )

                        while True:
                            category = input(
                                "Category (e.g., Food, Salary, Rent): "
                            ).strip()

                            if category:
                                break

                            self.show_error(
                                "Category cannot be empty. Please enter a category."
                            )

                        while True:
                            date_str = input(
                                f"Date (YYYY-MM-DD, Enter for {datetime.today().strftime('%Y-%m-%d')}): "
                            ).strip()

                            if not date_str:
                                date_str = datetime.today().strftime("%Y-%m-%d")

                            try:
                                parsed_date = datetime.strptime(
                                    date_str, "%Y-%m-%d"
                                )

                                if parsed_date.strftime("%Y-%m-%d") != date_str:
                                    raise ValueError

                                break

                            except ValueError:
                                self.show_error(
                                    "Invalid date format. Please use YYYY-MM-DD."
                                )

                        desc = input("Description: ").strip()

                        tid = self.services.add_transaction(
                            amount,
                            category,
                            trans_type,
                            date_str,
                            desc
                        )

                        print(
                            f"\n[+] Successfully recorded transaction #{tid}!"
                        )

                        if trans_type == "expense":
                            status = self.services.check_budget_status(
                                category,
                                date_str[:7]
                            )

                            if status and status.level in ("WARNING", "CRITICAL"):
                                print(f"\n[ALERT] {status.message}")

                    except Exception as e:
                        self.show_error(e)

                elif choice == "2":
                    try:
                        transactions = self.services.list_transactions()

                        print(
                            f"\n{'ID':<5} | {'Date':<10} | {'Type':<8} | "
                            f"{'Category':<15} | {'Amount':>10} | {'Description'}"
                        )

                        print("-" * 75)

                        for t in transactions:
                            print(
                                f"{t.id:<5} | {t.date:<10} | {t.trans_type:<8} | "
                                f"{t.category:<15} | {t.amount:>10.2f} | "
                                f"{t.description}"
                            )

                    except Exception as e:
                        self.show_error(e)

                elif choice == "3":
                    try:
                        summary = self.services.get_net_summary()

                        print(
                            f"\nTotal Income : {summary['total_income']:>12.2f}"
                        )
                        print(
                            f"Total Expense: {summary['total_expense']:>12.2f}"
                        )
                        print(
                            f"Net Balance  : {summary['net_savings']:>12.2f}"
                        )

                    except Exception as e:
                        self.show_error(e)

                elif choice == "4":
                    try:
                        my = input(
                            f"Month (YYYY-MM, Enter for {datetime.today().strftime('%Y-%m')}): "
                        ).strip()

                        if not my:
                            my = datetime.today().strftime("%Y-%m")

                        try:
                            parsed_month = datetime.strptime(my, "%Y-%m")

                            if parsed_month.strftime("%Y-%m") != my:
                                raise ValueError

                        except ValueError:
                            self.show_error(
                                "Invalid month format. Please use YYYY-MM."
                            )
                            continue

                        statuses = self.services.get_all_budget_statuses(my)

                        if not statuses:
                            print(f"\nNo budgets found for {my}.")

                            add_budget = input(
                                "Add a budget for this month? (y/n): "
                            ).strip().lower()

                            if add_budget == "y":
                                while True:
                                    category = input(
                                        "Budget category: "
                                    ).strip()

                                    if category:
                                        break

                                    self.show_error(
                                        "Category cannot be empty."
                                    )

                                while True:
                                    try:
                                        limit = float(
                                            input("Monthly limit: ").strip()
                                        )

                                        if limit <= 0:
                                            raise ValueError

                                        break

                                    except ValueError:
                                        self.show_error(
                                            "Budget limit must be a positive number."
                                        )

                                self.services.set_budget(
                                    category,
                                    limit,
                                    my
                                )

                                print(
                                    f"\n[+] Budget added for {category} in {my}."
                                )

                                statuses = self.services.get_all_budget_statuses(my)

                        if statuses:
                            for st in statuses:
                                print(
                                    f"[{st.level}] {st.category}: "
                                    f"Spent {st.spent:.2f}/{st.limit:.2f} "
                                    f"({st.percentage:.1f}%)"
                                )

                    except Exception as e:
                        self.show_error(e)

                elif choice == "5":
                    try:
                        month_filter = input(
                            "Month filter (YYYY-MM, press Enter for all): "
                        ).strip()

                        if month_filter:
                            try:
                                parsed_month = datetime.strptime(
                                    month_filter,
                                    "%Y-%m"
                                )

                                if parsed_month.strftime("%Y-%m") != month_filter:
                                    raise ValueError

                            except ValueError:
                                self.show_error(
                                    "Invalid month format. Please use YYYY-MM."
                                )
                                continue

                        breakdown = self.analytics.get_category_breakdown(
                            "expense",
                            month_filter or None
                        )

                        print(
                            self.analytics.generate_ascii_bar_chart(
                                breakdown,
                                title="Expense Category Breakdown"
                            )
                        )

                    except Exception as e:
                        self.show_error(e)

                elif choice == "6":
                    try:
                        trends = self.analytics.get_monthly_trends()

                        print(
                            f"\n{'Month':<10} | {'Income':>10} | "
                            f"{'Expense':>10} | {'Savings':>10}"
                        )

                        print("-" * 50)

                        for my, val in trends.items():
                            print(
                                f"{my:<10} | {val['income']:>10.2f} | "
                                f"{val['expense']:>10.2f} | "
                                f"{val['savings']:>10.2f}"
                            )

                    except Exception as e:
                        self.show_error(e)

                elif choice == "7":
                    try:
                        count = self.portability.export_to_csv(
                            "expenses_export.csv"
                        )

                        print(
                            f"\n[+] Exported {count} transactions "
                            f"to 'expenses_export.csv'."
                        )

                    except Exception as e:
                        self.show_error(e)

                elif choice == "8":
                    try:
                        fn = input("CSV Path: ").strip()

                        if not fn:
                            raise ValueError("CSV path cannot be empty.")

                        s, e, _ = self.portability.import_from_csv(fn)

                        print(
                            f"\n[+] Imported: {s} success, {e} errors."
                        )

                    except Exception as e:
                        self.show_error(e)

                elif choice == "9":
                    try:
                        amount_text = input("Amount: ").strip()
                        f_c = input("From Currency: ").strip().upper()
                        t_c = input("To Currency: ").strip().upper()

                        amt = self.validate_currency_data(
                            amount_text,
                            f_c,
                            t_c
                        )

                        print(
                            f"\n[+] Converted: "
                            f"{self.services.convert_amount(amt, f_c, t_c)}"
                        )

                    except Exception as e:
                        self.show_error(e)

                elif choice == "10":
                    try:
                        backup_path = self.services.create_database_backup()

                        print(
                            f"\n[+] Backup saved to: {backup_path}"
                        )

                    except Exception as e:
                        self.show_error(e)

                elif choice == "0":
                    print("\nGoodbye!\n")
                    break

                else:
                    self.show_error(
                        "Invalid option selected. Please choose from 0 to 10."
                    )

            except KeyboardInterrupt:
                print(
                    "\nProgram interrupted. Exiting gracefully.\n"
                )
                break

            except Exception as e:
                self.show_error(
                    f"Unexpected problem: {e}"
                )

