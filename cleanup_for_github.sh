#!/bin/bash
# cleanup_for_github.sh
# Script to clean up unnecessary files before pushing to GitHub

echo "🧹 Cleaning up unnecessary files for GitHub..."

# Remove Python cache files
echo "Removing __pycache__ directories..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true
find . -type f -name "*.pyo" -delete 2>/dev/null || true
find . -type f -name "*.pyd" -delete 2>/dev/null || true

# Remove database files
echo "Removing database files..."
rm -rf instance/*.db 2>/dev/null || true
rm -rf instance/*.sqlite 2>/dev/null || true
rm -rf instance/*.sqlite3 2>/dev/null || true

# Remove utility scripts
echo "Removing utility scripts..."
rm -f add_goal_id_column.py
rm -f analyze_topic_assignment.py
rm -f check_schema.py
rm -f create_database.py
rm -f delete_tasks_keep_structure.py
rm -f fix_topic_assignments.py
rm -f import_tasks_csv.py
rm -f init_db.py
rm -f link_tasks_to_goals.py
rm -f migrate_add_goal_id.py
rm -f migrate_goals.py
rm -f reset_database.py
rm -f restructure_database.py
rm -f restructure_goals.py
rm -f setup_goals_structure.py
rm -f verify_goals_data.py
rm -f verify_structure.py

# Remove CSV files
echo "Removing CSV files..."
rm -f *.csv

# Remove local deployment scripts
echo "Removing local deployment scripts..."
rm -f deploy.bat
rm -f deploy.sh

# Remove unnecessary documentation
echo "Removing unnecessary documentation..."
rm -f CSV_IMPORT_GUIDE.md
rm -f DEPLOYMENT.md
rm -f FINAL_STRUCTURE.md
rm -f HIERARCHY_STRUCTURE.md
rm -f PYTHONANYWHERE_SETUP.md
rm -f QUICK_START.md
rm -f SYSTEM_STRUCTURE.md

# Remove wsgi_debug.py
rm -f wsgi_debug.py

# Remove app.py if it exists (we use wsgi.py)
rm -f app.py

echo "✅ Cleanup complete!"
echo ""
echo "Essential files kept:"
echo "  - app/ (application code)"
echo "  - config.py (configuration)"
echo "  - wsgi.py (WSGI entry point)"
echo "  - requirements.txt (dependencies)"
echo "  - README.md (documentation)"
echo "  - Procfile (for deployment)"
echo "  - runtime.txt (Python version)"
echo "  - .gitignore (Git ignore rules)"
echo ""
echo "Ready to commit and push to GitHub! 🚀"
