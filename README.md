# Admin-Web-Form
Simple web-form for system administrators or support engineers.
Sends form data via email and writes one to the DB Sqlite.

## Requirements
- Python3.6 or beyond installed
- Nginx installed
- Git installed (optional)

## Installation and configuration
1. Download the repository to your webroot directory e.g. /var/www
```
cd /var/www
git clone https://github.com/Dionis-90/admin-web-form.git
```

2. Copy and rename files
- db.db.structure db.sqlite (or other name)
- form.conf.default to form.conf (or other name)
- settings_example.py to settings.py

3. Open your settings.py and check email settings and paths.
4. Create Nginx virtual host config e.g.:
```
server {
        listen 80;
        server_name  form.example.com ;
        root /var/www/admin-web-form/;
        index  index.html;
        location / {
                proxy_pass http://localhost:8080;
                proxy_http_version 1.1;
                proxy_read_timeout 60;
                proxy_connect_timeout 5;
        }

}
```
and restart Nginx
```nginx -t && service nginx reload```

5. Install requirements:
```pip3 install cherrypy```

6. Run application e.g.:
```python3 form.py &```
