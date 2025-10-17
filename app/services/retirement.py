"""
Stage 5: Virtual Task Retirement Logic
=======================================
Retire virtual tasks when a subject has enough real tasks
with concept_weight sum ≈ subject_weight

Called during apply-plan operation
"""

from app.models import Task, Subject, Topic, db
from datetime import datetime
from app.services.predict import ist_now


def should_retire_virtual_tasks(goal_id: int, subject_id: int) -> bool:
    """
    Check if virtual tasks for a subject should be retired
    
    Returns True if:
    - Sum of real task concept_weights >= 95% of subject_weight
    - Subject has at least 3 real tasks
    """
    subject = Subject.query.get(subject_id)
    if not subject:
        return False
    
    subject_weight = subject.subject_weight or 0
    if subject_weight == 0:
        return False
    
    # Get all real tasks (not derived/virtual, not retired)
    real_tasks = Task.query.join(Topic).filter(
        Topic.subject_id == subject_id,
        Task.derived == False,  # Real user-created tasks
        Task.retired_at == None
    ).all()
    
    # Need minimum number of real tasks
    if len(real_tasks) < 3:
        return False
    
    # Sum concept weights of real tasks
    real_weight_sum = sum(t.concept_weight or 0 for t in real_tasks)
    
    # Check if we've covered >= 95% of subject weight
    coverage = real_weight_sum / subject_weight if subject_weight > 0 else 0
    
    return coverage >= 0.95


def retire_virtual_tasks(goal_id: int, subject_id: int) -> int:
    """
    Retire all virtual tasks for a subject
    
    Returns: Number of tasks retired
    """
    now = ist_now()
    
    # Find all virtual tasks for this subject
    virtual_tasks = Task.query.join(Topic).filter(
        Topic.subject_id == subject_id,
        Task.derived == True,  # Virtual/derived tasks
        Task.retired_at == None  # Not already retired
    ).all()
    
    count = 0
    for task in virtual_tasks:
        task.retired_at = now
        count += 1
    
    if count > 0:
        db.session.commit()
    
    return count


def auto_retire_check(goal_id: int):
    """
    Check all subjects in a goal for virtual task retirement
    Called automatically during apply-plan
    
    Returns: Dict of {subject_id: count_retired}
    """
    from app.models import Goal
    
    goal = Goal.query.get(goal_id)
    if not goal:
        return {}
    
    retirement_log = {}
    
    for subject in goal.subjects:
        if should_retire_virtual_tasks(goal_id, subject.subject_id):
            count = retire_virtual_tasks(goal_id, subject.subject_id)
            if count > 0:
                retirement_log[subject.subject_id] = {
                    'subject_name': subject.name,
                    'tasks_retired': count
                }
    
    return retirement_log


def reactivate_virtual_task(task_id: int) -> bool:
    """
    Reactivate a retired virtual task (admin utility)
    Returns True if successful
    """
    task = Task.query.get(task_id)
    if not task or not task.retired_at:
        return False
    
    task.retired_at = None
    db.session.commit()
    return True


def get_retirement_stats(goal_id: int) -> dict:
    """
    Get retirement statistics for a goal
    
    Returns:
    {
        'total_tasks': int,
        'virtual_tasks': int,
        'retired_tasks': int,
        'real_tasks': int,
        'subjects': [{
            'subject_id': int,
            'subject_name': str,
            'virtual_count': int,
            'retired_count': int,
            'real_count': int,
            'coverage': float  # % of subject weight covered by real tasks
        }]
    }
    """
    from app.models import Goal
    
    goal = Goal.query.get(goal_id)
    if not goal:
        return {}
    
    stats = {
        'total_tasks': 0,
        'virtual_tasks': 0,
        'retired_tasks': 0,
        'real_tasks': 0,
        'subjects': []
    }
    
    for subject in goal.subjects:
        all_tasks = Task.query.join(Topic).filter(
            Topic.subject_id == subject.subject_id
        ).all()
        
        virtual = [t for t in all_tasks if t.derived and not t.retired_at]
        retired = [t for t in all_tasks if t.retired_at]
        real = [t for t in all_tasks if not t.derived and not t.retired_at]
        
        real_weight_sum = sum(t.concept_weight or 0 for t in real)
        subject_weight = subject.subject_weight or 0
        coverage = (real_weight_sum / subject_weight * 100) if subject_weight > 0 else 0
        
        stats['subjects'].append({
            'subject_id': subject.subject_id,
            'subject_name': subject.name,
            'virtual_count': len(virtual),
            'retired_count': len(retired),
            'real_count': len(real),
            'coverage': round(coverage, 1)
        })
        
        stats['total_tasks'] += len(all_tasks)
        stats['virtual_tasks'] += len(virtual)
        stats['retired_tasks'] += len(retired)
        stats['real_tasks'] += len(real)
    
    return stats
