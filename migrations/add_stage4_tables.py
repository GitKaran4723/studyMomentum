"""
Stage 4 Migration: Add IdempotencyLog table
Prevents duplicate writes from apply-plan and quiz operations
"""

import sqlite3
from datetime import datetime
import sys
import os

# Add parent directory to path to import models
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

DB_PATH = 'instance/goal_tracker.db'


def add_idempotency_log_table():
    """Create idempotency_logs table for Stage 4 write operations"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        print("📋 Creating idempotency_logs table...")
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS idempotency_logs (
                log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                idempotency_key VARCHAR(64) UNIQUE NOT NULL,
                user_id INTEGER NOT NULL,
                goal_id INTEGER NOT NULL,
                operation_type VARCHAR(50) NOT NULL,
                operation_date DATE NOT NULL,
                request_hash VARCHAR(64) NOT NULL,
                response_data TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (goal_id) REFERENCES goals(goal_id)
            )
        ''')
        
        # Create index for fast lookups
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_idempotency_key 
            ON idempotency_logs(idempotency_key)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_idempotency_user_goal_date 
            ON idempotency_logs(user_id, goal_id, operation_date)
        ''')
        
        conn.commit()
        print("✅ idempotency_logs table created successfully")
        
        # Verify
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='idempotency_logs'")
        if cursor.fetchone():
            cursor.execute("PRAGMA table_info(idempotency_logs)")
            columns = cursor.fetchall()
            print(f"\n✅ Table structure verified: {len(columns)} columns")
            for col in columns:
                print(f"   - {col[1]} ({col[2]})")
        
        return True
        
    except sqlite3.Error as e:
        print(f"❌ Error: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


def add_goal_version_column():
    """Add version column to goals for optimistic locking"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        print("\n📋 Adding version column to goals table...")
        
        # Check if column already exists
        cursor.execute("PRAGMA table_info(goals)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'version' not in columns:
            cursor.execute('ALTER TABLE goals ADD COLUMN version INTEGER DEFAULT 1')
            conn.commit()
            print("✅ Version column added to goals")
        else:
            print("ℹ️  Version column already exists")
        
        return True
        
    except sqlite3.Error as e:
        print(f"❌ Error: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


def add_task_version_column():
    """Add version column to tasks for optimistic locking"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        print("\n📋 Adding version column to tasks table...")
        
        # Check if column already exists
        cursor.execute("PRAGMA table_info(tasks)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'version' not in columns:
            cursor.execute('ALTER TABLE tasks ADD COLUMN version INTEGER DEFAULT 1')
            conn.commit()
            print("✅ Version column added to tasks")
        else:
            print("ℹ️  Version column already exists")
        
        return True
        
    except sqlite3.Error as e:
        print(f"❌ Error: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


def main():
    """Run Stage 4 migration"""
    print("="*60)
    print("Stage 4 Migration: Idempotency & Optimistic Locking")
    print("="*60)
    
    if not os.path.exists(DB_PATH):
        print(f"❌ Database not found at {DB_PATH}")
        return False
    
    success = True
    
    # 1. Create idempotency_logs table
    if not add_idempotency_log_table():
        success = False
    
    # 2. Add version columns for optimistic locking
    if not add_goal_version_column():
        success = False
    
    if not add_task_version_column():
        success = False
    
    print("\n" + "="*60)
    if success:
        print("✅ Stage 4 migration completed successfully!")
        print("\nNext steps:")
        print("1. Test idempotency: Apply plan twice with same key")
        print("2. Test optimistic locking: Concurrent updates")
        print("3. Enable writes: PREDICTION_ENABLED=on")
    else:
        print("❌ Migration completed with errors")
        print("Review errors above and retry")
    print("="*60)
    
    return success


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
