#!/bin/bash
# COMPLETE DIAGNOSTIC SCRIPT FOR PYTHONANYWHERE
# Run this on PythonAnywhere to diagnose issues

echo "🔍 Study Momentum - Diagnostic Report"
echo "========================================"
echo ""

# Check current directory
echo "📁 Current Directory:"
pwd
echo ""

# Check if in correct directory
echo "📂 Checking if wsgi.py exists:"
if [ -f "wsgi.py" ]; then
    echo "   ✅ wsgi.py found"
    echo "   Size: $(wc -c < wsgi.py) bytes"
else
    echo "   ❌ wsgi.py NOT FOUND!"
    echo "   You need to cd to the correct directory"
fi
echo ""

# Check virtual environment
echo "🐍 Virtual Environment:"
if [ -d ".venv" ]; then
    echo "   ✅ .venv directory exists"
    echo "   Python: $(.venv/bin/python --version)"
else
    echo "   ❌ .venv directory NOT FOUND!"
    echo "   Run: python3 -m venv .venv"
fi
echo ""

# Check if venv is activated
echo "🔄 Virtual Environment Status:"
if [ -n "$VIRTUAL_ENV" ]; then
    echo "   ✅ Virtual environment is ACTIVATED"
    echo "   Location: $VIRTUAL_ENV"
else
    echo "   ⚠️  Virtual environment is NOT activated"
    echo "   Run: source .venv/bin/activate"
fi
echo ""

# Check Flask installation
echo "📦 Flask Installation:"
if [ -n "$VIRTUAL_ENV" ]; then
    python -c "import flask; print('   ✅ Flask version:', flask.__version__)" 2>/dev/null || echo "   ❌ Flask NOT installed"
else
    echo "   ⚠️  Activate venv first to check"
fi
echo ""

# Check all required packages
echo "📚 Required Packages:"
if [ -n "$VIRTUAL_ENV" ]; then
    for pkg in flask sqlalchemy flask_login flask_wtf; do
        python -c "import $pkg; print('   ✅ $pkg')" 2>/dev/null || echo "   ❌ $pkg missing"
    done
else
    echo "   ⚠️  Activate venv first to check"
fi
echo ""

# Check database
echo "🗄️  Database:"
if [ -f "instance/goal_tracker.db" ]; then
    echo "   ✅ Database exists"
    echo "   Size: $(wc -c < instance/goal_tracker.db) bytes"
    echo "   Location: $(pwd)/instance/goal_tracker.db"
else
    echo "   ❌ Database NOT found"
    echo "   Run the initialization script"
fi
echo ""

# Check Git status
echo "🔧 Git Repository:"
if [ -d ".git" ]; then
    echo "   ✅ Git repository"
    echo "   Branch: $(git branch --show-current)"
    echo "   Last commit: $(git log -1 --oneline)"
else
    echo "   ❌ Not a git repository"
fi
echo ""

# Check Python path
echo "🛤️  Python sys.path (first 3):"
if [ -n "$VIRTUAL_ENV" ]; then
    python -c "import sys; [print(f'   {i}. {p}') for i, p in enumerate(sys.path[:3], 1)]"
else
    echo "   ⚠️  Activate venv first"
fi
echo ""

# Test wsgi import
echo "🧪 Testing wsgi.py Import:"
if [ -n "$VIRTUAL_ENV" ] && [ -f "wsgi.py" ]; then
    python -c "from wsgi import application; print('   ✅ Successfully imported application')" 2>/dev/null || echo "   ❌ Failed to import - check error above"
else
    echo "   ⚠️  Prerequisites not met"
fi
echo ""

# Summary
echo "========================================"
echo "📊 SUMMARY"
echo "========================================"
echo ""
echo "Your PythonAnywhere paths should be:"
echo ""
echo "Source code:"
echo "   /home/$(whoami)/studyMomentum"
echo ""
echo "Working directory:"
echo "   /home/$(whoami)/studyMomentum"
echo ""
echo "Virtualenv:"
echo "   /home/$(whoami)/studyMomentum/.venv"
echo ""
echo "WSGI file should contain:"
echo "   project_home = '/home/$(whoami)/studyMomentum'"
echo ""
echo "========================================"
