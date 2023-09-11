# Keeping


### Demo

https://stats.unknownbug.net
```
username: demo
password: 9J4wj#^zD0eFwS
```

***

#### Setting up development:

1. Clone the repo
```
git clone https://github.com/nezinomas/keeping.git
```

2. Create `.conf`
```
cp .conf___TEMPLATE .conf
```

3. Define enviroment parameters in `.conf` [django] section:
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

5. Install development requirements (make sure you have mysql client installed)
```
pip install -r requirements/develop.txt
```

6. If you are using python version lower than 3.11 you must install tomli
```
pip install toml

change import in files manage.py, wsgi.py, base.py

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
_fast:_ pytest -n auto -k "not webtest"
_slow:_ pytest
```
