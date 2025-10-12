"""
WSGI configuration for Study Momentum Application
Can be used for both local development and production deployment
"""

import sys
import os

# Production environment detection
is_production = os.environ.get('FLASK_ENV') == 'production' or 'PYTHONANYWHERE_DOMAIN' in os.environ

if is_production:
    # Production settings
    os.environ['FLASK_ENV'] = 'production'
    os.environ.setdefault('SECRET_KEY', os.environ.get('SECRET_KEY', 'change-this-in-production'))

from app import create_app

# Create the Flask application instance
application = create_app()

# For local development
if __name__ == "__main__":
    application.run(debug=not is_production, host='0.0.0.0', port=5000)