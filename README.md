# Keeping

![Build](https://img.shields.io/badge/build-passing-brightgreen)
![Coverage](https://img.shields.io/badge/coverage-100%25-brightgreen)
![Python](https://img.shields.io/badge/python-3.12-blue)
![Django](https://img.shields.io/badge/django-5.0-blue)
![License](https://img.shields.io/badge/license-MIT-blue)

**Keeping** is a self-hosted personal finance and life-tracking platform. It allows tracking expenses, incomes, multiple accounts, transfers, savings, books, drinks, and custom counters. Built with Django and fully tested (pytest 100% coverage) for reliability.

### Demo
🔗 [https://stats.unknownbug.net](https://stats.unknownbug.net)  
```
username: demo
password: 9J4wj#^zD0eFwS
```

Keeping unifies personal finance and habit tracking in one system. You can log daily expenses, move funds between accounts, plan savings goals, or maintain side trackers for habits, books, or consumables. The goal is to replace messy spreadsheets with a structured, test-verified web tool.

Features include: track expenses, incomes, and transfers across multiple accounts; maintain custom categories and flexible data models; monitor savings and budget planning; record books read, drinks consumed, or any numeric habit; transactions between accounts with automatic balance updates; fully tested backend with 100% pytest coverage; modular Django architecture easily extendable with new trackers.

### Setting up development
1. Clone the repo
```
git clone https://github.com/nezinomas/keeping.git
```
2. Create `.conf`
```
cp .conf___TEMPLATE .conf
```
3. Define environment parameters in `.conf` [django] section:
```
SECRET_KEY = "django secret key"
SALT = "some password for additional security"
DJANGO_SETTINGS_MODULE = "project.config.settings.develop"
ALLOWED_HOSTS = ["127.0.0.1", "localhost"]
MEDIA_ROOT = "\path\to\media\folder\"
LOG_FILE = "\path\to\log_file.log"
```
4. Define database connection parameters in `.conf` [database] section:
```
NAME = "database name"
USER = "user"
PASSWORD = "password"
ENGINE = "django.db.backends.mysql"
DEFAULT-CHARACTER-SET = "utf8"
CONN_MAX_AGE = 600
```
5. Install development requirements:

Make sure you have **mysql client** and [**uv**](https://docs.astral.sh/uv/getting-started/installation/) python package installed.
```
uv sync --all-extras
```
6. If using Python <3.11, install tomli
```
uv add toml

# change import in manage.py, wsgi.py, base.py
import tomllib as toml > import tomli as toml
```

7. Migrate the database (make sure you have mysql server running)
```
python manage.py migrate
```
8. Create a folder for media uploads if it is not created. Set permissions:
```
mkdir media; chmod -R 755 media
```
9. Run tests:
```
fast: uv run pytest -n auto -k "not webtest"
slow: uv run pytest
```

This project is open-source under the MIT License.

**Author:** Audrius Nznm  
[GitHub](https://github.com/nezinomas) • [Portfolio](https://nezinomas.dev)
