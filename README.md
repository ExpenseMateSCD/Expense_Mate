# ExpenseMate

ExpenseMate is a personal finance manager for recording income and expenses, tracking monthly budgets, and reviewing spending. This repository's `assignment-02` branch contains version 2, which adds a desktop GUI and refactors the application into controllers, services, and repositories while retaining a command-line interface.

## Features

- Record and browse income and expense transactions.
- Review monthly income, expenses, and net savings.
- Set category budgets and view budget status alerts.
- Explore spending by category and monthly trends.
- Import and export transactions as CSV.
- Convert between supported currencies.
- Back up the SQLite database.
- Use the application through either the desktop GUI or interactive CLI.

## Requirements

- Python 3
- Tkinter for the desktop GUI (usually included with Python; some Linux distributions package it separately)

The application uses Python's standard library and SQLite; no third-party packages are required.

## Run

From the repository root, start the desktop application:

```powershell
python -m expense_mate.main
```

To start the command-line interface instead:

```powershell
python -m expense_mate.main --cli
```

The application creates `expense_mate.db` in the current working directory when it first needs a database.

## Tests

Run the test suite from the repository root:

```powershell
python -m unittest discover -v
```

## Project layout

- `expense_mate/` — application models, database, repositories, services, controllers, analytics, GUI, and CLI.
- `test_*.py` — unit and integration tests.
- `project_csv.csv` — sample transaction data.
- `Migration_Report.pdf` — assignment migration report.
