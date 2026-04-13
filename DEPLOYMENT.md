# Deployment Guide

## Local
On Windows, run `run.bat` to bootstrap Python, install dependencies, initialize the database, and start the app.
On macOS/Linux, you can still use `python app.py` directly.

## Production
We recommend `gunicorn` for serving the application.
```bash
# Linux / macOS
bash scripts/run.sh

# Windows (use a WSGI server such as Waitress or IIS integration)
```
Nginx configuration is available under `nginx/nginx.conf`. Ensure you adjust paths inside `nginx.conf` properly before symlinking into `/etc/nginx/sites-enabled`.
