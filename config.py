import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'goal_tracker.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = None
    
    # Flask-Login configurations for persistent login (Android-style)
    REMEMBER_COOKIE_DURATION = 30 * 24 * 60 * 60  # 30 days in seconds
    REMEMBER_COOKIE_SECURE = False  # Set to True in production with HTTPS
    REMEMBER_COOKIE_HTTPONLY = True  # Prevent XSS attacks
    SESSION_PROTECTION = 'strong'  # Protect against session hijacking
    PERMANENT_SESSION_LIFETIME = 30 * 24 * 60 * 60  # 30 days for regular sessions too
    
    # App specific settings
    ITEMS_PER_PAGE = 10
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file upload

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False
    # PythonAnywhere specific settings
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-production-secret-key-here'
    # Enable secure cookies in production
    REMEMBER_COOKIE_SECURE = True
    # Use MySQL on PythonAnywhere if needed
    # SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
    #     'mysql+pymysql://username:password@username.mysql.pythonanywhere-services.com/username$goaltracker'

class PythonAnywhereConfig(ProductionConfig):
    """Configuration for PythonAnywhere deployment"""
    DEBUG = False
    TESTING = False
    
    # For PythonAnywhere, you can use either SQLite or MySQL
    # SQLite (default - simpler setup)
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:////home/yourusername/myGoalTracker/goal_tracker.db'
    
    # OR MySQL (uncomment and update with your details)
    # SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://username:password@username.mysql.pythonanywhere-services.com/username$goaltracker'

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'pythonanywhere': PythonAnywhereConfig,
    'default': DevelopmentConfig
}