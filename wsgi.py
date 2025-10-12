"""
WSGI configuration for Goal Tracker on PythonAnywhere
"""

import sys
import os

# Add your project directory to the sys.path
path = '/home/yourusername/myGoalTracker'  # Update with your actual username
if path not in sys.path:
    sys.path.insert(0, path)

# Set environment variables
os.environ['FLASK_ENV'] = 'production'
os.environ.setdefault('SECRET_KEY', 'your-production-secret-key-change-this')

from app import create_app

application = create_app()

if __name__ == "__main__":
    application.run()