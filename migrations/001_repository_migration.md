# Migration 001: Direct SQL to Repository Pattern Migration

- **Date:** 2026-11-05
- **Author:** Afshal Liaquat (24K-2558) — Student 1
- **Reviewed by:** Bisma Shahid (24K-3012) — Student 2
- **Scope:** `expense_mate/database.py`, `expense_mate/repositories.py`

---

## 1. Before State
In Assignment 01, `DatabaseManager` in `expense_mate/database.py` executed all raw SQL queries directly:
- `insert_transaction` executed SQL queries and called model validation.
- `get_all_transactions` executed SQL select queries.
- `upsert_budget`, `get_budget`, and `get_budgets_for_month` executed SQL statements directly on SQLite connections.
- Services and managers held direct references to `DatabaseManager`.

## 2. Target State
- `TransactionRepository`: Encapsulates all SQL statements for the `transactions` table (`add`, `get_all`, `get_by_month`, `get_by_filter`).
- `BudgetRepository`: Encapsulates all SQL statements for the `budgets` table (`save`, `get`, `get_for_month`).
- `DatabaseManager`: Owns only SQLite connection management (`get_connection()` context manager) and schema initialization (`_init_schema()`).
- Compatibility wrappers were maintained on `DatabaseManager` to guarantee non-breaking backward compatibility.

## 3. Reason for Migration
1. **Separation of Concerns:** Connection management is separated from query execution.
2. **Security & Parameterization:** All SQL queries are strictly parameterized, eliminating SQL injection vulnerabilities.
3. **Layered Architecture Compliance:** Satisfies Part A and Part B requirements for Assignment 02.

## 4. Risks & Compatibility
- **Risk:** Existing callers expecting `db.get_all_transactions()` or `db.insert_transaction()` could fail.
- **Mitigation:** Compatibility wrappers were implemented on `DatabaseManager` that delegate directly to `TransactionRepository` and `BudgetRepository`.

## 5. Verification
- Verified through `test_repositories.py` (2 unit tests).
- Verified through full regression suite `test_expense_mate.py` (9 tests passing).
- Verified data preservation across schema initialization.
