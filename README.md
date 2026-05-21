# Keeping — Collaborative Personal Finance & Life Tracker

![Build](https://img.shields.io/badge/build-passing-brightgreen)
![Coverage](https://img.shields.io/badge/coverage-100%25-brightgreen)
![Python](https://img.shields.io/badge/python-3.13-blue)
![Django](https://img.shields.io/badge/django-6.0-blue)
![License](https://img.shields.io/badge/license-MIT-blue)

**Author:** Audrius Nznm  
**GitHub:** [github.com/nezinomas](https://github.com/nezinomas)  
**Demo:** [stats.unknownbug.net](https://stats.unknownbug.net)  

> [!NOTE]  
> **Demo Credentials:**  
> **Username:** `demo`  
> **Password:** `9J4wj#^zD0eFwS`  

---

## Table of Contents
1. [Project Overview](#project-overview)
2. [Key Architecture & Tech Stack](#key-architecture--tech-stack)
3. [Key Modules Breakdown](#key-modules-breakdown)
4. [Getting Started & Installation](#getting-started--installation)
5. [Testing & Performance Tuning](#testing--performance-tuning)
6. [License](#license)

---

## Project Overview

**Keeping** is a self-hosted, modular web application that combines **collaborative household finance management** with **private personal metrics tracking**. 

Unlike conventional financial trackers, Keeping operates on a dual-privacy model:
*   **Shared Household Finance:** Financial tracking (incomes, expenses, savings, pensions, transactions, plans, and debts) is associated with a shared **Journal**. Multiple users can log into the same journal to cooperatively manage household statistics and plans.
*   **Private Personal Trackers:** Habit and life-tracking metrics (books read, drinks consumed, custom counters) are scoped **per user** and remain private to the individual account, even when sharing a household journal.

---

## Key Architecture & Tech Stack

### Statistics Compiling with Polars
Central reports and charts are powered by **Polars** (high-performance DataFrame library). It handles:
*   Fast time-series padding (filling missing dates with zero values).
*   Dynamic pivot table construction for monthly expense breakdowns.
*   High-performance statistics compilation for graphs and annual summaries.

### Component-Driven Modern Frontend
Keeping provides a Single-Page Application (SPA) feel without the weight of modern JavaScript build chains:
*   **Django Cotton:** Used to build reusable components (e.g., custom form inputs, paginators, progress bars, and modals) directly in Django templates.
*   **HTMX:** Handles seamless, asynchronous HTML swapping for tables, search queries, and form actions.
*   **AlpineJS & Alpine Morph:** Orchestrates micro-interactions and smooth UI state transitions (like inline modal updates).
*   **Custom SASS Design System:** Styled using a custom SASS grid and components (compiled directly to `project/static/css/main.css`).

### Backend & Database
*   **Backend:** Python 3.13, Django 6.0.
*   **Database:** MySQL/MariaDB (production), SQLite in-memory (testing).

---

## Key Modules Breakdown

| Module | Description | Key Models |
|:---|:---|:---|
| **`bookkeeping`** | The central statistics engine. Compiles data from incomes, expenses, savings, and pensions into annual/monthly reports. | `SavingWorth`, `AccountWorth`, `PensionWorth` |
| **`accounts`** | Represents financial accounts (e.g., bank accounts, cash, credit cards) and tracks their current balances. | `Account` |
| **`incomes`** | Track income sources and details. Supports different categories. | `IncomeType`, `Income` |
| **`expenses`** | Log expenses grouped by category types and names. Supports tagging special expenses. | `ExpenseType`, `ExpenseName`, `Expense` |
| **`savings`** | Tracks savings goals, funds, and shares. | `SavingType`, `Saving`, `SavingBalance` |
| **`pensions`** | Track pension funds, contributions, fees, and market value. | `PensionType`, `Pension`, `PensionBalance` |
| **`transactions`** | Manages internal transfers between accounts, saving changes, and saving closures. | `Transaction`, `SavingClose`, `SavingChange` |
| **`debts`** | Logs money borrowed from or lent to other people, including returns. | `Debt`, `DebtReturn` |
| **`plans`** | Set plans and limits for incomes, expenses, savings, and day-to-day budgets. | `IncomePlan`, `ExpensePlan`, `SavingPlan`, `DayPlan` |
| **`books`** | *Private Tracker*: Log books read, reading targets, and personal bookmarks. | `Book`, `BookTarget` |
| **`drinks`** | *Private Tracker*: Track alcohol intake in Standard Average Drinks (Std Av) with daily targets. | `Drink`, `DrinkTarget` |
| **`counts`** | *Private Tracker*: Custom numeric trackers (e.g., pushups, coffee count, custom habits). | `CountType`, `Count` |

---

## Getting Started & Installation

### Prerequisite
*   **Python:** `>= 3.13`
*   **Package Manager:** [uv](https://github.com/astral-sh/uv) (recommended)
*   **Node.js:** (Optional, only needed if you want to compile SASS files)

### 1. Clone the repository
```bash
git clone https://github.com/nezinomas/keeping.git
cd keeping
```

### 2. Configure Environment variables
Create a `.conf` configuration file from the template:
```bash
cp .conf___TEMPLATE .conf
```
Open `.conf` and update the parameters under `[django]` and `[database]`.

### 3. Install Dependencies
Using `uv`:
```bash
uv sync --all-extras
```

### 4. Database Setup & Migrations
Ensure your database (configured in `.conf`) is running, then run migrations:
```bash
python manage.py migrate
```

### 5. Media Folders
Create the media upload directory:
```bash
mkdir media
```

### 6. Stylesheet Compilation (SASS)
If you want to edit stylesheets, navigate to the `sass/` directory, install packages, and start the compiler:
```bash
cd sass
npm install
npx sass sass/main.scss ../project/static/css/main.css --watch
```

### 7. Run the Development Server
```bash
python manage.py runserver
```
Visit the local server at `http://127.0.0.1:8000`.

---

## Testing & Performance Tuning

Keeping maintains a robust test suite with **100% test coverage** for backend logic.

### Why is the test suite so fast?
The testing configuration in [testing.py](project/config/settings/testing.py) is highly optimized:
1.  **In-Memory DB:** Uses SQLite `:memory:` database instead of MySQL.
2.  **No Migrations:** Instructs pytest to skip migration runs via `--nomigrations`.
3.  **Fast Hasher:** Uses `MD5PasswordHasher` instead of Argon2/BCrypt to speed up user creations in tests.
4.  **Parallel Execution:** Leverages `pytest-xdist` to run tests across all CPU cores.

### Running Tests
To run tests locally:

*   **Fast Run** (excludes integration/web tests):
    ```bash
    uv run pytest -n auto -k "not webtest"
    ```
*   **Full Run** (includes web/integration tests):
    ```bash
    uv run pytest
    ```

---

## License

This project is licensed under the [MIT License](LICENSE).  
Author: **Audrius Nznm**
