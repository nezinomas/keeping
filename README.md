# Keeping – Personal Finance & Life Tracker

![Build](https://img.shields.io/badge/build-passing-brightgreen)
![Coverage](https://img.shields.io/badge/coverage-100%25-brightgreen)
![Python](https://img.shields.io/badge/python-3.13-blue)
![Django](https://img.shields.io/badge/django-6.0-blue)
![License](https://img.shields.io/badge/license-MIT-blue)

**Author:** Audrius Nznm
**GitHub:** [github.com/nezinomas](https://github.com/nezinomas)
**Demo:** [https://stats.unknownbug.net](https://stats.unknownbug.net)
```
username: demo
password: 9J4wj#^zD0eFwS
```

---

## **1️⃣ Project Overview**

**Keeping** is a self-hosted web platform for **personal and household finance management** combined with **life tracking**.

- Track **expenses, incomes, transfers, debts, savings, pensions, and plans** collaboratively.
- **Central statistics (`bookkeeping`)** aggregates financial data for reports and dashboards.
- Track **personal metrics** privately (**books, drinks, counters**) per user.
- Designed for **shared household finances**: superuser + other users can manage financial apps together.
- Fully tested backend (**pytest 100% coverage**) and modular Django architecture.

---

## **2️⃣ Key Features**

| Feature | Description |
|---------|-------------|
| Collaborative finance | Superuser + other users manage all financial apps |
| Statistics & dashboards | `bookkeeping` aggregates data across financial apps |
| Private personal trackers | Books, drinks, counters are per-user |
| Accounts & transactions | Multiple accounts, transfers, automatic balance updates |
| Savings & plans | Track goals, budgets, and long-term finances |
| High Performance | Data processing powered by **Polars** |
| Tested | 100% pytest coverage |


---

## **3️⃣ Project Structure**

Keeping follows a clean, modular Django architecture:
- **`bookkeeping`**: The core statistics engine. Aggregates data from all other apps.
- **`accounts`**, **`incomes`**, **`expenses`**, **`savings`**, **`pensions`**, **`transactions`**: Financial management apps.
- **`books`**, **`drinks`**, **`counts`**: Personal life tracking metrics.
- **`plans`**: Budgeting and financial goal setting.
- **`core`**: Shared utilities, base classes, and layout components.

---

## **4️⃣ Technical Stack**

- **Backend:** Python 3.13, Django 6.0
- **Data Processing:** Polars (high-performance DataFrames)
- **Frontend:** HTMX, AlpineJS, SASS (Vanilla CSS/SASS workflow)
- **Database:** MySQL
- **Testing:** Pytest (100% coverage), Selenium (integration tests)
- **Configuration:** `.conf` for environment-specific settings

---

## **5️⃣ Why Keeping is Special**

1. **Engineer-focused:** Modular, reliable, test-covered architecture.
2. **Household collaboration:** All users manage financial data together in a shared journal.
3. **Private personal metrics:** Users maintain their own habits without exposing them to others.
4. **Modern Frontend:** Uses a "No-Build" or "Light-Build" approach with HTMX and AlpineJS for a SPA-like feel without JS complexity.

---

## **6️⃣ Getting Started (Optional)**

1. Clone the repo:
```bash
git clone https://github.com/nezinomas/keeping.git
```

2. Create `.conf` from template:
```bash
cp .conf___TEMPLATE .conf
```

3. Set environment variables in `.conf` ([django] and [database] sections).

4. Install requirements:
```bash
uv sync --all-extras
```

5. Migrate the database:
```bash
python manage.py migrate
```

6. Create media folder:
```bash
mkdir media; chmod -R 755 media
```

7. Run tests:
```bash
fast: uv run pytest -n auto -k "not webtest"
slow: uv run pytest
```

---

**License:** MIT
**Author:** Audrius Nznm
[GitHub](https://github.com/nezinomas)
