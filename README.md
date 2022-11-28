# Keeping


### Demo

https://stats.unknownbug.net
username: *demo*
password: *9J4wj#^zD0eFwS*

***

#### Setting up development:

1. Clone the repo
```
git clone https://github.com/nezinomas/keeping.git
```

2. Create `.env`
```
cp .env___TEMPLATE .env
```

3. Define enviroment parameters in `.env`:
```
SECRET_KEY=django_secrect_key
SALT=some_password_for_additional_security
MEDIA_ROOT="\PATH\TO\MEDIA_FOLDER\"
ALLOWED_HOSTS=127.0.0.1,localhost
DJANGO_SETTINGS_MODULE=project.config.settings.develop
```

4. Create `.db`
```
cp .db___TEMPLATE .db
```

5. Define database connection parameters in `.db`:
```
# my.cnf
[client]
database = DB
user = USER
password = PASSWORD
default-character-set = utf8
CONN_MAX_AGE = 60 * 10
```

6. Install development requirements (make sure you have mysql client installed)
```
pip install -r requirements/develop.txt
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
pytest -n auto -k "not webtest"
```
