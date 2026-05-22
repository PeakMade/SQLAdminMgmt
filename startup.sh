# Azure App Service Startup Script
# This file tells Azure how to start your Python application

gunicorn --bind=0.0.0.0:8000 --workers=4 --timeout=120 app:app
