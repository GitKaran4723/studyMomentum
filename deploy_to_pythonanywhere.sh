#!/bin/bash
# ============================================================
# PythonAnywhere Deployment Script - Stage 5
# ============================================================
# Safe deployment with database backup and rollback capability
# 
# Usage: bash deploy_to_pythonanywhere.sh
#
# What this does:
# 1. Backs up current database
# 2. Pulls latest code from Git
# 3. Runs migrations
# 4. Restarts web app
# 5. Validates deployment
# ============================================================

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
APP_NAME="studyMomentum"
PYTHONANYWHERE_USER="${PYTHONANYWHERE_USER:-YOUR_USERNAME}"  # Replace with your username
APP_PATH="/home/$PYTHONANYWHERE_USER/$APP_NAME"
BACKUP_DIR="$APP_PATH/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

echo -e "${BLUE}============================================================${NC}"
echo -e "${BLUE}Stage 5 Deployment to PythonAnywhere${NC}"
echo -e "${BLUE}============================================================${NC}"
echo ""

# Step 1: Pre-flight checks
echo -e "${YELLOW}[1/8] Pre-flight checks...${NC}"

if [ ! -d "$APP_PATH" ]; then
    echo -e "${RED}Error: Application directory not found: $APP_PATH${NC}"
    echo "Please update PYTHONANYWHERE_USER in this script"
    exit 1
fi

cd "$APP_PATH"
echo -e "${GREEN}✅ Application directory found${NC}"

# Check if git repo exists
if [ ! -d ".git" ]; then
    echo -e "${RED}Error: Not a git repository${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Git repository verified${NC}"

# Step 2: Create backup directory
echo ""
echo -e "${YELLOW}[2/8] Creating backup directory...${NC}"
mkdir -p "$BACKUP_DIR"
echo -e "${GREEN}✅ Backup directory ready: $BACKUP_DIR${NC}"

# Step 3: Backup current database
echo ""
echo -e "${YELLOW}[3/8] Backing up database...${NC}"

DB_PATH="$APP_PATH/instance/goal_tracker.db"
if [ -f "$DB_PATH" ]; then
    BACKUP_FILE="$BACKUP_DIR/goal_tracker_${TIMESTAMP}.db"
    cp "$DB_PATH" "$BACKUP_FILE"
    
    # Verify backup
    if [ -f "$BACKUP_FILE" ]; then
        BACKUP_SIZE=$(stat -f%z "$BACKUP_FILE" 2>/dev/null || stat -c%s "$BACKUP_FILE")
        echo -e "${GREEN}✅ Database backed up: $BACKUP_FILE${NC}"
        echo -e "   Size: $BACKUP_SIZE bytes"
    else
        echo -e "${RED}❌ Backup failed!${NC}"
        exit 1
    fi
else
    echo -e "${YELLOW}⚠️  Database not found (fresh install?)${NC}"
fi

# Step 4: Backup .env files
echo ""
echo -e "${YELLOW}[4/8] Backing up environment files...${NC}"
if [ -f ".env" ]; then
    cp .env "$BACKUP_DIR/.env_${TIMESTAMP}"
    echo -e "${GREEN}✅ .env backed up${NC}"
fi
if [ -f ".env.prediction" ]; then
    cp .env.prediction "$BACKUP_DIR/.env.prediction_${TIMESTAMP}"
    echo -e "${GREEN}✅ .env.prediction backed up${NC}"
fi

# Step 5: Pull latest code
echo ""
echo -e "${YELLOW}[5/8] Pulling latest code from Git...${NC}"

# Stash any local changes
git stash save "Auto-stash before deployment $TIMESTAMP"

# Pull latest changes
git pull origin main

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Code updated successfully${NC}"
else
    echo -e "${RED}❌ Git pull failed!${NC}"
    echo "Rolling back..."
    git stash pop
    exit 1
fi

# Step 6: Install/update dependencies
echo ""
echo -e "${YELLOW}[6/8] Installing dependencies...${NC}"

# Activate virtual environment
if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
elif [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
else
    echo -e "${YELLOW}⚠️  Virtual environment not found, using system Python${NC}"
fi

# Install requirements
if [ -f "requirements.txt" ]; then
    pip install --quiet --upgrade pip
    pip install --quiet -r requirements.txt
    echo -e "${GREEN}✅ Dependencies installed${NC}"
else
    echo -e "${YELLOW}⚠️  No requirements.txt found${NC}"
fi

# Step 7: Run migrations
echo ""
echo -e "${YELLOW}[7/8] Running database migrations...${NC}"

# Run Stage 4 migration (if not already run)
if [ -f "migrations/add_stage4_tables.py" ]; then
    echo "Running Stage 4 migration..."
    python migrations/add_stage4_tables.py
fi

# Run Stage 5 migration
if [ -f "migrations/add_stage5_features.py" ]; then
    echo "Running Stage 5 migration..."
    python migrations/add_stage5_features.py
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Migrations completed${NC}"
    else
        echo -e "${RED}❌ Migration failed!${NC}"
        echo "Restoring database backup..."
        cp "$BACKUP_FILE" "$DB_PATH"
        exit 1
    fi
else
    echo -e "${RED}❌ Migration file not found${NC}"
    exit 1
fi

# Step 8: Restart web app
echo ""
echo -e "${YELLOW}[8/8] Restarting web application...${NC}"

# Touch wsgi.py to reload the app
if [ -f "wsgi.py" ]; then
    touch wsgi.py
    echo -e "${GREEN}✅ Web app restart triggered${NC}"
elif [ -f "app.py" ]; then
    touch app.py
    echo -e "${GREEN}✅ Web app restart triggered${NC}"
else
    echo -e "${YELLOW}⚠️  WSGI file not found - manual restart required${NC}"
    echo "Visit: https://www.pythonanywhere.com/user/$PYTHONANYWHERE_USER/webapps/"
fi

# Validation
echo ""
echo -e "${BLUE}============================================================${NC}"
echo -e "${GREEN}✅ Deployment Complete!${NC}"
echo -e "${BLUE}============================================================${NC}"
echo ""
echo "Summary:"
echo "  • Database backup: $BACKUP_FILE"
echo "  • Code updated from Git"
echo "  • Migrations applied"
echo "  • Web app restarted"
echo ""
echo "Next steps:"
echo "  1. Visit your website to verify it's working"
echo "  2. Check error logs if needed:"
echo "     tail -f /var/log/$PYTHONANYWHERE_USER.pythonanywhere.com.error.log"
echo "  3. Test Stage 5 features:"
echo "     - Subject weight sliders"
echo "     - Analytics dashboard"
echo "     - Plan caching"
echo ""
echo "Rollback command (if needed):"
echo "  cp $BACKUP_FILE $DB_PATH"
echo "  touch wsgi.py"
echo ""
echo -e "${BLUE}============================================================${NC}"

# Keep last 5 backups, delete older ones
echo ""
echo -e "${YELLOW}Cleaning up old backups...${NC}"
cd "$BACKUP_DIR"
ls -t goal_tracker_*.db | tail -n +6 | xargs -r rm
echo -e "${GREEN}✅ Old backups cleaned (kept last 5)${NC}"
