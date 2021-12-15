# Keeping

Setting up development:

1. Clone the repo
```
git clone https://github.com/nezinomas/keeping.git
```

2. Create `.env`
```
cp .env___TEMPLATE .env
```

3. Create `.db` and
```
cp .db___TEMPLATE .db
```

4. Define database connection parameters in `.db`:
```
# my.cnf
[client]
database = DB
user = USER
password = PASSWORD
default-character-set = utf8
CONN_MAX_AGE = 60 * 10
```

5. Install development requirements (make sure you have mysql client installed)
```
pip install -r requirements/develop.txt
```

6. Migrate the database (make sure you have mysql server running)
```
python manage.py migrate
```

7. Create a folder for media uploads:
```
mkdir media; chmod -R 755 media 
```

8. Tell the project to use that folder in `base.py` (around line 45):
```
# ================   MEDIA CONFIGURATION
MEDIA_ROOT = os.path.join(PROJECT_ROOT, 'media/')
MEDIA_URL = "/media/"
```
