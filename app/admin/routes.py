"""Admin routes for user and database management"""
from flask import render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_required, current_user
from app.extensions import db
from app.admin import bp
from app.models import User, Subject, Topic, Goal, Task, Completion, Session

def admin_required(f):
    """Decorator to require admin privileges"""
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('Admin privileges required', 'error')
            return redirect(url_for('main.dashboard'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

@bp.route('/')
@login_required
@admin_required
def admin_dashboard():
    """Admin dashboard"""
    # System statistics
    stats = {
        'total_users': User.query.count(),
        'active_users': User.query.filter_by(is_active=True).count(),
        'total_subjects': Subject.query.count(),
        'total_topics': Topic.query.count(),
        'total_goals': Goal.query.count(),
        'total_tasks': Task.query.count(),
        'completed_tasks': Task.query.join(Completion).filter(Completion.completed == True).count(),
    }
    
    # Recent activity
    recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
    recent_completions = Completion.query.join(Task).join(User).order_by(
        Completion.created_at.desc()).limit(10).all()
    
    return render_template('admin/dashboard.html', 
                         stats=stats,
                         recent_users=recent_users,
                         recent_completions=recent_completions)

@bp.route('/users')
@login_required
@admin_required
def users():
    """Manage users"""
    page = request.args.get('page', 1, type=int)
    users = User.query.order_by(User.created_at.desc()).paginate(
        page=page, per_page=current_app.config['ITEMS_PER_PAGE'],
        error_out=False
    )
    return render_template('admin/users.html', users=users)

@bp.route('/users/new', methods=['GET', 'POST'])
@login_required
@admin_required
def create_user():
    """Create new user"""
    from app.auth.forms import RegistrationForm
    
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data,
            is_active=True,
            is_admin=False
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash(f'User {user.username} created successfully!', 'success')
        return redirect(url_for('admin.users'))
    
    return render_template('admin/create_user.html', form=form, title='Create User')

@bp.route('/users/<int:user_id>/toggle-status', methods=['POST'])
@login_required
@admin_required
def toggle_user_status(user_id):
    """Toggle user active status"""
    user = User.query.get_or_404(user_id)
    
    # Prevent deactivating the current admin
    if user.id == current_user.id:
        flash('Cannot deactivate your own account', 'error')
        return redirect(url_for('admin.users'))
    
    user.is_active = not user.is_active
    db.session.commit()
    
    status = 'activated' if user.is_active else 'deactivated'
    flash(f'User {user.username} has been {status}', 'success')
    return redirect(url_for('admin.users'))

@bp.route('/users/<int:user_id>/make-admin', methods=['POST'])
@login_required
@admin_required
def make_admin(user_id):
    """Make user an admin"""
    user = User.query.get_or_404(user_id)
    user.is_admin = True
    db.session.commit()
    flash(f'User {user.username} is now an admin', 'success')
    return redirect(url_for('admin.users'))

@bp.route('/users/<int:user_id>/remove-admin', methods=['POST'])
@login_required
@admin_required
def remove_admin(user_id):
    """Remove admin privileges"""
    user = User.query.get_or_404(user_id)
    
    # Prevent removing admin from self
    if user.id == current_user.id:
        flash('Cannot remove admin privileges from your own account', 'error')
        return redirect(url_for('admin.users'))
    
    user.is_admin = False
    db.session.commit()
    flash(f'Admin privileges removed from {user.username}', 'success')
    return redirect(url_for('admin.users'))

@bp.route('/users/<int:user_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    """Delete user and all associated data"""
    user = User.query.get_or_404(user_id)
    
    # Prevent deleting self
    if user.id == current_user.id:
        flash('Cannot delete your own account', 'error')
        return redirect(url_for('admin.users'))
    
    username = user.username
    db.session.delete(user)
    db.session.commit()
    flash(f'User {username} and all associated data has been deleted', 'success')
    return redirect(url_for('admin.users'))

@bp.route('/database')
@login_required
@admin_required
def database_management():
    """Database management interface"""
    # Table row counts
    table_stats = {
        'users': User.query.count(),
        'subjects': Subject.query.count(),
        'topics': Topic.query.count(),
        'goals': Goal.query.count(),
        'tasks': Task.query.count(),
        'completions': Completion.query.count(),
        'sessions': Session.query.count(),
    }
    
    return render_template('admin/database.html', table_stats=table_stats)

@bp.route('/database/backup', methods=['POST'])
@login_required
@admin_required
def backup_database():
    """Create database backup"""
    import sqlite3
    import os
    from datetime import datetime
    
    try:
        # Get database path
        db_path = current_app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
        backup_name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        backup_path = os.path.join(os.path.dirname(db_path), 'backups', backup_name)
        
        # Create backups directory if it doesn't exist
        os.makedirs(os.path.dirname(backup_path), exist_ok=True)
        
        # Create backup
        source = sqlite3.connect(db_path)
        backup = sqlite3.connect(backup_path)
        source.backup(backup)
        source.close()
        backup.close()
        
        flash(f'Database backup created: {backup_name}', 'success')
    except Exception as e:
        flash(f'Backup failed: {str(e)}', 'error')
    
    return redirect(url_for('admin.database_management'))

@bp.route('/database/clear-table/<table_name>', methods=['POST'])
@login_required
@admin_required
def clear_table(table_name):
    """Clear all data from a table"""
    allowed_tables = ['completions', 'sessions', 'tasks', 'goals', 'topics']
    
    if table_name not in allowed_tables:
        flash('Invalid table name', 'error')
        return redirect(url_for('admin.database_management'))
    
    try:
        if table_name == 'completions':
            Completion.query.delete()
        elif table_name == 'sessions':
            Session.query.delete()
        elif table_name == 'tasks':
            Task.query.delete()
        elif table_name == 'goals':
            Goal.query.delete()
        elif table_name == 'topics':
            Topic.query.delete()
        
        db.session.commit()
        flash(f'All data cleared from {table_name} table', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error clearing table: {str(e)}', 'error')
    
    return redirect(url_for('admin.database_management'))

@bp.route('/system-info')
@login_required
@admin_required
def system_info():
    """System information"""
    import sys
    import platform
    from flask import __version__ as flask_version
    
    info = {
        'python_version': sys.version,
        'platform': platform.platform(),
        'flask_version': flask_version,
        'database_uri': current_app.config['SQLALCHEMY_DATABASE_URI'],
        'debug_mode': current_app.debug,
        'secret_key_set': bool(current_app.config.get('SECRET_KEY')),
    }
    
    return render_template('admin/system_info.html', info=info)

# API endpoints for admin
@bp.route('/api/stats')
@login_required
@admin_required
def api_admin_stats():
    """API endpoint for admin statistics"""
    stats = {
        'users': {
            'total': User.query.count(),
            'active': User.query.filter_by(is_active=True).count(),
            'admins': User.query.filter_by(is_admin=True).count()
        },
        'content': {
            'subjects': Subject.query.count(),
            'topics': Topic.query.count(),
            'goals': Goal.query.count(),
            'tasks': Task.query.count(),
            'completions': Completion.query.count()
        },
        'activity': {
            'completed_tasks': Task.query.join(Completion).filter(
                Completion.completed == True).count(),
            'pending_tasks': Task.query.outerjoin(Completion).filter(
                (Completion.completed == False) | (Completion.completed.is_(None))
            ).count()
        }
    }
    
    return jsonify(stats)