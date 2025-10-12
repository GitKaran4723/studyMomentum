#!/bin/bash
# initialize_pythonanywhere.sh
# Run this script on PythonAnywhere after cloning the repository

echo "🚀 Initializing Study Momentum on PythonAnywhere..."
echo ""

# Check if we're in the right directory
if [ ! -f "wsgi.py" ]; then
    echo "❌ Error: Please run this script from the myGoalTracker directory"
    exit 1
fi

# Create instance directory
echo "📁 Creating instance directory..."
mkdir -p instance

# Initialize database
echo "🗄️  Initializing database..."
python3 << END
from app import create_app, db
app = create_app()
with app.app_context():
    db.create_all()
    print("✅ Database tables created")
END

# Create admin user
echo "👤 Creating admin user..."
python3 << END
from app import create_app, db
from app.models import User
app = create_app()
with app.app_context():
    # Check if admin exists
    admin = User.query.filter_by(username='admin').first()
    if admin:
        print("ℹ️  Admin user already exists")
    else:
        admin = User(
            username='admin',
            email='admin@example.com',
            is_admin=True,
            is_active=True
        )
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        print("✅ Admin user created!")
        print("   Username: admin")
        print("   Password: admin123")
        print("   ⚠️  CHANGE THIS PASSWORD AFTER FIRST LOGIN!")
END

echo ""
echo "✅ Initialization complete!"
echo ""
echo "Next steps:"
echo "1. Configure your WSGI file in PythonAnywhere Web tab"
echo "2. Set virtualenv path: ~/.virtualenvs/mygoaltracker"
echo "3. Set working directory: ~/myGoalTracker"
echo "4. Reload your web app"
echo "5. Visit your site and login with admin/admin123"
echo "6. CHANGE THE ADMIN PASSWORD!"
echo ""
echo "📚 Study Momentum is ready to use! 🎉"
