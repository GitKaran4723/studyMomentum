# ============================================================
# PythonAnywhere Deployment Script - Stage 5 (PowerShell)
# ============================================================
# Safe deployment with database backup and rollback capability
# 
# Usage: .\deploy_to_pythonanywhere.ps1
#
# Prerequisites:
# - Git configured with SSH keys for PythonAnywhere
# - PythonAnywhere username set in script
# ============================================================

param(
    [string]$PythonAnywhereUser = "YOUR_USERNAME"  # Replace with your username
)

$ErrorActionPreference = "Stop"

# Configuration
$AppName = "studyMomentum"
$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"

Write-Host "`n============================================================" -ForegroundColor Blue
Write-Host "Stage 5 Deployment to PythonAnywhere - Local Preparation" -ForegroundColor Blue
Write-Host "============================================================`n" -ForegroundColor Blue

# Step 1: Verify local changes
Write-Host "[1/6] Checking local repository..." -ForegroundColor Yellow

if (-not (Test-Path ".git")) {
    Write-Host "Error: Not a git repository" -ForegroundColor Red
    exit 1
}
Write-Host "✅ Git repository verified" -ForegroundColor Green

# Step 2: Check for uncommitted changes
Write-Host "`n[2/6] Checking for uncommitted changes..." -ForegroundColor Yellow

$status = git status --porcelain
if ($status) {
    Write-Host "Uncommitted changes found:" -ForegroundColor Yellow
    git status --short
    
    $commit = Read-Host "`nCommit these changes? (y/n)"
    if ($commit -eq "y") {
        $message = Read-Host "Commit message"
        git add .
        git commit -m "$message"
        Write-Host "✅ Changes committed" -ForegroundColor Green
    }
}

# Step 3: Push to remote
Write-Host "`n[3/6] Pushing to remote repository..." -ForegroundColor Yellow

git push origin main

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Code pushed successfully" -ForegroundColor Green
} else {
    Write-Host "❌ Git push failed!" -ForegroundColor Red
    exit 1
}

# Step 4: Create deployment package
Write-Host "`n[4/6] Creating deployment package..." -ForegroundColor Yellow

$deployFiles = @(
    "migrations/add_stage4_tables.py",
    "migrations/add_stage5_features.py",
    "deploy_to_pythonanywhere.sh",
    ".env.prediction"
)

$missing = @()
foreach ($file in $deployFiles) {
    if (-not (Test-Path $file)) {
        $missing += $file
    }
}

if ($missing.Count -gt 0) {
    Write-Host "⚠️  Missing files:" -ForegroundColor Yellow
    $missing | ForEach-Object { Write-Host "   - $_" }
} else {
    Write-Host "✅ All deployment files present" -ForegroundColor Green
}

# Step 5: Generate deployment commands
Write-Host "`n[5/6] Generating PythonAnywhere commands..." -ForegroundColor Yellow

$bashScript = @"
#!/bin/bash
# Copy these commands to PythonAnywhere Bash Console

cd ~/myGoalTracker

# 1. Backup database
mkdir -p backups
cp instance/goal_tracker.db backups/goal_tracker_$Timestamp.db
echo "Database backed up"

# 2. Pull latest code
git stash
git pull origin main

# 3. Activate virtual environment
source .venv/bin/activate || source venv/bin/activate

# 4. Install dependencies
pip install --quiet -r requirements.txt

# 5. Run migrations
python migrations/add_stage4_tables.py
python migrations/add_stage5_features.py

# 6. Restart web app
touch wsgi.py

echo "Deployment complete!"
"@

$scriptPath = "pythonanywhere_commands_$Timestamp.sh"
$bashScript | Out-File -FilePath $scriptPath -Encoding UTF8
Write-Host "✅ Deployment script created: $scriptPath" -ForegroundColor Green

# Step 6: Instructions
Write-Host "`n[6/6] Next steps for PythonAnywhere..." -ForegroundColor Yellow

Write-Host "`n============================================================" -ForegroundColor Blue
Write-Host "✅ Local Preparation Complete!" -ForegroundColor Green
Write-Host "============================================================`n" -ForegroundColor Blue

Write-Host "Now, SSH to PythonAnywhere and run these commands:`n" -ForegroundColor Cyan

Write-Host "ssh $PythonAnywhereUser@ssh.pythonanywhere.com`n" -ForegroundColor White

Write-Host "cd ~/myGoalTracker" -ForegroundColor White
Write-Host "bash deploy_to_pythonanywhere.sh`n" -ForegroundColor White

Write-Host "OR copy and paste from: $scriptPath`n" -ForegroundColor Yellow

Write-Host "To verify deployment:" -ForegroundColor Cyan
Write-Host "  • Visit: https://$PythonAnywhereUser.pythonanywhere.com" -ForegroundColor White
Write-Host "  • Check logs: tail -f /var/log/$PythonAnywhereUser.pythonanywhere.com.error.log`n" -ForegroundColor White

Write-Host "Rollback (if needed):" -ForegroundColor Yellow
Write-Host "  cd ~/myGoalTracker" -ForegroundColor White
Write-Host "  cp backups/goal_tracker_$Timestamp.db instance/goal_tracker.db" -ForegroundColor White
Write-Host "  touch wsgi.py`n" -ForegroundColor White

Write-Host "============================================================`n" -ForegroundColor Blue
