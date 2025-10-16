"""
OPTIONAL: Convert old UTC timestamps to IST
This is NOT REQUIRED - only for cosmetic consistency
Only run this if you want all timestamps to show IST
"""

from app import create_app, db
from app.models import User, Subject, Topic, Goal, Task, Completion, Session, DailySnapshot
from datetime import datetime
import pytz

app = create_app()

def convert_utc_to_ist(utc_dt):
    """Convert naive UTC datetime to IST"""
    if utc_dt is None:
        return None
    
    # If already timezone-aware, return as-is
    if utc_dt.tzinfo is not None:
        return utc_dt
    
    # Assume naive datetime is UTC
    utc = pytz.UTC.localize(utc_dt)
    ist = pytz.timezone('Asia/Kolkata')
    return utc.astimezone(ist)

def migrate_timestamps():
    """Migrate all UTC timestamps to IST (OPTIONAL)"""
    with app.app_context():
        print("Starting timestamp migration (OPTIONAL)...")
        print("This will convert old UTC timestamps to IST")
        print("=" * 60)
        
        # Users
        users = User.query.all()
        for user in users:
            if user.created_at and user.created_at.tzinfo is None:
                user.created_at = convert_utc_to_ist(user.created_at)
        print(f"✓ Converted {len(users)} user timestamps")
        
        # Subjects
        subjects = Subject.query.all()
        for subject in subjects:
            if subject.created_at and subject.created_at.tzinfo is None:
                subject.created_at = convert_utc_to_ist(subject.created_at)
        print(f"✓ Converted {len(subjects)} subject timestamps")
        
        # Topics
        topics = Topic.query.all()
        for topic in topics:
            if topic.created_at and topic.created_at.tzinfo is None:
                topic.created_at = convert_utc_to_ist(topic.created_at)
        print(f"✓ Converted {len(topics)} topic timestamps")
        
        # Goals
        goals = Goal.query.all()
        for goal in goals:
            if goal.created_at and goal.created_at.tzinfo is None:
                goal.created_at = convert_utc_to_ist(goal.created_at)
        print(f"✓ Converted {len(goals)} goal timestamps")
        
        # Tasks
        tasks = Task.query.all()
        for task in tasks:
            if task.created_at and task.created_at.tzinfo is None:
                task.created_at = convert_utc_to_ist(task.created_at)
        print(f"✓ Converted {len(tasks)} task timestamps")
        
        # Completions
        completions = Completion.query.all()
        for completion in completions:
            if completion.created_at and completion.created_at.tzinfo is None:
                completion.created_at = convert_utc_to_ist(completion.created_at)
        print(f"✓ Converted {len(completions)} completion timestamps")
        
        # Sessions
        sessions = Session.query.all()
        for session in sessions:
            if session.created_at and session.created_at.tzinfo is None:
                session.created_at = convert_utc_to_ist(session.created_at)
            if session.start_time and session.start_time.tzinfo is None:
                session.start_time = convert_utc_to_ist(session.start_time)
            if session.end_time and session.end_time.tzinfo is None:
                session.end_time = convert_utc_to_ist(session.end_time)
        print(f"✓ Converted {len(sessions)} session timestamps")
        
        # DailySnapshots
        snapshots = DailySnapshot.query.all()
        for snapshot in snapshots:
            if snapshot.created_at and snapshot.created_at.tzinfo is None:
                snapshot.created_at = convert_utc_to_ist(snapshot.created_at)
        print(f"✓ Converted {len(snapshots)} snapshot timestamps")
        
        # Commit changes
        db.session.commit()
        print("=" * 60)
        print("✅ Migration complete!")
        print("\nNOTE: This was cosmetic only - not required for functionality")

if __name__ == '__main__':
    response = input("This will convert old UTC timestamps to IST. Continue? (yes/no): ")
    if response.lower() == 'yes':
        migrate_timestamps()
    else:
        print("Migration cancelled.")
