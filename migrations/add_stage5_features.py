"""
Stage 5 Migration: Subject Weights, Topic Hints, Performance Features
================================================================
Adds:
- subject_weights JSON field to goals (stores per-subject weight overrides)
- topic_weight_hint to topics (user can adjust topic importance)
- cache_key to daily_snapshots (for 5-minute plan caching)
- retired_at to tasks (mark when virtual tasks are retired)

Run: python migrations/add_stage5_features.py
"""

import sqlite3
from datetime import datetime
import os

# Get the database path from instance directory
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'instance', 'goal_tracker.db')

def run_migration():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("="*60)
    print("Stage 5 Migration: Weights, Hints & Performance")
    print("="*60)
    
    try:
        # 1. Add subject_weights to goals
        print("\n📋 Adding subject_weights column to goals...")
        try:
            cursor.execute("""
                ALTER TABLE goals 
                ADD COLUMN subject_weights TEXT DEFAULT NULL
            """)
            print("✅ subject_weights column added")
        except sqlite3.OperationalError as e:
            if "duplicate column" in str(e).lower():
                print("ℹ️  subject_weights column already exists")
            else:
                raise
        
        # Verify
        cursor.execute("PRAGMA table_info(goals)")
        cols = [row[1] for row in cursor.fetchall()]
        if 'subject_weights' in cols:
            print("✅ Column verified in goals table")
        
        # 2. Add topic_weight_hint to topics
        print("\n📋 Adding topic_weight_hint column to topics...")
        try:
            cursor.execute("""
                ALTER TABLE topics 
                ADD COLUMN topic_weight_hint REAL DEFAULT NULL
            """)
            print("✅ topic_weight_hint column added")
        except sqlite3.OperationalError as e:
            if "duplicate column" in str(e).lower():
                print("ℹ️  topic_weight_hint column already exists")
            else:
                raise
        
        # Verify
        cursor.execute("PRAGMA table_info(topics)")
        cols = [row[1] for row in cursor.fetchall()]
        if 'topic_weight_hint' in cols:
            print("✅ Column verified in topics table")
        
        # 3. Add cache_key to daily_snapshots
        print("\n📋 Adding cache_key column to daily_snapshots...")
        try:
            cursor.execute("""
                ALTER TABLE daily_snapshots 
                ADD COLUMN cache_key VARCHAR(64) DEFAULT NULL
            """)
            print("✅ cache_key column added")
        except sqlite3.OperationalError as e:
            if "duplicate column" in str(e).lower():
                print("ℹ️  cache_key column already exists")
            else:
                raise
        
        # Create index on cache_key for fast lookups
        print("📋 Creating index on cache_key...")
        try:
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_snapshots_cache_key 
                ON daily_snapshots(cache_key, created_at)
            """)
            print("✅ Index created on cache_key")
        except Exception as e:
            print(f"⚠️  Index creation skipped: {e}")
        
        # 4. Add retired_at to tasks
        print("\n📋 Adding retired_at column to tasks...")
        try:
            cursor.execute("""
                ALTER TABLE tasks 
                ADD COLUMN retired_at DATETIME DEFAULT NULL
            """)
            print("✅ retired_at column added")
        except sqlite3.OperationalError as e:
            if "duplicate column" in str(e).lower():
                print("ℹ️  retired_at column already exists")
            else:
                raise
        
        # Verify
        cursor.execute("PRAGMA table_info(tasks)")
        cols = [row[1] for row in cursor.fetchall()]
        if 'retired_at' in cols:
            print("✅ Column verified in tasks table")
        
        # Create index on retired_at for filtering
        print("📋 Creating index on retired_at...")
        try:
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_tasks_retired_at 
                ON tasks(retired_at) WHERE retired_at IS NOT NULL
            """)
            print("✅ Index created on retired_at")
        except Exception as e:
            print(f"⚠️  Index creation skipped: {e}")
        
        # 5. Add derived column to tasks
        print("\n📋 Adding derived column to tasks...")
        try:
            cursor.execute("""
                ALTER TABLE tasks 
                ADD COLUMN derived BOOLEAN DEFAULT 1
            """)
            print("✅ derived column added")
        except sqlite3.OperationalError as e:
            if "duplicate column" in str(e).lower():
                print("ℹ️  derived column already exists")
            else:
                raise
        
        # Verify
        cursor.execute("PRAGMA table_info(tasks)")
        cols = [row[1] for row in cursor.fetchall()]
        if 'derived' in cols:
            print("✅ Column verified in tasks table")
        
        # Commit all changes
        conn.commit()
        
        print("\n" + "="*60)
        print("✅ Stage 5 migration completed successfully!")
        print("\nNext steps:")
        print("1. Update Goal model with subject_weights JSON field")
        print("2. Update Topic model with topic_weight_hint")
        print("3. Add task retirement logic to apply-plan endpoint")
        print("4. Implement 5-minute caching with cache_key")
        print("="*60)
        
    except Exception as e:
        conn.rollback()
        print(f"\n❌ Migration failed: {e}")
        raise
    finally:
        conn.close()

if __name__ == '__main__':
    run_migration()
