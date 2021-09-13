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

3. Install development requirements (make sure you have mysql client installed)
```
pip install -r requirements/develop.txt
```

4. Migrate the database (make sure you have mysql server running)
```
python manage.py migrate
```

5. Create a folder for media uploads:
```
mkdir media; chmod -R 755 media 
```

6. Tell the project to use that folder in `base.py` (around line 45):
```
# ================   MEDIA CONFIGURATION
MEDIA_ROOT = os.path.join(PROJECT_ROOT, 'media/')
MEDIA_URL = "/media/"
```
