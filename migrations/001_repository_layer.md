# Migration 001: Introduce the Repository Layer

## Before state

Assignment 01 placed SQL CRUD methods in `DatabaseManager`. Services and the
CSV portability module called those methods directly, so database access and
domain operations were coupled.

## Target state

`DatabaseManager` owns the SQLite connection and schema lifecycle. The new
`TransactionRepository` and `BudgetRepository` own SQL queries and convert
database rows into domain models:

```text
Services -> Repositories -> DatabaseManager -> SQLite database
```

The old `DatabaseManager` CRUD methods remain as compatibility wrappers during
the transition. They delegate to repositories so existing Assignment 01
callers continue to work while services are migrated.

## Procedure

1. Keep the existing SQLite file and run the application once. The existing
   schema is retained by `CREATE TABLE IF NOT EXISTS`.
2. Add `expense_mate/repositories.py`.
3. Instantiate `TransactionRepository` and `BudgetRepository` with the
   existing `DatabaseManager`.
4. Verify existing rows with `get_all()` and `get_by_month()`.
5. Verify budgets with `get()` and `get_for_month()`.
6. Update services to depend on repositories in the next refactoring step.

No destructive SQL or data-copy operation is required. Existing records remain
in the same `transactions` and `budgets` tables.

## Risks and compatibility

- Services that still call the old methods continue to work through wrappers.
- New repository methods use parameterized SQL, preserving the existing input
  safety behavior.
- The `date LIKE 'YYYY-MM-%'` query assumes the existing ISO date format,
  which is already enforced by `Transaction.validate()`.

## Verification

Run:

```text
python -m unittest test_repositories.py test_expense_mate.py
```

The repository tests verify transaction preservation and budget upsert
behavior. The existing suite verifies Assignment 01 workflows through the
compatibility wrappers.
