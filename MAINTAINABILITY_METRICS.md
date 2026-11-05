# ExpenseMate Assignment 02: Maintainability Metrics Report
**Quantitative & Qualitative Before/After Software Quality Analysis**

- **Course:** Software Construction & Development
- **Project:** ExpenseMate — Personal Expense Manager
- **Team Members:**
  - **Member B (Student 2 - Metrics & Refactoring Lead):** Bisma Shahid (24K-3012)
  - **Member A (Student 1 - Migration Lead):** Afshal Liaquat (24K-2558)
- **Date:** November 2026

---

## 1. Measurement Methodology

To ensure objective and reproducible evaluation, all maintainability metrics were computed using static analysis tools and Python's standard `ast` (Abstract Syntax Tree) module:

- **Cyclomatic Complexity (CC):** Calculated using McCabe’s formula:
  $$CC = \text{Decision Points} + 1$$
  where decision points include conditional branches (`if`, `elif`), loops (`while`, `for`), exception handlers (`except`), context handlers (`with`), boolean operators (`and`, `or`), and assertions (`assert`).
- **Source Lines of Code (SLOC):** Physical lines of code excluding blank lines and standalone comments (`#`).
- **Coupling & Layering:** Count of concrete cross-tier import dependencies.
- **Test Coverage & Verification:** Ratio of functional assertions and automated test scenarios.

---

## 2. Metric 1: Cyclomatic Complexity Comparison

Cyclomatic complexity measures the number of linearly independent paths through a program's source code. A complexity exceeding 15 indicates high defect risk and poor testability.

### 2.1 Major Methods Comparison Table

| Module / File | Method / Function | Baseline CC (A01) | Refactored CC (A02) | Complexity Reduction | Risk Assessment |
|---|---|:---:|:---:|:---:|---|
| `cli.py` | `ExpenseMateCLI.run()` | **58** | **7** | **-87.9%** | Reduced from **High Risk** to **Low Risk** |
| `cli.py` | `validate_transaction_data()` | **9** | **1** (delegated) | **-88.9%** | Centralized in Controller |
| `cli.py` | `validate_currency_data()` | **8** | **1** (delegated) | **-87.5%** | Centralized in Controller |
| `cli.py` | `_handle_add_transaction()` | *N/A (embedded)* | **14** | *Modularized* | Low/Moderate isolated handler |
| `cli.py` | `_handle_manage_budgets()` | *N/A (embedded)* | **12** | *Modularized* | Low/Moderate isolated handler |
| `controllers.py` | `ExpenseMateController.add_transaction()` | *N/A (new)* | **2** | *Minimal* | High testability |
| `controllers.py` | `ExpenseMateController.set_budget()` | *N/A (new)* | **3** | *Minimal* | High testability |
| `controllers.py` | `validate_transaction_data()` | *N/A (new)* | **9** | *Standard* | Comprehensive validation |
| `services.py` | `BudgetService.check_budget_status()` | **5** | **5** | **0%** | Maintained clean decision logic |
| `services.py` | `TransactionService.add_transaction()` | **1** | **1** | **0%** | Pure delegation to repository |
| `analytics.py` | `AnalyticsService.get_monthly_trends()` | **6** | **6** | **0%** | Preserved trend aggregation |
| `analytics.py` | `ChartFormatter.generate_ascii_bar_chart()` | **5** | **5** | **0%** | Isolated presentation method |

**Key Finding:** The single biggest maintainability flaw in Assignment 01 was `ExpenseMateCLI.run()` with a CC of **58**. Decomposing `run()` into an action dispatcher and isolated handler methods reduced its complexity to **7**, making each option independently maintainable and readable.

---

## 3. Metric 2: Separation of Responsibilities & Cohesion (SRP)

Cohesion evaluates whether the responsibilities of a module form a single, focused purpose.

| Class | Baseline Responsibilities (A01) | Refactored Responsibilities (A02) | Structural Benefit |
|---|---|---|---|
| **`ExpenseService`** | **7 Mixed Responsibilities:**<br>1. Transactions<br>2. Filter queries<br>3. Financial net summaries<br>4. Budget persistence<br>5. Budget threshold alerts<br>6. Multi-currency math<br>7. Filesystem DB backup | **Decomposed into 4 Cohesive Services:**<br>• `TransactionService` (1 responsibility)<br>• `BudgetService` (1 responsibility)<br>• `CurrencyService` (1 responsibility)<br>• `BackupService` (1 responsibility)<br>• `ExpenseService` (Facade adapter) | High cohesion, zero filesystem coupling in financial logic, isolated unit testability. |
| **`AnalyticsEngine`** | **2 Mixed Responsibilities:**<br>1. Business aggregation<br>2. ASCII chart character formatting | **Decomposed into 2 Cohesive Components:**<br>• `AnalyticsService` (Pure computation)<br>• `ChartFormatter` (Pure visual formatting) | Separation of domain logic from visual console rendering. Easily extensible to GUI/Web/JSON. |
| **`ExpenseMateCLI`** | **3 Mixed Responsibilities:**<br>1. Console I/O & formatting<br>2. Parameter validation<br>3. Workflow orchestration | **Clean Separation:**<br>• `ExpenseMateCLI` (Pure Console View)<br>• `ExpenseMateController` (Validation & Coordination) | Clear boundary between UI presentation and application control. |

---

## 4. Metric 3: Architectural Layering & Dependency Separation

In Assignment 01, several modules directly instantiated or queried `DatabaseManager`, violating separation of concerns and preventing dependency injection.

### Dependency Direction Matrix

| Caller Layer | Allowed Callee Layer | Baseline Violations (A01) | Assignment 02 Status |
|---|---|---|---|
| **Presentation (CLI)** | Controller only | Direct calls to Services & DatabaseManager | **ELIMINATED** (CLI calls Controller only) |
| **Controller** | Services only | N/A (Controller did not exist) | **ENFORCED** (Controller delegates to Services) |
| **Services** | Repositories only | Services directly called DatabaseManager & raw DB paths | **ENFORCED** (Services call Repositories only) |
| **Repositories** | Database only | N/A (Repositories did not exist) | **ENFORCED** (All SQL isolated in Repositories) |
| **Database** | SQLite only | DatabaseManager mixed SQL, DDL, and model validation | **ENFORCED** (DatabaseManager handles schema & context) |

---

## 5. Metric 4: Source Lines of Code (SLOC) & Distribution

| Layer / Component | Baseline SLOC (A01) | Refactored SLOC (A02) | Distribution Explanation |
|---|:---:|:---:|---|
| **Models** (`models.py`) | 45 | 45 | Domain entities preserved. |
| **Data Access** (`database.py` + `repositories.py`) | 120 | 208 | Extracted `TransactionRepository` and `BudgetRepository`. |
| **Services** (`services.py`) | 110 | 250 | Decomposed into 4 modular services + backward-compatible facade. |
| **Analytics & Presentation** (`analytics.py`) | 80 | 103 | Separated `AnalyticsService` and `ChartFormatter`. |
| **Controller** (`controllers.py`) | 0 | 233 | Centralized validation, action handlers, and DTO coordination. |
| **CLI / View** (`cli.py`) | 390 | 254 | Removed validation and service logic; streamlined to view handlers. |
| **Data Portability** (`importer_exporter.py`) | 80 | 87 | Refactored to use repository data access. |
| **TOTAL PRODUCTION SLOC** | **~825** | **~1,180** | +355 SLOC of clean abstractions, type hints, and decoupled layers. |

Although total SLOC increased by ~355 lines, this expansion reflects professional architectural decomposition: explicit interfaces, comprehensive docstrings, modular error handling, and dedicated controller abstractions.

---

## 6. Metric 5: Test Verification & Coverage Expansion

| Test Metric | Assignment 01 Baseline | Assignment 02 Refactored | Improvement |
|---|:---:|:---:|:---:|
| **Total Test Files** | 1 (`test_expense_mate.py`) | **5** (`test_expense_mate`, `test_repositories`, `test_services`, `test_controller`, `test_integration`) | **+400%** |
| **Total Automated Tests** | 9 | **29** | **+222%** |
| **Unit Tests** | 5 | **18** | **+260%** |
| **End-to-End Integration Workflows** | 4 | **11** (5 existing + 6 comprehensive workflows) | **+175%** |
| **Test Pass Rate** | 100% (9/9) | **100% (29/29)** | **Zero Regressions** |

---

## 7. Conclusion

The empirical evidence confirms that the refactoring and class rewriting executed for Assignment 02 yielded dramatic improvements in maintainability:
1. Cyclomatic complexity of the main loop plummeted by **88%** (from 58 to 7).
2. The God class `ExpenseService` was eliminated in favor of 4 single-responsibility services.
3. Domain calculations are completely decoupled from terminal presentation and SQLite persistence.
4. Test suite capacity grew from 9 tests to 29 tests, proving zero regressions and full backward compatibility.
