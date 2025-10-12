#!/bin/bash
# initialize_pythonanywhere.sh
# Complete setup script for PythonAnywhere - Run this after cloning the repository
# This script will: create venv, install packages, setup database, create admin user

echo "🚀 Initializing Study Momentum on PythonAnywhere..."
echo ""

# Check if we're in the right directory
if [ ! -f "wsgi.py" ]; then
    echo "❌ Error: Please run this script from the studyMomentum directory"
    echo "Current directory: $(pwd)"
    exit 1
fi

echo "✅ Found project files in: $(pwd)"
echo ""

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv .venv
    if [ $? -ne 0 ]; then
        echo "❌ Failed to create virtual environment"
        exit 1
    fi
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment already exists"
fi
echo ""

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source .venv/bin/activate
if [ $? -ne 0 ]; then
    echo "❌ Failed to activate virtual environment"
    exit 1
fi
echo "✅ Virtual environment activated: $VIRTUAL_ENV"
echo ""

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip -q
echo "✅ Pip upgraded"
echo ""

# Install dependencies
echo "📚 Installing dependencies from requirements.txt..."
echo "   This may take a few minutes..."
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "❌ Failed to install dependencies"
    exit 1
fi
echo "✅ All dependencies installed successfully"
echo ""

# Verify Flask installation
echo "🔍 Verifying Flask installation..."
if ! python -c "import flask" 2>/dev/null; then
    echo "❌ Flask installation verification failed"
    exit 1
fi
echo "✅ Flask is installed and working"
echo ""

# Create instance directory
echo "📁 Creating instance directory..."
mkdir -p instance

# Initialize database
echo "🗄️  Initializing database..."
python << END
from app import create_app, db
app = create_app()
with app.app_context():
    db.create_all()
    print("✅ Database tables created")
END

if [ $? -ne 0 ]; then
    echo "❌ Database initialization failed"
    exit 1
fi

# Create admin user
echo "👤 Creating admin user..."
python << END
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

if [ $? -ne 0 ]; then
    echo "❌ Admin user creation failed"
    exit 1
fi

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "✅ INITIALIZATION COMPLETE!"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "📋 YOUR SETUP INFORMATION:"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "📁 Project Directory:"
echo "   $(pwd)"
echo ""
echo "🐍 Virtual Environment:"
echo "   $(pwd)/.venv"
echo ""
echo "🗄️  Database Location:"
echo "   $(pwd)/instance/goal_tracker.db"
echo ""
echo "� Admin Credentials:"
echo "   Username: admin"
echo "   Password: admin123"
echo "   ⚠️  CHANGE PASSWORD AFTER FIRST LOGIN!"
echo ""
echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "🔧 COPY THESE EXACT PATHS TO PYTHONANYWHERE WEB TAB:"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "1️⃣  Source code:"
echo "   /home/$(whoami)/studyMomentum"
echo ""
echo "2️⃣  Working directory:"
echo "   /home/$(whoami)/studyMomentum"
echo ""
echo "3️⃣  Virtualenv:"
echo "   /home/$(whoami)/studyMomentum/.venv"
echo ""
echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "📝 WSGI CONFIGURATION FILE CONTENT:"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "Click on the WSGI configuration file link in Web tab."
echo "DELETE EVERYTHING and replace with this:"
echo ""
cat << 'WSGI_CONTENT'
┌─────────────────────────────────────────────────────────────┐
│ import sys                                                  │
│ import os                                                   │
│                                                             │
│ path = '/home/$(whoami)/studyMomentum'                  │
│ if path not in sys.path:                                   │
│     sys.path.insert(0, path)                               │
│                                                             │
│ os.environ['FLASK_ENV'] = 'production'                     │
│                                                             │
│ from wsgi import application                               │
└─────────────────────────────────────────────────────────────┘
WSGI_CONTENT
echo ""
echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "🚀 FINAL STEPS:"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "1. Go to PythonAnywhere Web tab"
echo "2. Enter the paths above in the appropriate fields"
echo "3. Edit the WSGI file with the content shown above"
echo "4. Click the green 'Reload' button"
echo "5. Visit: https://$(whoami).pythonanywhere.com"
echo "6. Login with admin/admin123"
echo "7. Go to Settings → Change Password"
echo ""
echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "📚 Study Momentum is ready to launch! 🎉"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "Need help? Check PYTHONANYWHERE_QUICKSTART.md or FIX_PYTHONANYWHERE.md"
echo ""
