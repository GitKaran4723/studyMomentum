"""API routes for programmatic access"""
from datetime import datetime, date
from flask import request, jsonify, current_app
from flask_login import login_required, current_user
from sqlalchemy import func
from app.extensions import db
from app.api import bp
from app.models import Subject, Topic, Goal, GoalTopic, Task, Completion, Session, User

def serialize_subject(subject):
    """Serialize subject to JSON"""
    return {
        'id': subject.subject_id,
        'name': subject.name,
        'short_code': subject.short_code,
        'description': subject.description,
        'created_at': subject.created_at.isoformat() if subject.created_at else None
    }

def serialize_topic(topic):
    """Serialize topic to JSON"""
    return {
        'id': topic.topic_id,
        'name': topic.topic_name,
        'subject_id': topic.subject_id,
        'subject_name': topic.subject.name,
        'syllabus_ref': topic.syllabus_ref,
        'default_priority': topic.default_priority,
        'suggested_source': topic.suggested_source,
        'doc_link': topic.doc_link,
        'created_at': topic.created_at.isoformat() if topic.created_at else None
    }

def serialize_goal(goal):
    """Serialize goal to JSON"""
    return {
        'id': goal.goal_id,
        'title': goal.title,
        'description': goal.description,
        'start_date': goal.start_date.isoformat() if goal.start_date else None,
        'target_date': goal.target_date.isoformat() if goal.target_date else None,
        'status': goal.status,
        'progress_percentage': goal.progress_percentage,
        'created_at': goal.created_at.isoformat() if goal.created_at else None
    }

def serialize_task(task):
    """Serialize task to JSON"""
    return {
        'id': task.task_id,
        'topic_id': task.topic_id,
        'topic_name': task.topic.topic_name,
        'subject_name': task.topic.subject.name,
        'planned_date': task.planned_date.isoformat(),
        'planned_start': task.planned_start,
        'planned_duration_min': task.planned_duration_min,
        'priority': task.priority,
        'ssb_warmup': task.ssb_warmup,
        'ugc_related': task.ugc_related,
        'notes': task.notes,
        'is_completed': task.is_completed,
        'task_score': task.task_score,
        'created_at': task.created_at.isoformat() if task.created_at else None
    }

def serialize_completion(completion):
    """Serialize completion to JSON"""
    return {
        'id': completion.completion_id,
        'task_id': completion.task_id,
        'completion_date': completion.completion_date.isoformat(),
        'completed': completion.completed,
        'enthusiasm_score': completion.enthusiasm_score,
        'mcq_percent': completion.mcq_percent,
        'mains_score': completion.mains_score,
        'notes_link': completion.notes_link,
        'attempts': completion.attempts,
        'is_final': completion.is_final,
        'created_at': completion.created_at.isoformat() if completion.created_at else None
    }

# Subject endpoints
@bp.route('/subjects', methods=['GET'])
@login_required
def get_subjects():
    """Get all subjects"""
    subjects = Subject.query.all()
    return jsonify([serialize_subject(s) for s in subjects])

@bp.route('/subjects', methods=['POST'])
@login_required
def create_subject():
    """Create new subject (admin only)"""
    if not current_user.is_admin:
        return jsonify({'error': 'Admin privileges required'}), 403
    
    data = request.get_json()
    if not data or 'name' not in data:
        return jsonify({'error': 'Subject name is required'}), 400
    
    subject = Subject(
        name=data['name'],
        short_code=data.get('short_code'),
        description=data.get('description')
    )
    db.session.add(subject)
    db.session.commit()
    
    return jsonify(serialize_subject(subject)), 201

# Topic endpoints
@bp.route('/topics', methods=['GET'])
@login_required
def get_topics():
    """Get all topics"""
    subject_id = request.args.get('subject_id', type=int)
    query = Topic.query
    
    if subject_id:
        query = query.filter_by(subject_id=subject_id)
    
    topics = query.all()
    return jsonify([serialize_topic(t) for t in topics])

@bp.route('/topics', methods=['POST'])
@login_required
def create_topic():
    """Create new topic"""
    data = request.get_json()
    required_fields = ['topic_name', 'subject_id']
    
    if not data or not all(field in data for field in required_fields):
        return jsonify({'error': 'topic_name and subject_id are required'}), 400
    
    # Verify subject exists
    subject = Subject.query.get(data['subject_id'])
    if not subject:
        return jsonify({'error': 'Subject not found'}), 404
    
    topic = Topic(
        topic_name=data['topic_name'],
        subject_id=data['subject_id'],
        syllabus_ref=data.get('syllabus_ref'),
        default_priority=data.get('default_priority', 2),
        suggested_source=data.get('suggested_source'),
        doc_link=data.get('doc_link')
    )
    db.session.add(topic)
    db.session.commit()
    
    return jsonify(serialize_topic(topic)), 201

# Goal endpoints
@bp.route('/goals', methods=['GET'])
@login_required
def get_goals():
    """Get user's goals"""
    goals = Goal.query.filter_by(user_id=current_user.id).all()
    return jsonify([serialize_goal(g) for g in goals])

@bp.route('/goals', methods=['POST'])
@login_required
def create_goal():
    """Create new goal"""
    data = request.get_json()
    if not data or 'title' not in data:
        return jsonify({'error': 'Goal title is required'}), 400
    
    goal = Goal(
        user_id=current_user.id,
        title=data['title'],
        description=data.get('description'),
        start_date=datetime.strptime(data['start_date'], '%Y-%m-%d').date() if data.get('start_date') else None,
        target_date=datetime.strptime(data['target_date'], '%Y-%m-%d').date() if data.get('target_date') else None,
        status=data.get('status', 'active')
    )
    db.session.add(goal)
    db.session.commit()
    
    return jsonify(serialize_goal(goal)), 201

@bp.route('/goals/<int:goal_id>/topics', methods=['POST'])
@login_required
def add_topic_to_goal(goal_id):
    """Add topics to a goal"""
    goal = Goal.query.filter_by(goal_id=goal_id, user_id=current_user.id).first_or_404()
    
    data = request.get_json()
    if not data or 'topic_ids' not in data:
        return jsonify({'error': 'topic_ids array is required'}), 400
    
    added_topics = []
    for topic_id in data['topic_ids']:
        # Check if topic exists
        topic = Topic.query.get(topic_id)
        if not topic:
            continue
        
        # Check if already linked
        existing = GoalTopic.query.filter_by(goal_id=goal_id, topic_id=topic_id).first()
        if existing:
            continue
        
        goal_topic = GoalTopic(
            goal_id=goal_id,
            topic_id=topic_id,
            must_complete=data.get('must_complete', True)
        )
        db.session.add(goal_topic)
        added_topics.append(topic_id)
    
    db.session.commit()
    return jsonify({'added_topics': added_topics, 'count': len(added_topics)})

# Task endpoints
@bp.route('/tasks', methods=['GET'])
@login_required
def get_tasks():
    """Get user's tasks"""
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    completed = request.args.get('completed')
    
    query = Task.query.filter_by(user_id=current_user.id)
    
    if date_from:
        try:
            from_date = datetime.strptime(date_from, '%Y-%m-%d').date()
            query = query.filter(Task.planned_date >= from_date)
        except ValueError:
            return jsonify({'error': 'Invalid date_from format. Use YYYY-MM-DD'}), 400
    
    if date_to:
        try:
            to_date = datetime.strptime(date_to, '%Y-%m-%d').date()
            query = query.filter(Task.planned_date <= to_date)
        except ValueError:
            return jsonify({'error': 'Invalid date_to format. Use YYYY-MM-DD'}), 400
    
    if completed is not None:
        is_completed = completed.lower() == 'true'
        if is_completed:
            query = query.join(Completion).filter(Completion.completed == True)
        else:
            query = query.outerjoin(Completion).filter(
                (Completion.completed == False) | (Completion.completed.is_(None))
            )
    
    tasks = query.order_by(Task.planned_date.desc()).all()
    return jsonify([serialize_task(t) for t in tasks])

@bp.route('/tasks', methods=['POST'])
@login_required
def create_task():
    """Create new task"""
    data = request.get_json()
    required_fields = ['topic_id', 'planned_date', 'priority']
    
    if not data or not all(field in data for field in required_fields):
        return jsonify({'error': 'topic_id, planned_date, and priority are required'}), 400
    
    # Verify topic exists
    topic = Topic.query.get(data['topic_id'])
    if not topic:
        return jsonify({'error': 'Topic not found'}), 404
    
    try:
        planned_date = datetime.strptime(data['planned_date'], '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'error': 'Invalid planned_date format. Use YYYY-MM-DD'}), 400
    
    # Check for duplicate
    existing = Task.query.filter_by(
        user_id=current_user.id,
        topic_id=data['topic_id'],
        planned_date=planned_date
    ).first()
    
    if existing:
        return jsonify({'error': 'Task for this topic on this date already exists'}), 409
    
    task = Task(
        user_id=current_user.id,
        topic_id=data['topic_id'],
        planned_date=planned_date,
        planned_start=data.get('planned_start'),
        planned_duration_min=data.get('planned_duration_min'),
        priority=data['priority'],
        ssb_warmup=data.get('ssb_warmup', False),
        ugc_related=data.get('ugc_related', False),
        notes=data.get('notes')
    )
    db.session.add(task)
    db.session.commit()
    
    return jsonify(serialize_task(task)), 201

@bp.route('/tasks/<int:task_id>/complete', methods=['POST'])
@login_required
def complete_task_api(task_id):
    """Mark task as complete via API"""
    task = Task.query.filter_by(task_id=task_id, user_id=current_user.id).first_or_404()
    
    data = request.get_json() or {}
    
    completion = Completion(
        task_id=task_id,
        completed=data.get('completed', True),
        enthusiasm_score=data.get('enthusiasm_score'),
        mcq_percent=data.get('mcq_percent'),
        mains_score=data.get('mains_score'),
        notes_link=data.get('notes_link')
    )
    db.session.add(completion)
    db.session.commit()
    
    return jsonify(serialize_completion(completion)), 201

# Analytics endpoints
@bp.route('/dashboard', methods=['GET'])
@login_required
def dashboard_api():
    """Dashboard data API"""
    today = date.today()
    days = request.args.get('days', 7, type=int)
    
    # Recent tasks
    recent_tasks = Task.query.filter(
        Task.user_id == current_user.id,
        Task.planned_date >= today - datetime.timedelta(days=days-1)
    ).order_by(Task.planned_date.desc()).all()
    
    # Goal progress
    goals = Goal.query.filter_by(user_id=current_user.id, status='active').all()
    
    # Daily summary
    daily_summary = {}
    for i in range(days):
        day = today - datetime.timedelta(days=i)
        day_tasks = [t for t in recent_tasks if t.planned_date == day]
        daily_summary[day.isoformat()] = {
            'total_tasks': len(day_tasks),
            'completed_tasks': sum(1 for t in day_tasks if t.is_completed),
            'total_score': sum(t.task_score for t in day_tasks)
        }
    
    return jsonify({
        'daily_summary': daily_summary,
        'recent_tasks': [serialize_task(t) for t in recent_tasks[:10]],
        'goals': [serialize_goal(g) for g in goals],
        'user': {
            'username': current_user.username,
            'is_admin': current_user.is_admin
        }
    })

@bp.route('/bulk-tasks', methods=['POST'])
@login_required
def create_bulk_tasks():
    """Create multiple tasks at once"""
    data = request.get_json()
    if not data or 'tasks' not in data:
        return jsonify({'error': 'tasks array is required'}), 400
    
    created_tasks = []
    errors = []
    
    for i, task_data in enumerate(data['tasks']):
        try:
            # Validate required fields
            required_fields = ['topic_id', 'planned_date', 'priority']
            if not all(field in task_data for field in required_fields):
                errors.append(f'Task {i}: missing required fields')
                continue
            
            # Verify topic exists
            topic = Topic.query.get(task_data['topic_id'])
            if not topic:
                errors.append(f'Task {i}: topic not found')
                continue
            
            planned_date = datetime.strptime(task_data['planned_date'], '%Y-%m-%d').date()
            
            # Check for duplicate
            existing = Task.query.filter_by(
                user_id=current_user.id,
                topic_id=task_data['topic_id'],
                planned_date=planned_date
            ).first()
            
            if existing:
                errors.append(f'Task {i}: duplicate task')
                continue
            
            task = Task(
                user_id=current_user.id,
                topic_id=task_data['topic_id'],
                planned_date=planned_date,
                planned_start=task_data.get('planned_start'),
                planned_duration_min=task_data.get('planned_duration_min'),
                priority=task_data['priority'],
                ssb_warmup=task_data.get('ssb_warmup', False),
                ugc_related=task_data.get('ugc_related', False),
                notes=task_data.get('notes')
            )
            db.session.add(task)
            created_tasks.append(task)
            
        except ValueError as e:
            errors.append(f'Task {i}: {str(e)}')
        except Exception as e:
            errors.append(f'Task {i}: {str(e)}')
    
    if created_tasks:
        db.session.commit()
    
    return jsonify({
        'created_count': len(created_tasks),
        'created_tasks': [serialize_task(t) for t in created_tasks],
        'errors': errors
    })