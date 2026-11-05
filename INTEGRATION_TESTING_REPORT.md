# ExpenseMate Assignment 02: Integration & Regression Testing Report

- **Course:** Software Construction & Development
- **Project:** ExpenseMate — Personal Expense Manager
- **Team Members:**
  - **Member B (Student 2 - Testing & Controller Lead):** Bisma Shahid (24K-3012)
  - **Member A (Student 1 - Database Lead):** Afshal Liaquat (24K-2558)
- **Date:** November 2026

---

## 1. Test Suite Architecture & Overview

To ensure robust software construction, maintainability, and complete absence of regressions, the ExpenseMate test package was organized into four distinct automated test modules:

1. **`test_expense_mate.py` (Regression Suite):** Contains the 9 original Assignment 01 automated tests to verify that baseline features remain functional.
2. **`test_repositories.py` (Repository Unit Tests):** Contains 2 unit tests validating data access and SQLite schema persistence.
3. **`test_services.py` (Services Unit Tests):** Contains 7 unit tests validating individual rewritten services (`TransactionService`, `BudgetService`, `CurrencyService`, `BackupService`, `AnalyticsService`, and `ChartFormatter`).
4. **`test_controller.py` (Controller Unit Tests):** Contains 5 unit tests validating input sanitization, error interception, and action coordination.
5. **`test_integration.py` (Integration Workflow Suite):** Contains **6 comprehensive integration test cases** exercising complete end-to-end user workflows across the 4-tier `Controller → Services → Repository → Database` architecture.

**Overall Test Execution Summary:**
- Total Tests: **29**
- Passing: **29 (100%)**
- Failures / Errors: **0**
- Execution Duration: **~1.2 seconds**

---

## 2. Detailed Integration Test Workflows (6 Test Cases)

Each integration test executes across the entire vertical stack without mocking, proving seamless interoperability between layers.

### Workflow 1: Transaction Lifecycle and Balance Calculation
- **Method:** `test_workflow_1_transaction_lifecycle_and_balance_calculation`
- **Objective:** Verify end-to-end transaction recording, category filtering, and net summary calculation.
- **Layers Exercised:**
  `ExpenseMateController` → `TransactionService` → `TransactionRepository` → `DatabaseManager` (SQLite).
- **Procedure:**
  1. User records income of 85,000 PKR via Controller.
  2. User records expenses of 25,000 PKR (Rent) and 12,000 PKR (Groceries) via Controller.
  3. Controller queries transactions filtered by category (`Rent`).
  4. Controller queries financial net summary for month `2026-10`.
- **Expected Results:** Total income = 85,000, Total expenses = 37,000, Net savings = 48,000, Filtered rent count = 1.
- **Actual Results:** All assertions passed. Returned transaction IDs > 0, exact balance match.
- **Status:** **PASS**

---

### Workflow 2: Budgeting Threshold Alert Escalation
- **Method:** `test_workflow_2_budget_threshold_warning_and_critical_alerts`
- **Objective:** Verify that monthly budget limits trigger accurate `NORMAL`, `WARNING` (>= 80%), and `CRITICAL` (>= 100%) threshold alerts during successive expense logging.
- **Layers Exercised:**
  `ExpenseMateController` → `BudgetService` & `TransactionService` → `BudgetRepository` & `TransactionRepository` → `DatabaseManager` (SQLite).
- **Procedure:**
  1. Set monthly budget of 10,000 PKR for "Dining" in `2026-10`.
  2. Log expense of 5,000 PKR (50% spending).
  3. Log second expense of 3,500 PKR (Cumulative 8,500 PKR = 85% spending).
  4. Log third expense of 2,000 PKR (Cumulative 10,500 PKR = 105% spending).
  5. Fetch all budget statuses for the month.
- **Expected Results:**
  - Expense 1 returns `NORMAL` alert status (50.0%).
  - Expense 2 returns `WARNING` alert status (85.0%).
  - Expense 3 returns `CRITICAL` alert status (105.0%).
- **Actual Results:** All alerts generated with correct levels, spent sums, and formatted messages.
- **Status:** **PASS**

---

### Workflow 3: CSV Data Portability and Cross-Database Migration
- **Method:** `test_workflow_3_csv_export_import_data_integrity`
- **Objective:** Verify end-to-end export from an existing database and seamless import into an uninitialized fresh database.
- **Layers Exercised:**
  `ExpenseMateController` → `DataPortabilityManager` → `TransactionRepository` → `DatabaseManager` (SQLite).
- **Procedure:**
  1. Insert 3 distinct transactions in Database A.
  2. Export Database A transactions to temporary CSV file via Controller.
  3. Initialize a fresh, empty Database B.
  4. Import CSV into Database B via Controller.
  5. Compare transaction records, amounts, and net financial summaries between both databases.
- **Expected Results:** 3 records exported, 3 records successfully imported, 0 errors, net summary matches identically.
- **Actual Results:** Export count = 3, Import success = 3, Errors = 0. Records and balances matched 100%.
- **Status:** **PASS**

---

### Workflow 4: Financial Analytics Breakdown and ASCII Chart Rendering
- **Method:** `test_workflow_4_analytics_breakdown_and_ascii_chart_rendering`
- **Objective:** Verify multi-month trends aggregation, category breakdown, and ASCII visual chart rendering.
- **Layers Exercised:**
  `ExpenseMateController` → `AnalyticsService` & `ChartFormatter` → `TransactionRepository` → `DatabaseManager` (SQLite).
- **Procedure:**
  1. Insert transactions across August (`2026-08`) and September (`2026-09`).
  2. Request category analytics for `2026-09`.
  3. Request monthly trends across all time.
  4. Verify data breakdown dictionary and generated ASCII bar chart string.
- **Expected Results:**
  - September breakdown: Food = 8,000 (40.0%), Shopping = 12,000 (60.0%).
  - ASCII chart contains labels, correct percentage calculations, and Unicode block bars (`█`).
  - Monthly trends contains August savings (35,000) and September savings (40,000).
- **Actual Results:** Breakdown and ASCII bar charts matched exact specifications.
- **Status:** **PASS**

---

### Workflow 5: Multi-Currency Conversion and Budget Integration
- **Method:** `test_workflow_5_multi_currency_conversion_and_budget_integration`
- **Objective:** Verify conversion calculations across all supported currencies (PKR, USD, EUR, GBP, AED, SAR) and transaction persistence.
- **Layers Exercised:**
  `ExpenseMateController` → `CurrencyService` & `TransactionService` → `TransactionRepository` → `DatabaseManager` (SQLite).
- **Procedure:**
  1. Convert 50.0 USD to base currency PKR via Controller.
  2. Log converted expense into the database with foreign description note.
  3. Convert PKR equivalent back to USD to verify bidirectional conversion fidelity.
  4. Convert non-base currency cross-pair (EUR to GBP).
- **Expected Results:** USD to PKR converts accurately (~13,888.89 PKR), bidirectional roundtrip error < 0.5 delta, cross-rate calculation positive and non-zero.
- **Actual Results:** All conversion rates verified to 2 decimal places. Converted expense persisted properly.
- **Status:** **PASS**

---

### Workflow 6: Controller Input Sanitization and Error Defense
- **Method:** `test_workflow_6_controller_validation_and_defense_against_corrupted_data`
- **Objective:** Verify that the Controller boundary catches and rejects malformed inputs before reaching services or the database, protecting data integrity.
- **Layers Exercised:**
  `ExpenseMateController` (Validation Defense) → System Boundary Protection.
- **Procedure:**
  1. Attempt to add transaction with negative amount (`-100.0`).
  2. Attempt to add transaction with empty category (`"   "`).
  3. Attempt to add transaction with invalid type (`"investment"`).
  4. Attempt to add transaction with non-ISO date (`"10/10/2026"`).
  5. Attempt to set negative monthly budget (`-500.0`).
  6. Inspect database transaction count before and after invalid attempts.
- **Expected Results:** Each invalid operation raises a descriptive `ValueError`. Zero records inserted into database.
- **Actual Results:** All 5 invalid payloads intercepted with clear error messages. Database remained pristine.
- **Status:** **PASS**

---

## 3. Regression Testing Evidence

The original 9 tests in `test_expense_mate.py` were run against the refactored architecture without modification:

```text
test_analytics_breakdown ..................................................... OK
test_budget_threshold_alerts ................................................. OK
test_csv_export_and_import ................................................... OK
test_currency_conversion ..................................................... OK
test_insert_and_get_all_transactions .......................................... OK
test_net_summary_calculation ................................................. OK
test_transaction_validation_invalid_date ..................................... OK
test_transaction_validation_negative_amount ................................... OK
test_transaction_validation_valid ............................................. OK
test_budget_repository_updates_existing_monthly_budget ....................... OK
test_transaction_repository_preserves_records ................................ OK
----------------------------------------------------------------------
Ran 11 tests in 0.469s - OK
```

**Conclusion:** All existing Assignment 01 features and contracts remain 100% functional. Backward compatibility is completely preserved.

---

## 4. Defect Log & Corrective Action

| Defect ID | Severity | Component | Description | Resolution | Status |
|---|---|---|---|---|---|
| **DEF-01** | Low | `BudgetService.check_budget_status` | Floating-point IEEE 754 precision caused `110.00000000000001` instead of `110.0` when calculating percentage. | Applied `round(percentage, 2)` to normalize threshold percentage results. | **RESOLVED** |
| **DEF-02** | Medium | `DataPortabilityManager` | Direct coupling to `DatabaseManager` bypassed the repository layer. | Refactored `DataPortabilityManager` constructor to accept and use `TransactionRepository`. | **RESOLVED** |
