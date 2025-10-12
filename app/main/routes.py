"""Main application routes"""
from datetime import datetime, date, timedelta
from flask import render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_required, current_user
from sqlalchemy import func, and_, or_, case
from app.extensions import db
from app.main import bp
from app.main.forms import SubjectForm, TopicForm, GoalForm, TaskForm, CompletionForm, SessionForm
from app.models import Subject, Topic, Goal, GoalTopic, Task, Completion, Session, DailySnapshot

@bp.route('/')
@bp.route('/dashboard')
@login_required
def dashboard():
    """Main dashboard"""
    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    month_start = today.replace(day=1)
    
    # Today's tasks
    today_tasks = Task.query.filter(
        Task.user_id == current_user.id,
        Task.planned_date == today
    ).all()
    
    # Week's tasks
    week_tasks = Task.query.filter(
        Task.user_id == current_user.id,
        Task.planned_date >= week_start,
        Task.planned_date < week_start + timedelta(days=7)
    ).all()
    
    # Calculate metrics
    today_completed = sum(1 for task in today_tasks if task.is_completed)
    today_score = sum(task.task_score for task in today_tasks)
    
    week_completed = sum(1 for task in week_tasks if task.is_completed)
    week_score = sum(task.task_score for task in week_tasks)
    
    # Active goals
    active_goals = Goal.query.filter(
        Goal.user_id == current_user.id,
        Goal.status == 'active'
    ).limit(5).all()
    
    # Recent activity
    recent_completions = Completion.query.join(Task).filter(
        Task.user_id == current_user.id
    ).order_by(Completion.created_at.desc()).limit(5).all()
    
    return render_template('main/dashboard.html', 
                         today_tasks=today_tasks,
                         today_completed=today_completed,
                         today_total=len(today_tasks),
                         today_score=round(today_score, 2),
                         week_completed=week_completed,
                         week_total=len(week_tasks),
                         week_score=round(week_score, 2),
                         active_goals=active_goals,
                         recent_completions=recent_completions,
                         now=datetime.now)

@bp.route('/subjects')
@login_required
def subjects():
    """List all subjects"""
    goal_id = request.args.get('goal_id', type=int)
    
    if goal_id:
        subjects = Subject.query.filter_by(goal_id=goal_id).all()
    else:
        subjects = Subject.query.all()
    
    goals = Goal.query.filter_by(user_id=current_user.id).all()
    total_subjects_count = Subject.query.count()
    
    return render_template('main/subjects.html', 
                         subjects=subjects, 
                         goals=goals, 
                         selected_goal_id=goal_id,
                         total_subjects_count=total_subjects_count)

@bp.route('/subjects/new', methods=['GET', 'POST'])
@login_required
def new_subject():
    """Create new subject"""
    if not current_user.is_admin:
        flash('Admin privileges required', 'error')
        return redirect(url_for('main.subjects'))
    
    form = SubjectForm()
    # Populate goal choices
    form.goal_id.choices = [(g.goal_id, g.title) for g in Goal.query.filter_by(user_id=current_user.id).all()]
    
    if form.validate_on_submit():
        subject = Subject(
            goal_id=form.goal_id.data,
            name=form.name.data,
            short_code=form.short_code.data,
            description=form.description.data
        )
        db.session.add(subject)
        db.session.commit()
        flash('Subject created successfully!', 'success')
        return redirect(url_for('main.subjects'))
    
    return render_template('main/subject_form.html', form=form, title='New Subject')

@bp.route('/subjects/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_subject(id):
    """Edit subject"""
    if not current_user.is_admin:
        flash('Admin privileges required', 'error')
        return redirect(url_for('main.subjects'))
    
    subject = Subject.query.get_or_404(id)
    form = SubjectForm()
    # Populate goal choices
    form.goal_id.choices = [(g.goal_id, g.title) for g in Goal.query.filter_by(user_id=current_user.id).all()]
    
    if form.validate_on_submit():
        subject.goal_id = form.goal_id.data
        subject.name = form.name.data
        subject.short_code = form.short_code.data
        subject.description = form.description.data
        db.session.commit()
        flash('Subject updated successfully!', 'success')
        return redirect(url_for('main.subjects'))
    elif request.method == 'GET':
        form.goal_id.data = subject.goal_id
        form.name.data = subject.name
        form.short_code.data = subject.short_code
        form.description.data = subject.description
    
    return render_template('main/subject_form.html', form=form, subject=subject, title='Edit Subject')

@bp.route('/subjects/<int:id>/delete', methods=['POST'])
@login_required
def delete_subject(id):
    """Delete subject"""
    if not current_user.is_admin:
        flash('Admin privileges required', 'error')
        return redirect(url_for('main.subjects'))
    
    subject = Subject.query.get_or_404(id)
    
    # Check if subject has tasks
    task_count = Task.query.join(Topic).filter(Topic.subject_id == subject.subject_id).count()
    if task_count > 0:
        flash(f'Cannot delete subject "{subject.name}". It has {task_count} tasks. Delete tasks first.', 'error')
        return redirect(url_for('main.subjects'))
    
    # Delete subject (cascade will handle topics)
    subject_name = subject.name
    db.session.delete(subject)
    db.session.commit()
    flash(f'Subject "{subject_name}" deleted successfully!', 'success')
    return redirect(url_for('main.subjects'))

@bp.route('/goals/<int:id>/delete', methods=['POST'])
@login_required
def delete_goal(id):
    """Delete goal"""
    if not current_user.is_admin:
        flash('Admin privileges required', 'error')
        return redirect(url_for('main.goals'))
    
    goal = Goal.query.get_or_404(id)
    
    # Check if goal has subjects
    subject_count = Subject.query.filter_by(goal_id=goal.goal_id).count()
    if subject_count > 0:
        # Check if any subject has tasks
        total_tasks = Task.query.join(Topic).join(Subject).filter(
            Subject.goal_id == goal.goal_id
        ).count()
        
        if total_tasks > 0:
            flash(f'Cannot delete goal "{goal.title}". It has {subject_count} subjects with {total_tasks} tasks. Delete tasks and subjects first.', 'error')
            return redirect(url_for('main.goals'))
    
    # Delete goal (cascade will handle subjects → topics → tasks)
    goal_title = goal.title
    db.session.delete(goal)
    db.session.commit()
    flash(f'Goal "{goal_title}" deleted successfully!', 'success')
    return redirect(url_for('main.goals'))

@bp.route('/topics')
@login_required
def topics():
    """List all topics"""
    page = request.args.get('page', 1, type=int)
    subject_id = request.args.get('subject_id', type=int)
    
    query = Topic.query
    if subject_id:
        query = query.filter_by(subject_id=subject_id)
    
    topics = query.paginate(
        page=page, per_page=current_app.config['ITEMS_PER_PAGE'],
        error_out=False
    )
    
    subjects = Subject.query.all()
    return render_template('main/topics.html', topics=topics, subjects=subjects, selected_subject=subject_id)

@bp.route('/topics/new', methods=['GET', 'POST'])
@login_required
def new_topic():
    """Create new topic"""
    form = TopicForm()
    form.subject_id.choices = [(s.subject_id, s.name) for s in Subject.query.all()]
    
    if form.validate_on_submit():
        topic = Topic(
            topic_name=form.topic_name.data,
            subject_id=form.subject_id.data,
            syllabus_ref=form.syllabus_ref.data,
            default_priority=form.default_priority.data,
            suggested_source=form.suggested_source.data,
            doc_link=form.doc_link.data
        )
        db.session.add(topic)
        db.session.commit()
        flash('Topic created successfully!', 'success')
        return redirect(url_for('main.topics'))
    
    return render_template('main/topic_form.html', form=form, title='New Topic')

@bp.route('/topics/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_topic(id):
    """Edit existing topic"""
    topic = Topic.query.get_or_404(id)
    form = TopicForm()
    form.subject_id.choices = [(s.subject_id, s.name) for s in Subject.query.all()]
    
    if form.validate_on_submit():
        topic.topic_name = form.topic_name.data
        topic.subject_id = form.subject_id.data
        topic.syllabus_ref = form.syllabus_ref.data
        topic.default_priority = form.default_priority.data
        topic.suggested_source = form.suggested_source.data
        topic.doc_link = form.doc_link.data
        db.session.commit()
        flash('Topic updated successfully!', 'success')
        return redirect(url_for('main.topics'))
    elif request.method == 'GET':
        form.topic_name.data = topic.topic_name
        form.subject_id.data = topic.subject_id
        form.syllabus_ref.data = topic.syllabus_ref
        form.default_priority.data = topic.default_priority
        form.suggested_source.data = topic.suggested_source
        form.doc_link.data = topic.doc_link
    
    return render_template('main/topic_form.html', form=form, title='Edit Topic')

@bp.route('/goals')
@login_required
def goals():
    """List user's goals"""
    goals = Goal.query.filter_by(user_id=current_user.id).all()
    
    # Calculate user stats
    user_stats = {
        'total_goals': len(goals),
        'completed_goals': len([g for g in goals if g.status == 'completed']),
        'completion_rate': round((len([g for g in goals if g.status == 'completed']) / len(goals)) * 100) if goals else 0
    }
    
    return render_template('main/goals.html', goals=goals, user_stats=user_stats)

@bp.route('/goals/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_goal(id):
    """Edit goal"""
    goal = Goal.query.filter_by(goal_id=id, user_id=current_user.id).first_or_404()
    form = GoalForm(obj=goal)
    
    if form.validate_on_submit():
        form.populate_obj(goal)
        db.session.commit()
        flash('Goal updated successfully!', 'success')
        return redirect(url_for('main.goals'))
    
    return render_template('main/goal_form.html', form=form, title='Edit Goal')

@bp.route('/goals/add')
@login_required
def add_goal():
    """Redirect to new goal form"""
    return redirect(url_for('main.new_goal'))

@bp.route('/goals/new', methods=['GET', 'POST'])
@login_required  
def new_goal():
    """Create new goal"""
    form = GoalForm()
    if form.validate_on_submit():
        goal = Goal(
            user_id=current_user.id,
            goal_name=form.goal_name.data,
            description=form.description.data,
            goal_type=form.goal_type.data,
            target_date=form.target_date.data,
            target_value=form.target_value.data,
            unit=form.unit.data,
            success_criteria=form.success_criteria.data,
            reward=form.reward.data,
            status=form.status.data
        )
        db.session.add(goal)
        db.session.commit()
        flash('Goal created successfully!', 'success')
        return redirect(url_for('main.goals'))
    
    return render_template('main/goal_form.html', form=form, title='New Goal')

@bp.route('/tasks')
@login_required
def tasks():
    """List user's tasks"""
    page = request.args.get('page', 1, type=int)
    date_filter = request.args.get('date')
    status_filter = request.args.get('status')
    priority_filter = request.args.get('priority')
    goal_filter = request.args.get('goal_id', type=int)
    
    query = Task.query.filter_by(user_id=current_user.id)
    
    # Date filtering
    if date_filter:
        if date_filter == 'today':
            query = query.filter(Task.planned_date == date.today())
        else:
            try:
                filter_date = datetime.strptime(date_filter, '%Y-%m-%d').date()
                query = query.filter(Task.planned_date == filter_date)
            except ValueError:
                pass
    
    # Status filtering
    if status_filter == 'completed':
        query = query.join(Completion).filter(Completion.completed == True)
    elif status_filter == 'in_progress':
        query = query.join(Completion).filter(Completion.completed == False)
    elif status_filter == 'pending':
        query = query.outerjoin(Completion).filter(
            or_(Completion.completion_id.is_(None))
        )
    
    # Priority filtering
    if priority_filter:
        query = query.filter(Task.priority == int(priority_filter))
    
    # Goal filtering
    if goal_filter:
        query = query.filter(Task.goal_id == goal_filter)
    
    tasks = query.order_by(Task.planned_date.desc(), Task.priority.asc()).paginate(
        page=page, per_page=current_app.config['ITEMS_PER_PAGE'],
        error_out=False
    )
    
    goals = Goal.query.filter_by(user_id=current_user.id).all()
    
    return render_template('main/tasks.html', tasks=tasks, goals=goals)

@bp.route('/tasks/new', methods=['GET', 'POST'])
@login_required
def new_task():
    """Create new task"""
    form = TaskForm()
    user_goals = Goal.query.filter_by(user_id=current_user.id).order_by(Goal.status.desc(), Goal.goal_name.asc()).all()
    if not user_goals:
        flash('Create a goal first to align this task with your mission.', 'info')
        return redirect(url_for('main.new_goal'))

    form.goal_id.choices = [(0, '— Select goal —')] + [(g.goal_id, g.goal_name or g.title) for g in user_goals]
    form.topic_id.choices = [(0, '— Select topic —')] + [(t.topic_id, f"{t.subject.name}: {t.topic_name}") 
                            for t in Topic.query.join(Subject).all()]
    
    # Pre-select topic and goal if coming from topic page
    topic_id = request.args.get('topic_id', type=int)
    if topic_id and request.method == 'GET':
        topic = Topic.query.get(topic_id)
        if topic:
            form.topic_id.data = topic_id
            # Auto-select goal based on topic's subject
            if topic.subject and topic.subject.goal_id:
                form.goal_id.data = topic.subject.goal_id
    
    if form.validate_on_submit():
        task = Task(
            user_id=current_user.id,
            goal_id=form.goal_id.data,
            topic_id=form.topic_id.data,
            task_name=form.task_name.data,
            planned_date=form.planned_date.data,
            planned_start=form.planned_start.data,
            planned_duration_min=form.planned_duration_min.data,
            priority=form.priority.data,
            ssb_warmup=form.ssb_warmup.data,
            ugc_related=form.ugc_related.data,
            notes=form.notes.data
        )
        db.session.add(task)
        db.session.commit()
        flash('Task created successfully!', 'success')
        return redirect(url_for('main.tasks'))
    
    return render_template('main/task_form.html', form=form, title='New Task')

@bp.route('/tasks/<int:id>/complete', methods=['GET', 'POST'])
@login_required
def complete_task(id):
    """Mark task as complete"""
    task = Task.query.filter_by(task_id=id, user_id=current_user.id).first_or_404()
    
    form = CompletionForm()
    if form.validate_on_submit():
        completion = Completion(
            task_id=task.task_id,
            completed=form.completed.data,
            enthusiasm_score=form.enthusiasm_score.data,
            mcq_percent=form.mcq_percent.data,
            mains_score=form.mains_score.data,
            notes_link=form.notes_link.data
        )
        db.session.add(completion)
        db.session.commit()
        flash('Task completion recorded!', 'success')
        return redirect(url_for('main.tasks'))
    
    return render_template('main/completion_form.html', form=form, task=task, title='Complete Task')

@bp.route('/tasks/<int:id>/toggle', methods=['POST'])
@login_required
def toggle_task(id):
    """Toggle task completion status"""
    task = Task.query.filter_by(task_id=id, user_id=current_user.id).first_or_404()
    
    # Get or create completion
    completion = task.latest_completion
    if completion:
        # Toggle existing completion
        completion.completed = not completion.completed
    else:
        # Create new completion
        data = request.get_json()
        completed = data.get('completed', True) if data else True
        completion = Completion(
            task_id=task.task_id,
            completed=completed,
            enthusiasm_score=0,
            mcq_percent=0,
            mains_score=0
        )
        db.session.add(completion)
    
    db.session.commit()
    return jsonify({'success': True, 'completed': completion.completed})

@bp.route('/tasks/<int:id>', methods=['DELETE'])
@login_required
def delete_task(id):
    """Delete a task"""
    task = Task.query.filter_by(task_id=id, user_id=current_user.id).first_or_404()
    db.session.delete(task)
    db.session.commit()
    return jsonify({'success': True})

@bp.route('/analytics')
@login_required
def analytics():
    """Analytics and reports"""
    # Get date range from query params
    days = request.args.get('days', 30, type=int)
    end_date = date.today()
    start_date = end_date - timedelta(days=days-1)
    
    # Daily scores
    daily_data = db.session.query(
        Task.planned_date,
        func.count(Task.task_id).label('total_tasks'),
        func.sum(case((Completion.completed == True, 1), else_=0)).label('completed_tasks'),
        func.sum(case(
            (Completion.completed == True, 
             case(
                 (Task.priority == 1, 1.25),
                 (Task.priority == 2, 1.0),
                 (Task.priority == 3, 0.85),
                 (Task.priority == 4, 0.70),
                 (Task.priority == 5, 0.50),
                 else_=1.0
             ) * 
             (0.5 * func.coalesce(Completion.enthusiasm_score, 0) / 10 + 
              0.5 * (func.coalesce(Completion.mcq_percent, 0) / 100 * 0.6 + 
                     func.coalesce(Completion.mains_score, 0) / 100 * 0.4))),
            else_=0
        )).label('weighted_score')
    ).select_from(Task).outerjoin(Completion).filter(
        Task.user_id == current_user.id,
        Task.planned_date >= start_date,
        Task.planned_date <= end_date
    ).group_by(Task.planned_date).all()
    
    # Subject-wise performance
    subject_data = db.session.query(
        Subject.name,
        func.count(Task.task_id).label('total_tasks'),
        func.sum(case((Completion.completed == True, 1), else_=0)).label('completed_tasks'),
        func.avg(Completion.enthusiasm_score).label('avg_enthusiasm')
    ).select_from(Subject).join(Topic).join(Task).outerjoin(Completion).filter(
        Task.user_id == current_user.id,
        Task.planned_date >= start_date
    ).group_by(Subject.name).all()
    
    # Calculate analytics summary
    total_tasks = sum(row.total_tasks for row in daily_data)
    completed_tasks = sum(row.completed_tasks for row in daily_data)
    completion_rate = int((completed_tasks / total_tasks * 100) if total_tasks > 0 else 0)
    
    # Get total sessions and hours (join through Task to filter by user)
    total_sessions = Session.query.join(Task).filter(
        Task.user_id == current_user.id,
        Session.start_time >= datetime.combine(start_date, datetime.min.time())
    ).count()
    
    total_minutes = db.session.query(
        func.sum(Session.duration_min)
    ).join(Task).filter(
        Task.user_id == current_user.id,
        Session.start_time >= datetime.combine(start_date, datetime.min.time())
    ).scalar() or 0
    total_hours = round(total_minutes / 60, 1)
    
    # Get goal stats
    total_goals = Goal.query.filter_by(user_id=current_user.id).count()
    completed_goals = Goal.query.filter_by(user_id=current_user.id, status='completed').count()
    
    # Calculate streaks (days with completed tasks)
    completed_dates = db.session.query(Task.planned_date).join(Completion).filter(
        Task.user_id == current_user.id,
        Completion.completed == True,
        Task.planned_date <= date.today()
    ).distinct().order_by(Task.planned_date.desc()).all()
    
    current_streak = 0
    check_date = date.today()
    for row in completed_dates:
        if row.planned_date == check_date or row.planned_date == check_date - timedelta(days=1):
            current_streak += 1
            check_date = row.planned_date - timedelta(days=1)
        else:
            break
    
    # Weekly stats
    week_start = date.today() - timedelta(days=date.today().weekday())
    weekly_hours = db.session.query(
        func.sum(Session.duration_min)
    ).join(Task).filter(
        Task.user_id == current_user.id,
        Session.start_time >= datetime.combine(week_start, datetime.min.time())
    ).scalar() or 0
    weekly_hours = round(weekly_hours / 60, 1)
    
    weekly_tasks = Task.query.join(Completion).filter(
        Task.user_id == current_user.id,
        Task.planned_date >= week_start,
        Completion.completed == True
    ).count()
    
    # Monthly milestones (completed goals this month)
    month_start = date.today().replace(day=1)
    monthly_milestones = Goal.query.filter(
        Goal.user_id == current_user.id,
        Goal.status == 'completed',
        Goal.created_at >= datetime.combine(month_start, datetime.min.time())
    ).count()
    
    analytics_data = {
        'total_sessions': total_sessions,
        'total_hours': total_hours,
        'productivity_score': completion_rate,
        'completion_rate': completion_rate,
        'focus_hours': total_hours,
        'current_streak': current_streak,
        'completed_goals': completed_goals,
        'total_goals': total_goals,
        'weekly_hours': weekly_hours,
        'weekly_tasks': weekly_tasks,
        'monthly_milestones': monthly_milestones
    }
    
    return render_template('main/analytics.html', 
                         daily_data=daily_data,
                         subject_data=subject_data,
                         analytics_data=analytics_data,
                         days=days)

@bp.route('/api/dashboard-data')
@login_required
def api_dashboard_data():
    """API endpoint for dashboard data"""
    today = date.today()
    
    today_tasks = Task.query.filter(
        Task.user_id == current_user.id,
        Task.planned_date == today
    ).all()
    
    data = {
        'today': {
            'total_tasks': len(today_tasks),
            'completed_tasks': sum(1 for task in today_tasks if task.is_completed),
            'total_score': sum(task.task_score for task in today_tasks),
            'tasks': [{
                'id': task.task_id,
                'topic': task.topic.topic_name,
                'subject': task.topic.subject.name,
                'priority': task.priority,
                'completed': task.is_completed,
                'score': task.task_score
            } for task in today_tasks]
        }
    }
    
    return jsonify(data)