# cleanup_for_github.ps1
# Script to clean up unnecessary files before pushing to GitHub

Write-Host "🧹 Cleaning up unnecessary files for GitHub..." -ForegroundColor Cyan

# Remove Python cache files
Write-Host "Removing __pycache__ directories..." -ForegroundColor Yellow
Get-ChildItem -Path . -Recurse -Directory -Filter "__pycache__" | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
Get-ChildItem -Path . -Recurse -File -Filter "*.pyc" | Remove-Item -Force -ErrorAction SilentlyContinue
Get-ChildItem -Path . -Recurse -File -Filter "*.pyo" | Remove-Item -Force -ErrorAction SilentlyContinue
Get-ChildItem -Path . -Recurse -File -Filter "*.pyd" | Remove-Item -Force -ErrorAction SilentlyContinue

# Remove database files
Write-Host "Removing database files..." -ForegroundColor Yellow
Remove-Item -Path "instance\*.db" -Force -ErrorAction SilentlyContinue
Remove-Item -Path "instance\*.sqlite" -Force -ErrorAction SilentlyContinue
Remove-Item -Path "instance\*.sqlite3" -Force -ErrorAction SilentlyContinue

# Remove utility scripts
Write-Host "Removing utility scripts..." -ForegroundColor Yellow
$utilityScripts = @(
    "add_goal_id_column.py",
    "analyze_topic_assignment.py",
    "check_schema.py",
    "create_database.py",
    "delete_tasks_keep_structure.py",
    "fix_topic_assignments.py",
    "import_tasks_csv.py",
    "init_db.py",
    "link_tasks_to_goals.py",
    "migrate_add_goal_id.py",
    "migrate_goals.py",
    "reset_database.py",
    "restructure_database.py",
    "restructure_goals.py",
    "setup_goals_structure.py",
    "verify_goals_data.py",
    "verify_structure.py"
)

foreach ($script in $utilityScripts) {
    Remove-Item -Path $script -Force -ErrorAction SilentlyContinue
}

# Remove CSV files
Write-Host "Removing CSV files..." -ForegroundColor Yellow
Remove-Item -Path "*.csv" -Force -ErrorAction SilentlyContinue

# Remove local deployment scripts
Write-Host "Removing local deployment scripts..." -ForegroundColor Yellow
Remove-Item -Path "deploy.bat" -Force -ErrorAction SilentlyContinue
Remove-Item -Path "deploy.sh" -Force -ErrorAction SilentlyContinue

# Remove unnecessary documentation
Write-Host "Removing unnecessary documentation..." -ForegroundColor Yellow
$unnecessaryDocs = @(
    "CSV_IMPORT_GUIDE.md",
    "DEPLOYMENT.md",
    "FINAL_STRUCTURE.md",
    "HIERARCHY_STRUCTURE.md",
    "PYTHONANYWHERE_SETUP.md",
    "QUICK_START.md",
    "SYSTEM_STRUCTURE.md"
)

foreach ($doc in $unnecessaryDocs) {
    Remove-Item -Path $doc -Force -ErrorAction SilentlyContinue
}

# Remove wsgi_debug.py and app.py
Remove-Item -Path "wsgi_debug.py" -Force -ErrorAction SilentlyContinue
Remove-Item -Path "app.py" -Force -ErrorAction SilentlyContinue

Write-Host ""
Write-Host "✅ Cleanup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "Essential files kept:" -ForegroundColor Cyan
Write-Host "  - app/ (application code)" -ForegroundColor White
Write-Host "  - config.py (configuration)" -ForegroundColor White
Write-Host "  - wsgi.py (WSGI entry point)" -ForegroundColor White
Write-Host "  - requirements.txt (dependencies)" -ForegroundColor White
Write-Host "  - README.md (documentation)" -ForegroundColor White
Write-Host "  - Procfile (for deployment)" -ForegroundColor White
Write-Host "  - runtime.txt (Python version)" -ForegroundColor White
Write-Host "  - .gitignore (Git ignore rules)" -ForegroundColor White
Write-Host ""
Write-Host "Ready to commit and push to GitHub! 🚀" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. git add ." -ForegroundColor White
Write-Host "  2. git commit -m 'Initial commit - Study Momentum App'" -ForegroundColor White
Write-Host "  3. git push origin main" -ForegroundColor White
