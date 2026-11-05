# ExpenseMate Assignment 02: Class Rewriting Report
**Detailed Analysis & Verification of Rewritten Classes**

- **Course:** Software Construction & Development
- **Project:** ExpenseMate — Personal Expense Manager
- **Student Author:** Bisma Shahid (24K-3012) — Student 2: Refactoring & Class Rewriting Lead
- **Collaborator:** Afshal Liaquat (24K-2558) — Student 1: Database & Migration Lead
- **Date:** November 2026

---

## 1. Overview of Class Rewriting

Assignment 02 mandates selecting and rewriting at least two existing classes that exhibit severe design or maintenance issues. Rewriting entails fundamentally redesigning and replacing the class implementation with a modular, cohesive, and extensible design while fully preserving required public behaviour and system integration.

The two primary classes selected and rewritten are:
1. **`ExpenseService`** (in `expense_mate/services.py`)
2. **`AnalyticsEngine`** (in `expense_mate/analytics.py`)

In addition, **`ExpenseMateCLI`** was restructured to extract the new **`ExpenseMateController`** (`expense_mate/controllers.py`).

---

## 2. Rewritten Class 1: `ExpenseService`

### 2.1 Baseline State & Original Responsibilities
In Assignment 01, `ExpenseService` served as an all-encompassing "God Class" that accumulated every backend function:
1. Transaction persistence orchestration (`add_transaction`).
2. In-memory transaction filtering by type and category (`list_transactions`).
3. Monthly financial balance calculation (`get_net_summary`).
4. Category monthly budget setting (`set_budget`).
5. Budget threshold alerting and percentage calculations (`check_budget_status`, `get_all_budget_statuses`).
6. Foreign currency conversion logic with hardcoded constants (`convert_amount`).
7. Filesystem manipulation and database file snapshotting (`create_database_backup`).

### 2.2 Problems in Baseline Design
- **Severe Violation of Single Responsibility Principle (SRP):** The class had 7 distinct reasons to change. A change in currency exchange rates, a change in database backup directory naming, or a change in budget alert thresholds all modified the exact same class.
- **Tight Coupling to Persistence & Operating System:** `ExpenseService` imported `os`, `shutil`, `DatabaseManager`, and domain models, combining low-level filesystem I/O with high-level financial business logic.
- **Untestable in Isolation:** Testing pure arithmetic (such as currency conversion) required creating a temporary SQLite database connection because the constructor required `DatabaseManager`.
- **Inefficient In-Memory Processing:** In `check_budget_status()`, the service repeatedly called `self.db.get_all_transactions()` and filtered every row in Python memory rather than querying the relevant monthly records.

### 2.3 Why a Full Rewrite Was Chosen Over a Small Refactor
A minor refactoring (such as renaming methods or extracting private helper functions) would have left all 7 responsibilities inside the same monolithic class, preserving the high coupling and untestable architecture. A complete architectural rewrite was necessary to decompose the class into discrete, single-purpose services that adhere to SOLID principles and depend only on repository abstractions.

### 2.4 New Architecture & Class Design
`ExpenseService` was rewritten by decomposing it into four highly cohesive classes:

1. **`TransactionService`:**
   - **Responsibility:** Transaction creation, filtered queries, and net financial summaries.
   - **Dependency:** `TransactionRepository`.
2. **`BudgetService`:**
   - **Responsibility:** Budget definitions, monthly spending tracking, and threshold alert evaluation (`NORMAL`, `WARNING` at 80%, `CRITICAL` at 100%).
   - **Dependencies:** `BudgetRepository` and `TransactionRepository`.
3. **`CurrencyService`:**
   - **Responsibility:** Multi-currency mathematical conversions between PKR, USD, EUR, GBP, AED, and SAR.
   - **Dependencies:** None (Pure domain calculation service).
4. **`BackupService`:**
   - **Responsibility:** Safe snapshotting and timestamping of SQLite database files.
   - **Dependencies:** Filesystem I/O (`os`, `shutil`).
5. **`ExpenseService` (Facade Wrapper):**
   - Retained as a composite facade that delegates incoming calls to the specialized services above, guaranteeing **100% backward compatibility** with Assignment 01 tests and callers.

### 2.5 Behaviour Preservation & Compatibility
All method signatures (`add_transaction`, `list_transactions`, `get_net_summary`, `set_budget`, `check_budget_status`, `get_all_budget_statuses`, `convert_amount`, `create_database_backup`) and return types remain identical to Assignment 01. Existing unit tests run without modification and pass completely.

---

## 3. Rewritten Class 2: `AnalyticsEngine`

### 3.1 Baseline State & Original Responsibilities
In Assignment 01, `AnalyticsEngine` performed both business intelligence calculations and terminal user interface rendering:
1. Category-wise expense breakdown computation (`get_category_breakdown`).
2. Multi-month trends aggregation (`get_monthly_trends`).
3. Text-based ASCII bar chart rendering with Unicode block characters (`generate_ascii_bar_chart`).

### 3.2 Problems in Baseline Design
- **Conflation of Business Logic and Presentation:** The class calculated financial percentages while simultaneously determining character cell widths, bar padding, and terminal string formatting.
- **Direct Database Dependency:** The class directly invoked `self.db.get_all_transactions()`, tightly coupling analytical algorithms to concrete database access.
- **Violation of Open/Closed Principle:** Introducing a new presentation format (e.g., HTML or JSON) required modifying the analytical engine itself.

### 3.3 Why a Full Rewrite Was Chosen Over a Small Refactor
Extracting small helper methods within `AnalyticsEngine` would not resolve the architectural flaw of mixing presentation with analytical data aggregation. A full rewrite cleanly decoupled the computational engine from visual formatting.

### 3.4 New Architecture & Class Design
`AnalyticsEngine` was rewritten and decomposed into two clean components:

1. **`AnalyticsService` (`expense_mate/analytics.py`):**
   - **Responsibility:** Pure business analytics and aggregation.
   - **Methods:** `get_category_breakdown(trans_type, month_year)` and `get_monthly_trends()`.
   - **Dependencies:** `TransactionRepository` (decoupled from concrete database connections).
2. **`ChartFormatter` (`expense_mate/analytics.py`):**
   - **Responsibility:** Pure visual formatting.
   - **Methods:** `generate_ascii_bar_chart(data, title, max_bar_width)` (stateless static method).
   - **Dependencies:** None. Operates purely on generic numeric dictionaries.
3. **`AnalyticsEngine` (Facade Wrapper):**
   - Maintained as a backward-compatible adapter delegating to `AnalyticsService` and `ChartFormatter`.

### 3.5 Behaviour Preservation & Compatibility
The generated ASCII bar charts, percentage calculations, dictionary formats, and headers remain identical to Assignment 01. All tests asserting on breakdown keys, values, and chart string representations pass without modification.

---

## 4. Verification & Testing Evidence

Both rewritten classes were verified through multiple test layers:

1. **Regression Testing (`test_expense_mate.py`):**
   - `test_analytics_breakdown`: Passes (100% data fidelity).
   - `test_budget_threshold_alerts`: Passes (Alert levels verified).
   - `test_currency_conversion`: Passes (Conversions verified).
   - `test_insert_and_get_all_transactions`: Passes.
2. **Dedicated Unit Tests (`test_services.py`):**
   - 7 unit tests specifically exercising `TransactionService`, `BudgetService`, `CurrencyService`, `BackupService`, `AnalyticsService`, and `ChartFormatter`.
3. **End-to-End Integration Tests (`test_integration.py`):**
   - 6 integration workflows verifying that rewritten services seamlessly integrate with the Controller, Repository, and Database layers.

| Test Class | File | Target | Results |
|---|---|---|---|
| `TestExpenseMate` | `test_expense_mate.py` | Legacy Compatibility / Regression | **9 Passed / 0 Failed** |
| `TestServices` | `test_services.py` | Rewritten Services Unit Tests | **7 Passed / 0 Failed** |
| `TestExpenseMateController` | `test_controller.py` | Controller Layer Unit Tests | **5 Passed / 0 Failed** |
| `TestExpenseMateIntegrationWorkflows` | `test_integration.py` | Multi-tier Integration Workflows | **6 Passed / 0 Failed** |
| `TestRepositories` | `test_repositories.py` | Repository Unit Tests | **2 Passed / 0 Failed** |
| **TOTAL** | **5 Test Suites** | **Complete System** | **29 Passed / 0 Failed** |
