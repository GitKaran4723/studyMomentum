"""
Stage 1: Add prediction fields to support intelligent planning
Adds fields for mastery tracking, forgetting curves, and Bayesian updates
All fields have safe defaults - existing app continues to work unchanged
"""
import sqlite3
from datetime import datetime
import os

def get_db_path():
    """Get the database path"""
    # Adjust this path based on your setup
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_dir, 'instance', 'goal_tracker.db')

def migrate_up():
    """Add new prediction fields to all tables"""
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("🚀 Starting Stage 1 Migration: Adding Prediction Fields...")
    
    try:
        # ============================================
        # 1. GOALS TABLE
        # ============================================
        print("\n📊 Migrating GOALS table...")
        
        # Check if columns already exist to make migration idempotent
        cursor.execute("PRAGMA table_info(goals)")
        existing_cols = {row[1] for row in cursor.fetchall()}
        
        goals_columns = {
            'threshold_marks': 'ALTER TABLE goals ADD COLUMN threshold_marks FLOAT',
            'exam_date': 'ALTER TABLE goals ADD COLUMN exam_date DATE',
            'daily_hours_default': 'ALTER TABLE goals ADD COLUMN daily_hours_default FLOAT DEFAULT 6.0',
            'split_new_default': 'ALTER TABLE goals ADD COLUMN split_new_default FLOAT DEFAULT 0.6',
            'delta_decay': 'ALTER TABLE goals ADD COLUMN delta_decay FLOAT DEFAULT 0.7'
        }
        
        for col_name, sql in goals_columns.items():
            if col_name not in existing_cols:
                cursor.execute(sql)
                print(f"  ✅ Added {col_name}")
            else:
                print(f"  ⏭️  {col_name} already exists")
        
        # ============================================
        # 2. SUBJECTS TABLE
        # ============================================
        print("\n📚 Migrating SUBJECTS table...")
        
        cursor.execute("PRAGMA table_info(subjects)")
        existing_cols = {row[1] for row in cursor.fetchall()}
        
        if 'subject_weight' not in existing_cols:
            cursor.execute('ALTER TABLE subjects ADD COLUMN subject_weight FLOAT')
            print("  ✅ Added subject_weight")
        else:
            print("  ⏭️  subject_weight already exists")
        
        # ============================================
        # 3. TOPICS TABLE
        # ============================================
        print("\n📝 Migrating TOPICS table...")
        
        cursor.execute("PRAGMA table_info(topics)")
        existing_cols = {row[1] for row in cursor.fetchall()}
        
        if 'topic_weight_hint' not in existing_cols:
            cursor.execute('ALTER TABLE topics ADD COLUMN topic_weight_hint FLOAT')
            print("  ✅ Added topic_weight_hint")
        else:
            print("  ⏭️  topic_weight_hint already exists")
        
        # ============================================
        # 4. TASKS TABLE (Most Complex)
        # ============================================
        print("\n✅ Migrating TASKS table...")
        
        cursor.execute("PRAGMA table_info(tasks)")
        existing_cols = {row[1] for row in cursor.fetchall()}
        
        tasks_columns = {
            'task_type': "ALTER TABLE tasks ADD COLUMN task_type TEXT DEFAULT 'learn' CHECK(task_type IN ('learn', 'revise', 'test'))",
            'concept_weight': 'ALTER TABLE tasks ADD COLUMN concept_weight FLOAT',
            't_est_hours': 'ALTER TABLE tasks ADD COLUMN t_est_hours FLOAT DEFAULT 4.0',
            'mastery': 'ALTER TABLE tasks ADD COLUMN mastery FLOAT DEFAULT 0.0',
            'lambda_forgetting': 'ALTER TABLE tasks ADD COLUMN lambda_forgetting FLOAT DEFAULT 0.04',
            'eta_learn': 'ALTER TABLE tasks ADD COLUMN eta_learn FLOAT DEFAULT 0.8',
            'rho_revise': 'ALTER TABLE tasks ADD COLUMN rho_revise FLOAT DEFAULT 0.35',
            'last_studied_at': 'ALTER TABLE tasks ADD COLUMN last_studied_at DATE',
            'spaced_stage': 'ALTER TABLE tasks ADD COLUMN spaced_stage INTEGER DEFAULT 0',
            'alpha': 'ALTER TABLE tasks ADD COLUMN alpha FLOAT',
            'beta': 'ALTER TABLE tasks ADD COLUMN beta FLOAT',
            'last_decay_date': 'ALTER TABLE tasks ADD COLUMN last_decay_date DATE'  # For idempotent decay
        }
        
        for col_name, sql in tasks_columns.items():
            if col_name not in existing_cols:
                cursor.execute(sql)
                print(f"  ✅ Added {col_name}")
            else:
                print(f"  ⏭️  {col_name} already exists")
        
        # ============================================
        # 5. DAILY_SNAPSHOTS TABLE (Extended)
        # ============================================
        print("\n📸 Migrating DAILY_SNAPSHOTS table...")
        
        cursor.execute("PRAGMA table_info(daily_snapshots)")
        existing_cols = {row[1] for row in cursor.fetchall()}
        
        snapshot_columns = {
            'mu': 'ALTER TABLE daily_snapshots ADD COLUMN mu FLOAT',
            'sigma2': 'ALTER TABLE daily_snapshots ADD COLUMN sigma2 FLOAT',
            'p_clear_today': 'ALTER TABLE daily_snapshots ADD COLUMN p_clear_today FLOAT',
            'delta_mu_day': 'ALTER TABLE daily_snapshots ADD COLUMN delta_mu_day FLOAT',
            'mu_exam': 'ALTER TABLE daily_snapshots ADD COLUMN mu_exam FLOAT',
            'p_clear_exam': 'ALTER TABLE daily_snapshots ADD COLUMN p_clear_exam FLOAT',
            'hours_planned': 'ALTER TABLE daily_snapshots ADD COLUMN hours_planned FLOAT',
            'hours_actual': 'ALTER TABLE daily_snapshots ADD COLUMN hours_actual FLOAT',
            'activity_score': 'ALTER TABLE daily_snapshots ADD COLUMN activity_score FLOAT',
            'learning_gain_marks': 'ALTER TABLE daily_snapshots ADD COLUMN learning_gain_marks FLOAT'
        }
        
        for col_name, sql in snapshot_columns.items():
            if col_name not in existing_cols:
                cursor.execute(sql)
                print(f"  ✅ Added {col_name}")
            else:
                print(f"  ⏭️  {col_name} already exists")
        
        conn.commit()
        print("\n✅ Migration completed successfully!")
        return True
        
    except Exception as e:
        conn.rollback()
        print(f"\n❌ Migration failed: {e}")
        return False
        
    finally:
        conn.close()


def migrate_down():
    """Rollback: Remove prediction fields"""
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("🔄 Rolling back Stage 1 Migration...")
    
    try:
        # Note: SQLite doesn't support DROP COLUMN directly
        # You would need to recreate tables without these columns
        # For now, we'll just document the rollback process
        
        print("\n⚠️  SQLite doesn't support DROP COLUMN.")
        print("To rollback, you need to:")
        print("1. Export data")
        print("2. Recreate tables without new columns")
        print("3. Re-import data")
        print("\nOr restore from backup before migration.")
        
        conn.commit()
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Rollback failed: {e}")
        return False
        
    finally:
        conn.close()


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == 'down':
        migrate_down()
    else:
        migrate_up()
