#!/bin/bash
echo "Starting BehaviourAI Production Server..."
# Ensure database is initialized
python scripts/init_db.py
# Start gunicorn
gunicorn -c gunicorn.conf.py app:app
