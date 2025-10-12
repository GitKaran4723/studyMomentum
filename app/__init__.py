"""
Application factory and extensions
"""

from datetime import datetime, timedelta
from flask import Flask
from config import config
import os
from sqlalchemy import inspect

# Import extensions
from app.extensions import db, login_manager

def create_app(config_name=None):
    """Create and configure Flask application"""
    app = Flask(__name__)
    
    # Load configuration
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'default')
        # Auto-detect PythonAnywhere environment
        if 'PYTHONANYWHERE_DOMAIN' in os.environ or '/home/' in os.getcwd():
            config_name = 'pythonanywhere'
    app.config.from_object(config[config_name])
    
    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'
    
    # Configure persistent login settings
    remember_duration = app.config.get('REMEMBER_COOKIE_DURATION', 30 * 24 * 60 * 60)
    if isinstance(remember_duration, (int, float)):
        remember_duration = timedelta(seconds=remember_duration)
    login_manager.remember_cookie_duration = remember_duration
    session_protection = app.config.get('SESSION_PROTECTION', 'strong')
    if session_protection:
        login_manager.session_protection = session_protection

    lifetime_value = app.config.get('PERMANENT_SESSION_LIFETIME', timedelta(days=30))
    if isinstance(lifetime_value, (int, float)):
        lifetime_value = timedelta(seconds=lifetime_value)
    app.permanent_session_lifetime = lifetime_value

    from flask import session
    from flask_login import current_user
    
    @app.before_request
    def extend_session():
        """Extend session for active users - Android style persistent login"""
        if current_user.is_authenticated:
            session.permanent = True
            # Update last activity to extend session
            session['last_activity'] = datetime.utcnow().isoformat()
    
    # Register blueprints
    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')
    
    from app.main import bp as main_bp
    app.register_blueprint(main_bp)
    
    from app.api import bp as api_bp
    app.register_blueprint(api_bp, url_prefix='/api')
    
    from app.admin import bp as admin_bp
    app.register_blueprint(admin_bp, url_prefix='/admin')
    
    # Create database tables
    with app.app_context():
        db.create_all()
        inspector = inspect(db.engine)
        columns = [column['name'] for column in inspector.get_columns('tasks')]
        if 'goal_id' not in columns:
            with db.engine.begin() as connection:
                connection.execute(db.text('ALTER TABLE tasks ADD COLUMN goal_id INTEGER'))
        
        # Create default admin user if it doesn't exist
        from app.models import User
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(username='admin', email='admin@goaltracker.com', is_admin=True)
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
    
    return app

@login_manager.user_loader
def load_user(user_id):
    from app.models import User
    return User.query.get(int(user_id))