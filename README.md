# Keeping

Setting up development:

1. clone the repo
```
git clone https://github.com/nezinomas/keeping.git
```

2. create `_config_secrets.json`
```
cp _config_secrets.json.TEMPLATE _config_secrets.json
```

3. create `_config_db.cnf` and
```
cp _config_db.cnf.TEMPLATE _config_db.cnf
```

4. Define database connection parameters in `_config_db.cnf`:
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