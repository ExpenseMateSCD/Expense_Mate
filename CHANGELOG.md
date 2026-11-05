# Changelog

## 2026-11-05

### Assignment 01 baseline

- **Commit:** `1c6daf5e6a2066a19bfaf48c61b3b944b148fb4d`
- **Files:** Existing ExpenseMate source, tests, sample CSV, and baseline report in this folder.
- **Change type:** Baseline snapshot.
- **Reason:** Preserve the available Assignment 01 project state before continuing Assignment 02 work.
- **Student:** Afshal Liaquat (24K-2558)
- **Note:** The supplied folder did not contain Git metadata, so the original Assignment 01 commit and tag could not be recovered. The replacement baseline is tagged `assignment-01-baseline`.

### Assignment 02 preparation (Part A: Database & Repository Migration)

- **Commit:** `5ab2780889a53f3c7ee285b454af4676ca384ed3`
- **Files:** `migrations/001_repository_layer.md`, `expense_mate/repositories.py`, `expense_mate/database.py`, `test_repositories.py`, and this changelog.
- **Change type:** Migration / Data Access Layer.
- **Reason:** Track the repository-layer migration and its verification while preserving compatibility with the Assignment 01 API.
- **Student:** Afshal Liaquat (24K-2558)

## 2026-11-06

### Assignment 02 Part B & C: Services & Analytics Rewriting

- **Commit:** `8f21bc9e472019a32c64db5021a892b130e5f291`
- **Files:** `expense_mate/services.py`, `expense_mate/analytics.py`, `test_services.py`
- **Change type:** Class Rewriting / Separation of Concerns.
- **Reason:** Decompose `ExpenseService` (which violated SRP with 7+ responsibilities) into `TransactionService`, `BudgetService`, `CurrencyService`, and `BackupService`. Decompose `AnalyticsEngine` into `AnalyticsService` (computations) and `ChartFormatter` (ASCII rendering). Provide backward-compatible facade wrappers for legacy calls.
- **Student:** Bisma Shahid (24K-3012)

### Assignment 02 Part B: Controller Layer & Layered Refactoring

- **Commit:** `9d37aa4b1829e01f6812cb4012c771e352f1a602`
- **Files:** `expense_mate/controllers.py`, `expense_mate/cli.py`, `expense_mate/importer_exporter.py`, `expense_mate/__init__.py`, `test_controller.py`
- **Change type:** Architectural Refactoring.
- **Reason:** Refactor the system into the strict `Controller -> Services -> Repository -> Database` architecture. Created `ExpenseMateController` to mediate between CLI and services and centralize input validation. Refactored `ExpenseMateCLI` to be a pure presentation/view layer, reducing `run()` cyclomatic complexity from 58 to 7. Refactored `DataPortabilityManager` to use `TransactionRepository`.
- **Student:** Bisma Shahid (24K-3012)

### Assignment 02 Testing & Verification: Integration Workflows & Reports

- **Commit:** `b412ce8902d159f81467e2a91280fc4971c20e14`
- **Files:** `test_integration.py`, `REFACTORING_REPORT.md`, `CLASS_REWRITING_REPORT.md`, `INTEGRATION_TESTING_REPORT.md`, `MAINTAINABILITY_METRICS.md`, `FINAL_REPORT_ASSIGNMENT_02.md`
- **Change type:** Testing & Documentation.
- **Reason:** Added 6 end-to-end integration test workflows covering transaction lifecycles, budgeting alerts, CSV data portability, analytics/ASCII charts, multi-currency conversion, and input validation protection. Prepared detailed refactoring, rewriting, maintainability, and final reports.
- **Student:** Bisma Shahid (24K-3012) & Afshal Liaquat (24K-2558)
