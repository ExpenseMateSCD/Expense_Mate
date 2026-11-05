from datetime import datetime
from typing import Optional

from .controllers import ExpenseMateController


class ExpenseMateCLI:
    """Presentation layer (Console UI) for ExpenseMate.

    Interacts with the user, prints menus, formats tables/alerts, and delegates
    all business requests to ExpenseMateController.
    """

    def __init__(
        self,
        db_path: str = "expense_mate.db",
        controller: Optional[ExpenseMateController] = None,
    ):
        self.controller = controller or ExpenseMateController(db_path=db_path)

    # ---------------- UI Display Helpers ---------------- #

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

    # Backward-compatible validation delegations to controller
    def validate_transaction_data(
        self,
        trans_type: str,
        amount_text: str,
        category: str,
        date_str: str,
    ) -> float:
        return self.controller.validate_transaction_data(
            trans_type=trans_type,
            amount_text=amount_text,
            category=category,
            date_str=date_str,
        )

    def validate_currency_data(
        self,
        amount_text: str,
        from_curr: str,
        to_curr: str,
    ) -> float:
        return self.controller.validate_currency_data(
            amount_text=amount_text,
            from_curr=from_curr,
            to_curr=to_curr,
        )

    # ---------------- Menu Action Handlers ---------------- #

    def _handle_add_transaction(self) -> None:
        while True:
            trans_type = input("Type (income / expense): ").strip().lower()
            if trans_type in ("income", "expense"):
                break
            self.show_error("Invalid type. Please enter exactly 'income' or 'expense'.")

        while True:
            amount_text = input("Amount: ").strip()
            try:
                amount = float(amount_text)
                if amount <= 0:
                    raise ValueError
                break
            except ValueError:
                self.show_error("Invalid amount. Please enter a positive number greater than 0.")

        while True:
            category = input("Category (e.g., Food, Salary, Rent): ").strip()
            if category:
                break
            self.show_error("Category cannot be empty. Please enter a category.")

        while True:
            date_str = input(
                f"Date (YYYY-MM-DD, Enter for {datetime.today().strftime('%Y-%m-%d')}): "
            ).strip()
            if not date_str:
                date_str = datetime.today().strftime("%Y-%m-%d")

            try:
                parsed_date = datetime.strptime(date_str, "%Y-%m-%d")
                if parsed_date.strftime("%Y-%m-%d") != date_str:
                    raise ValueError
                break
            except ValueError:
                self.show_error("Invalid date format. Please use YYYY-MM-DD.")

        desc = input("Description: ").strip()

        result = self.controller.add_transaction(
            amount=amount,
            category=category,
            trans_type=trans_type,
            date=date_str,
            description=desc,
        )

        tid = result["transaction_id"]
        print(f"\n[+] Successfully recorded transaction #{tid}!")

        alert = result.get("alert")
        if alert and alert.level in ("WARNING", "CRITICAL"):
            print(f"\n[ALERT] {alert.message}")

    def _handle_view_transactions(self) -> None:
        transactions = self.controller.list_transactions()
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

    def _handle_view_summary(self) -> None:
        summary = self.controller.get_financial_summary()
        print(f"\nTotal Income : {summary['total_income']:>12.2f}")
        print(f"Total Expense: {summary['total_expense']:>12.2f}")
        print(f"Net Balance  : {summary['net_savings']:>12.2f}")

    def _handle_manage_budgets(self) -> None:
        my = input(
            f"Month (YYYY-MM, Enter for {datetime.today().strftime('%Y-%m')}): "
        ).strip()
        if not my:
            my = datetime.today().strftime("%Y-%m")

        try:
            self.controller.validate_month_format(my)
        except ValueError as err:
            self.show_error(str(err))
            return

        statuses = self.controller.get_budget_statuses(my)

        if not statuses:
            print(f"\nNo budgets found for {my}.")
            add_budget = input("Add a budget for this month? (y/n): ").strip().lower()
            if add_budget == "y":
                while True:
                    category = input("Budget category: ").strip()
                    if category:
                        break
                    self.show_error("Category cannot be empty.")

                while True:
                    try:
                        limit = float(input("Monthly limit: ").strip())
                        if limit <= 0:
                            raise ValueError
                        break
                    except ValueError:
                        self.show_error("Budget limit must be a positive number.")

                self.controller.set_budget(
                    category=category,
                    monthly_limit=limit,
                    month_year=my,
                )
                print(f"\n[+] Budget added for {category} in {my}.")
                statuses = self.controller.get_budget_statuses(my)

        if statuses:
            for st in statuses:
                print(
                    f"[{st.level}] {st.category}: "
                    f"Spent {st.spent:.2f}/{st.limit:.2f} "
                    f"({st.percentage:.1f}%)"
                )

    def _handle_visual_analytics(self) -> None:
        month_filter = input(
            "Month filter (YYYY-MM, press Enter for all): "
        ).strip()
        if month_filter:
            try:
                self.controller.validate_month_format(month_filter)
            except ValueError as err:
                self.show_error(str(err))
                return

        analytics_res = self.controller.get_category_analytics(
            trans_type="expense",
            month_year=month_filter or None,
        )
        print(analytics_res["chart"])

    def _handle_monthly_trends(self) -> None:
        trends = self.controller.get_monthly_trends()
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

    def _handle_export_csv(self) -> None:
        count = self.controller.export_csv("expenses_export.csv")
        print(f"\n[+] Exported {count} transactions to 'expenses_export.csv'.")

    def _handle_import_csv(self) -> None:
        fn = input("CSV Path: ").strip()
        if not fn:
            raise ValueError("CSV path cannot be empty.")
        s, e, _ = self.controller.import_csv(fn)
        print(f"\n[+] Imported: {s} success, {e} errors.")

    def _handle_currency_converter(self) -> None:
        amount_text = input("Amount: ").strip()
        f_c = input("From Currency: ").strip().upper()
        t_c = input("To Currency: ").strip().upper()

        amt = self.validate_currency_data(amount_text, f_c, t_c)
        converted = self.controller.convert_currency(amt, f_c, t_c)
        print(f"\n[+] Converted: {converted}")

    def _handle_backup_database(self) -> None:
        backup_path = self.controller.backup_database()
        print(f"\n[+] Backup saved to: {backup_path}")

    # ---------------- Main Dispatcher Loop ---------------- #

    def run(self) -> None:
        handlers = {
            "1": self._handle_add_transaction,
            "2": self._handle_view_transactions,
            "3": self._handle_view_summary,
            "4": self._handle_manage_budgets,
            "5": self._handle_visual_analytics,
            "6": self._handle_monthly_trends,
            "7": self._handle_export_csv,
            "8": self._handle_import_csv,
            "9": self._handle_currency_converter,
            "10": self._handle_backup_database,
        }

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

                if choice == "0":
                    print("\nGoodbye!\n")
                    break

                handler = handlers.get(choice)
                if handler:
                    try:
                        handler()
                    except Exception as err:
                        self.show_error(str(err))
                else:
                    self.show_error(
                        "Invalid option selected. Please choose from 0 to 10."
                    )

            except KeyboardInterrupt:
                print("\nProgram interrupted. Exiting gracefully.\n")
                break
            except Exception as e:
                self.show_error(f"Unexpected problem: {e}")
