"""
Stage 1 Master Script: Run all migration steps in correct order
"""
import os
import sys
import shutil
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def print_banner(title):
    """Print a formatted banner"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70 + "\n")

def create_backup():
    """Step 1: Create database backup"""
    print_banner("Step 1: Creating Database Backup")
    
    try:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        db_path = os.path.join(base_dir, 'instance', 'study_momentum.db')
        
        if not os.path.exists(db_path):
            print("⚠️  WARNING: Database not found at", db_path)
            print("   This might be a fresh installation.")
            response = input("   Continue anyway? (y/n): ")
            if response.lower() != 'y':
                return False
            return True
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = f"{db_path}.backup_{timestamp}"
        
        shutil.copy2(db_path, backup_path)
        
        backup_size = os.path.getsize(backup_path)
        print(f"✅ Backup created successfully!")
        print(f"   Location: {backup_path}")
        print(f"   Size: {backup_size:,} bytes")
        
        return True
        
    except Exception as e:
        print(f"❌ Backup failed: {e}")
        return False

def run_tests():
    """Step 2: Run pre-migration tests"""
    print_banner("Step 2: Running Pre-Migration Tests")
    
    try:
        from migrations.test_stage1 import run_all_tests
        
        success = run_all_tests()
        
        if not success:
            print("\n⚠️  Some tests failed. Review output above.")
            response = input("Continue anyway? (y/n): ")
            return response.lower() == 'y'
        
        return True
        
    except Exception as e:
        print(f"❌ Tests failed: {e}")
        return False

def run_migration():
    """Step 3: Run database migration"""
    print_banner("Step 3: Running Database Migration")
    
    try:
        from migrations.add_prediction_fields import migrate_up
        
        success = migrate_up()
        
        if success:
            print("\n✅ Migration completed successfully!")
            return True
        else:
            print("\n❌ Migration failed. Check output above.")
            return False
            
    except Exception as e:
        print(f"❌ Migration error: {e}")
        import traceback
        traceback.print_exc()
        return False

def run_backfill():
    """Step 4: Run backfill script"""
    print_banner("Step 4: Running Data Backfill")
    
    try:
        from migrations.backfill_prediction_data import main as backfill_main
        
        success = backfill_main()
        
        if success:
            print("\n✅ Backfill completed successfully!")
            return True
        else:
            print("\n❌ Backfill failed. Check output above.")
            return False
            
    except Exception as e:
        print(f"❌ Backfill error: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_feature_flags():
    """Step 5: Verify feature flags"""
    print_banner("Step 5: Checking Feature Flags")
    
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    env_path = os.path.join(base_dir, '.env')
    env_prediction_path = os.path.join(base_dir, '.env.prediction')
    
    # Check if .env.prediction exists
    if not os.path.exists(env_prediction_path):
        print("⚠️  WARNING: .env.prediction not found")
        return True
    
    # Check if .env has prediction settings
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            env_content = f.read()
        
        if 'PREDICTION_ENABLED' in env_content:
            print("✅ Feature flags already in .env")
            
            # Check if disabled
            if 'PREDICTION_ENABLED=false' in env_content or 'PREDICTION_ENABLED=False' in env_content:
                print("   ✅ PREDICTION_ENABLED=false (correct)")
            else:
                print("   ⚠️  PREDICTION_ENABLED might be true (should be false for Stage 1)")
            
            return True
    
    print("ℹ️  Feature flags not in .env yet")
    print("   To add them, run:")
    print(f"   Get-Content {env_prediction_path} | Add-Content {env_path}")
    print("\n   Or manually copy contents from .env.prediction to .env")
    
    return True

def final_verification():
    """Step 6: Final verification"""
    print_banner("Step 6: Final Verification")
    
    print("Checking migration results...\n")
    
    try:
        import sqlite3
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        db_path = os.path.join(base_dir, 'instance', 'study_momentum.db')
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check tasks table
        cursor.execute("PRAGMA table_info(tasks)")
        task_columns = [row[1] for row in cursor.fetchall()]
        
        new_task_cols = ['task_type', 'concept_weight', 'mastery', 'lambda_forgetting']
        found = [col for col in new_task_cols if col in task_columns]
        
        if len(found) == len(new_task_cols):
            print(f"✅ Tasks table: {len(found)}/{len(new_task_cols)} new columns present")
        else:
            print(f"⚠️  Tasks table: Only {len(found)}/{len(new_task_cols)} new columns found")
        
        # Check subjects table
        cursor.execute("PRAGMA table_info(subjects)")
        subject_columns = [row[1] for row in cursor.fetchall()]
        
        if 'subject_weight' in subject_columns:
            print("✅ Subjects table: subject_weight column present")
        else:
            print("⚠️  Subjects table: subject_weight column missing")
        
        # Check if backfill ran
        cursor.execute("SELECT COUNT(*) FROM subjects WHERE subject_weight IS NOT NULL")
        weighted_subjects = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM subjects")
        total_subjects = cursor.fetchone()[0]
        
        if total_subjects > 0:
            if weighted_subjects > 0:
                print(f"✅ Backfill: {weighted_subjects}/{total_subjects} subjects have weights")
            else:
                print(f"⚠️  Backfill: No subjects have weights yet")
        else:
            print("ℹ️  No subjects in database (fresh install)")
        
        # Check virtual tasks
        cursor.execute("SELECT COUNT(*) FROM tasks WHERE task_name LIKE '%Virtual%'")
        virtual_tasks = cursor.fetchone()[0]
        
        if virtual_tasks > 0:
            print(f"✅ Virtual tasks: {virtual_tasks} created")
        else:
            print("ℹ️  No virtual tasks (all subjects may have real tasks)")
        
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"⚠️  Verification error: {e}")
        return True  # Non-critical

def print_next_steps():
    """Print next steps"""
    print_banner("🎉 Stage 1 Complete!")
    
    print("Next steps:\n")
    print("1. Test the application:")
    print("   python run.py")
    print()
    print("2. Verify existing functionality:")
    print("   - Dashboard loads")
    print("   - Tasks page works")
    print("   - Create/edit tasks works")
    print()
    print("3. Check feature flags in .env:")
    print("   PREDICTION_ENABLED should be 'false'")
    print()
    print("4. Ready for Stage 2:")
    print("   - Implement services/predict.py")
    print("   - Add prediction API endpoints")
    print("   - Create UI components")
    print()
    print("📖 See STAGE1_MIGRATION_GUIDE.md for detailed documentation")
    print()

def main():
    """Main execution flow"""
    print()
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 15 + "Stage 1: Schema & Safe Defaults" + " " * 21 + "║")
    print("║" + " " * 14 + "Prediction System Migration" + " " * 26 + "║")
    print("╚" + "=" * 68 + "╝")
    
    print("\nThis script will:")
    print("  1. Create a database backup")
    print("  2. Run pre-migration tests")
    print("  3. Add new prediction fields to database")
    print("  4. Backfill safe default values")
    print("  5. Verify feature flags")
    print("  6. Run final verification")
    
    print("\n⚠️  IMPORTANT: This will modify your database!")
    print("   A backup will be created, but please ensure you have")
    print("   your own backup before proceeding.")
    
    response = input("\nContinue with Stage 1 migration? (y/n): ")
    
    if response.lower() != 'y':
        print("\n❌ Migration cancelled by user.")
        return False
    
    # Step 1: Backup
    if not create_backup():
        print("\n❌ Migration stopped: Backup failed")
        return False
    
    input("\nPress Enter to continue to tests...")
    
    # Step 2: Tests
    if not run_tests():
        print("\n❌ Migration stopped: Tests failed or user cancelled")
        return False
    
    input("\nPress Enter to continue to migration...")
    
    # Step 3: Migration
    if not run_migration():
        print("\n❌ Migration stopped: Database migration failed")
        print("   Your database backup is available for rollback")
        return False
    
    input("\nPress Enter to continue to backfill...")
    
    # Step 4: Backfill
    if not run_backfill():
        print("\n❌ Warning: Backfill failed")
        print("   Migration completed but backfill had issues")
        print("   You can re-run backfill manually")
    
    # Step 5: Feature flags (non-critical)
    check_feature_flags()
    
    # Step 6: Verification
    final_verification()
    
    # Success!
    print_next_steps()
    
    return True

if __name__ == '__main__':
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n❌ Migration cancelled by user (Ctrl+C)")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
