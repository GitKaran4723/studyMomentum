"""
Prediction API Routes
Stage 2-5: Prediction endpoints with caching, analytics, and write operations
"""

import os
from flask import jsonify, request, current_app
from flask_login import login_required, current_user
from app.predict import bp
from app.models import Goal, Subject, Topic, Task
from app.services.predict import (
    simulate_daily_plan,
    compute_goal_status,
    ist_today
)
from app.predict.cache import cache_plan_response  # Stage 5: Caching


def is_prediction_enabled() -> bool:
    """Check if prediction features are enabled"""
    enabled = os.environ.get('PREDICTION_ENABLED', 'false').lower()
    return enabled in ['true', 'preview', 'preview_ui', '1', 'yes']


def prediction_required(f):
    """Decorator to guard prediction endpoints with feature flag"""
    from functools import wraps
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not is_prediction_enabled():
            return jsonify({
                'error': 'Prediction features are not enabled',
                'enabled': False
            }), 404
        return f(*args, **kwargs)
    
    return decorated_function


@bp.route('/plan', methods=['POST'])
@login_required
@prediction_required
@cache_plan_response()  # Stage 5: 5-minute caching
def generate_plan():
    """
    POST /api/predict/plan
    
    Generate a simulated daily study plan (READ-ONLY, no persistence)
    
    Request JSON:
    {
        "goal_id": 123,
        "daily_hours": 6.0,  // optional
        "split_new": 0.6     // optional (60% new, 40% revision)
    }
    
    Response JSON:
    {
        "goal_id": 123,
        "goal_name": "UPSC Prelims 2026",
        "date": "2025-10-17",
        "new_tasks": [
            {
                "task_id": 456,
                "task_name": "Ancient India",
                "subject_name": "History",
                "allocated_hours": 1.5,
                "mastery_before": 0.3,
                "mastery_after": 0.55,
                "sph_priority": 0.45,
                "derived": false  // true if from virtual task
            },
            ...
        ],
        "revision_tasks": [
            {
                "task_id": 789,
                "task_name": "Constitution Basics",
                "subject_name": "Polity",
                "allocated_hours": 0.8,
                "mastery_before": 0.7,
                "mastery_after": 0.82,
                "rpf_priority": 0.35,
                "days_since_last": 5,
                "derived": false
            },
            ...
        ],
        "summary": {
            "hours_new": 3.6,
            "hours_revision": 2.4,
            "total_hours": 6.0,
            "projected_gains": {
                "mu_before": 85.5,
                "mu_after": 92.3,
                "delta_mu": 6.8,
                "p_clear_before": 0.23,
                "p_clear_after": 0.35
            }
        }
    }
    """
    data = request.get_json() or {}
    goal_id = data.get('goal_id')
    
    if not goal_id:
        return jsonify({'error': 'goal_id is required'}), 400
    
    # Verify goal belongs to current user
    goal = Goal.query.filter_by(
        goal_id=goal_id,
        user_id=current_user.id
    ).first()
    
    if not goal:
        return jsonify({'error': 'Goal not found or access denied'}), 404
    
    # Get parameters with defaults from goal
    daily_hours = data.get('daily_hours', goal.daily_hours_default or 6.0)
    split_new = data.get('split_new', goal.split_new_default or 0.6)
    
    # Get all tasks for this goal
    tasks_query = Task.query.join(Topic).join(Subject).filter(
        Subject.goal_id == goal_id
    ).all()
    
    if not tasks_query:
        return jsonify({
            'error': 'No tasks found for this goal',
            'suggestion': 'Add topics and tasks first'
        }), 400
    
    # Convert to dict format for prediction service
    tasks_data = []
    for task in tasks_query:
        tasks_data.append({
            'task_id': task.task_id,
            'task_name': task.display_name,
            'subject_name': task.topic.subject.name if task.topic and task.topic.subject else 'Unknown',
            'concept_weight': task.concept_weight or 0.0,
            'mastery': task.mastery or 0.0,
            't_est_hours': task.t_est_hours or 4.0,
            'lambda_forgetting': task.lambda_forgetting or 0.04,
            'eta_learn': task.eta_learn or 0.8,
            'rho_revise': task.rho_revise or 0.35,
            'last_studied_at': task.last_studied_at,
            'spaced_stage': task.spaced_stage or 0,
            'task_type': task.task_type or 'learn'
        })
    
    # Generate plan (simulation only, no database changes)
    plan = simulate_daily_plan(
        tasks=tasks_data,
        daily_hours=daily_hours,
        split_new=split_new,
        today=ist_today()
    )
    
    # Format response
    return jsonify({
        'goal_id': goal_id,
        'goal_name': goal.goal_name or goal.title,
        'date': ist_today().isoformat(),
        'new_tasks': [
            {
                'task_id': t['task_id'],
                'task_name': t['task_name'],
                'subject_name': t['subject_name'],
                'allocated_hours': round(t.get('allocated_hours', 0.0), 2),
                'mastery_before': round(t.get('mastery_after_decay', 0.0), 3),
                'mastery_after': round(t.get('mastery_after_study', 0.0), 3),
                'sph_priority': round(t.get('sph_priority', 0.0), 4),
                'derived': t.get('derived', False)
            }
            for t in plan['new_tasks']
        ],
        'revision_tasks': [
            {
                'task_id': t['task_id'],
                'task_name': t['task_name'],
                'subject_name': t['subject_name'],
                'allocated_hours': round(t.get('allocated_hours', 0.0), 2),
                'mastery_before': round(t.get('mastery_after_decay', 0.0), 3),
                'mastery_after': round(t.get('mastery_after_study', 0.0), 3),
                'rpf_priority': round(t.get('rpf_priority', 0.0), 4),
                'days_since_last': t.get('days_since_last', 0),
                'derived': t.get('derived', False)
            }
            for t in plan['revision_tasks']
        ],
        'summary': {
            'hours_new': round(plan['hours_new'], 2),
            'hours_revision': round(plan['hours_revision'], 2),
            'total_hours': daily_hours,
            'projected_gains': {
                'mu_before': round(plan['projected_gains']['before']['mu'], 2),
                'mu_after': round(plan['projected_gains']['after']['mu'], 2),
                'delta_mu': round(plan['projected_gains']['after']['delta_mu'], 2),
                'p_clear_before': round(plan['projected_gains']['before']['p_clear_today'], 4),
                'p_clear_after': round(plan['projected_gains']['after']['p_clear_today'], 4)
            }
        },
        'metadata': {
            'simulation_only': True,
            'no_persistence': True,
            'derived_explanation': 'Tasks marked derived=true come from virtual tasks (subjects without real tasks)'
        }
    }), 200


@bp.route('/status', methods=['GET'])
@login_required
@prediction_required
def get_status():
    """
    GET /api/predict/status?goal_id=123
    
    Get comprehensive prediction status for a goal (READ-ONLY)
    
    Query Parameters:
    - goal_id: Required, ID of the goal
    
    Response JSON:
    {
        "goal_id": 123,
        "goal_name": "UPSC Prelims 2026",
        "current_state": {
            "mu": 85.5,              // Expected marks today
            "sigma2": 125.3,         // Variance
            "sigma": 11.2,           // Standard deviation
            "p_clear_today": 0.23    // Probability of clearing if exam were today
        },
        "exam_projection": {
            "exam_date": "2026-06-15",
            "days_remaining": 241,
            "mu_exam": 142.7,        // Projected marks at exam
            "p_clear_exam": 0.87     // Probability of clearing at exam
        },
        "task_statistics": {
            "total_tasks": 120,
            "mastered_tasks": 45,    // mastery >= 0.8
            "avg_mastery": 0.67,
            "completion_pct": 37.5
        },
        "threshold": {
            "marks": 120.0,
            "total_marks": 200.0,
            "required_pct": 60.0
        }
    }
    """
    goal_id = request.args.get('goal_id', type=int)
    
    if not goal_id:
        return jsonify({'error': 'goal_id query parameter is required'}), 400
    
    # Verify goal belongs to current user
    goal = Goal.query.filter_by(
        goal_id=goal_id,
        user_id=current_user.id
    ).first()
    
    if not goal:
        return jsonify({'error': 'Goal not found or access denied'}), 404
    
    # Get all tasks for this goal
    tasks_query = Task.query.join(Topic).join(Subject).filter(
        Subject.goal_id == goal_id
    ).all()
    
    if not tasks_query:
        return jsonify({
            'error': 'No tasks found for this goal',
            'suggestion': 'Add topics and tasks first, or run backfill to create virtual tasks'
        }), 400
    
    # Convert to dict format
    tasks_data = []
    for task in tasks_query:
        tasks_data.append({
            'task_id': task.task_id,
            'concept_weight': task.concept_weight or 0.0,
            'mastery': task.mastery or 0.0,
            't_est_hours': task.t_est_hours or 4.0,
            'lambda_forgetting': task.lambda_forgetting or 0.04,
            'eta_learn': task.eta_learn or 0.8,
            'rho_revise': task.rho_revise or 0.35,
            'last_studied_at': task.last_studied_at,
            'spaced_stage': task.spaced_stage or 0,
            'task_type': task.task_type or 'learn'
        })
    
    # Compute status (simulation only)
    status = compute_goal_status(
        tasks=tasks_data,
        threshold_marks=goal.threshold_marks or 120.0,
        exam_date=goal.exam_date,
        daily_hours=goal.daily_hours_default or 6.0,
        split_new=goal.split_new_default or 0.6,
        delta_decay=goal.delta_decay or 0.7,
        today=ist_today()
    )
    
    # Format response
    response = {
        'goal_id': goal_id,
        'goal_name': goal.goal_name or goal.title,
        'current_state': {
            'mu': round(status['mu'], 2),
            'sigma2': round(status['sigma2'], 2),
            'sigma': round(status['sigma2'] ** 0.5, 2),
            'p_clear_today': round(status['p_clear_today'], 4)
        },
        'task_statistics': {
            'total_tasks': status['total_tasks'],
            'mastered_tasks': status['mastered_tasks'],
            'avg_mastery': round(status['avg_mastery'], 3),
            'completion_pct': round((status['mastered_tasks'] / status['total_tasks'] * 100) if status['total_tasks'] > 0 else 0, 1)
        },
        'threshold': {
            'marks': status['threshold_marks'],
            'total_marks': status['threshold_marks'] * 1.67,  # Approximate
            'required_pct': round((status['threshold_marks'] / (status['threshold_marks'] * 1.67)) * 100, 1)
        },
        'metadata': {
            'simulation_only': True,
            'no_persistence': True,
            'computed_at': ist_today().isoformat()
        }
    }
    
    # Add exam projection if exam_date is set
    if goal.exam_date and status['days_remaining'] > 0:
        response['exam_projection'] = {
            'exam_date': goal.exam_date.isoformat(),
            'days_remaining': status['days_remaining'],
            'mu_exam': round(status['mu_exam'], 2),
            'p_clear_exam': round(status['p_clear_exam'], 4)
        }
    else:
        response['exam_projection'] = {
            'message': 'Set exam_date in goal to see projections'
        }
    
    return jsonify(response), 200


@bp.route('/health', methods=['GET'])
@prediction_required
def health_check():
    """Health check endpoint for prediction service"""
    return jsonify({
        'service': 'prediction',
        'status': 'operational',
        'stage': 4,  # Updated to Stage 4
        'features': {
            'daily_planning': True,
            'goal_status': True,
            'persistence': is_write_enabled(),  # Stage 4 write operations
            'bayesian_updates': is_write_enabled(),  # Stage 4
            'background_jobs': False  # Coming in future
        }
    }), 200


# ==================== Stage 4: Write Operations ====================

def is_write_enabled() -> bool:
    """Check if write operations are enabled (Stage 4)"""
    enabled = os.environ.get('PREDICTION_ENABLED', 'false').lower()
    return enabled in ['on', 'true', '1']


def write_required(f):
    """Decorator for write-enabled endpoints"""
    from functools import wraps
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not is_write_enabled():
            return jsonify({
                'error': 'Write operations disabled',
                'message': 'Set PREDICTION_ENABLED=on to enable write operations',
                'current_mode': os.environ.get('PREDICTION_ENABLED', 'false')
            }), 403
        return f(*args, **kwargs)
    return decorated_function


@bp.route('/apply-plan', methods=['POST'])
@login_required
@prediction_required
@write_required
def apply_plan():
    """
    Apply a daily plan to actual tasks (Stage 4)
    
    Request:
    {
        "idempotency_key": "uuid-string",  // Required for idempotency
        "goal_id": 1,
        "plan_date": "2025-10-17",
        "tasks": [
            {
                "task_id": 123,  // existing task ID or null for virtual
                "subject_id": 5,
                "topic_id": 10,
                "task_name": "Linear Algebra",
                "mode": "learn",  // or "revise"
                "alloc_hours": 1.5,
                "expected_mastery_gain": 0.25
            },
            ...
        ]
    }
    
    Response:
    {
        "success": true,
        "applied_tasks": 5,
        "created_tasks": 2,
        "updated_tasks": 3,
        "snapshot": {
            "mu_before": 45.5,
            "mu_after": 48.2,
            "delta_mu_day": 2.7,
            "p_clear_before": 0.35,
            "p_clear_after": 0.42
        }
    }
    """
    import hashlib
    import json
    from app.extensions import db
    from app.models import Goal, Task, Topic, Subject, DailySnapshot, IdempotencyLog
    from app.services.predict import (
        ist_today, days_since, apply_decay, learn_update, revise_update,
        bayes_init, compute_goal_status
    )
    
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data or 'idempotency_key' not in data:
            return jsonify({'error': 'idempotency_key required'}), 400
        
        if 'goal_id' not in data:
            return jsonify({'error': 'goal_id required'}), 400
        
        if 'tasks' not in data or not isinstance(data['tasks'], list):
            return jsonify({'error': 'tasks array required'}), 400
        
        idempotency_key = data['idempotency_key']
        goal_id = data['goal_id']
        plan_date_str = data.get('plan_date', str(ist_today()))
        plan_date = ist_today()  # Always use today for safety
        tasks_data = data['tasks']
        
        # Validate goal ownership
        goal = Goal.query.filter_by(
            goal_id=goal_id,
            user_id=current_user.id
        ).first_or_404()
        
        # Check idempotency - return cached response if duplicate
        request_hash = hashlib.sha256(
            json.dumps(data, sort_keys=True).encode()
        ).hexdigest()
        
        existing_log = IdempotencyLog.query.filter_by(
            idempotency_key=idempotency_key
        ).first()
        
        if existing_log:
            # Return cached response
            if existing_log.response_data:
                return jsonify(json.loads(existing_log.response_data)), 200
            else:
                return jsonify({'error': 'Duplicate request detected'}), 409
        
        # Calculate mu_before for comparison
        status_before = compute_goal_status(goal)
        mu_before = status_before['current_state']['mu']
        sigma_before = status_before['current_state']['sigma']
        p_clear_before = status_before['current_state']['p_clear_today']
        
        # Track changes
        created_count = 0
        updated_count = 0
        task_ids_updated = []
        
        # BEGIN TRANSACTION
        try:
            for task_data in tasks_data:
                mode = task_data.get('mode', 'learn')
                alloc_hours = float(task_data.get('alloc_hours', 0))
                task_id = task_data.get('task_id')
                
                if alloc_hours <= 0:
                    continue  # Skip invalid allocations
                
                # Get or create task
                if task_id:
                    # Update existing task
                    task = Task.query.filter_by(
                        task_id=task_id,
                        user_id=current_user.id
                    ).with_for_update().first()  # Row-level lock
                    
                    if not task:
                        continue  # Skip if not found or not owned
                    
                else:
                    # Create virtual task (no task_id)
                    subject_id = task_data.get('subject_id')
                    topic_id = task_data.get('topic_id')
                    task_name = task_data.get('task_name', 'Virtual Task')
                    
                    if not subject_id or not topic_id:
                        continue  # Skip invalid virtual tasks
                    
                    # Verify ownership of subject/topic
                    topic = Topic.query.join(Subject).filter(
                        Topic.topic_id == topic_id,
                        Subject.subject_id == subject_id,
                        Subject.goal_id == goal_id
                    ).first()
                    
                    if not topic:
                        continue  # Invalid topic
                    
                    # Create new task
                    task = Task(
                        user_id=current_user.id,
                        topic_id=topic_id,
                        task_name=task_name,
                        planned_date=plan_date,
                        priority=3,  # Default medium priority
                        est_hours_per_unit=alloc_hours,
                        planned_duration_min=int(alloc_hours * 60)
                    )
                    db.session.add(task)
                    db.session.flush()  # Get task_id
                    created_count += 1
                
                # Apply decay first if last_studied_at exists
                if task.last_studied_at:
                    days = days_since(task.last_studied_at)
                    if days > 0:
                        decay_lambda = goal.delta_decay or 0.04
                        task.mastery = apply_decay(task.mastery, decay_lambda, days)
                
                # Store old mastery for update calculation
                old_mastery = task.mastery
                
                # Apply learn or revise update
                if mode == 'learn':
                    eta = 0.8  # Learning rate
                    t_est = task.est_hours_per_unit or 10.0
                    delta_m = learn_update(old_mastery, eta, alloc_hours, t_est)
                    task.mastery = min(1.0, old_mastery + delta_m)
                    
                elif mode == 'revise':
                    rho = 0.35  # Revision boost
                    t_est = task.est_hours_per_unit or 10.0
                    delta_m = revise_update(old_mastery, rho, alloc_hours, t_est)
                    task.mastery = min(1.0, old_mastery + delta_m)
                    
                    # Update spaced repetition stage
                    current_stage = task.spaced_stage or 0
                    task.spaced_stage = min(current_stage + 1, 4)  # Max stage 4
                
                # Update last_studied_at
                task.last_studied_at = plan_date
                
                # Initialize Bayesian if missing
                if task.bayesian_alpha is None or task.bayesian_beta is None:
                    alpha, beta = bayes_init(task.mastery)
                    task.bayesian_alpha = alpha
                    task.bayesian_beta = beta
                
                # Update last_decay_date
                task.last_decay_date = plan_date
                
                # Increment version for optimistic locking
                if hasattr(task, 'version'):
                    task.version = (task.version or 0) + 1
                
                task_ids_updated.append(task.task_id)
                updated_count += 1
            
            # Calculate mu_after
            db.session.flush()  # Ensure all updates are visible
            status_after = compute_goal_status(goal)
            mu_after = status_after['current_state']['mu']
            sigma_after = status_after['current_state']['sigma']
            p_clear_after = status_after['current_state']['p_clear_today']
            
            delta_mu_day = mu_after - mu_before
            
            # Create/update DailySnapshot
            snapshot = DailySnapshot.query.filter_by(
                snapshot_date=plan_date,
                user_id=current_user.id
            ).first()
            
            if not snapshot:
                snapshot = DailySnapshot(
                    snapshot_date=plan_date,
                    user_id=current_user.id
                )
                db.session.add(snapshot)
            
            # Update snapshot with prediction data
            snapshot.mu = mu_after
            snapshot.sigma2 = sigma_after ** 2
            snapshot.p_clear_today = p_clear_after
            snapshot.delta_mu_day = delta_mu_day
            snapshot.hours_planned = sum(t.get('alloc_hours', 0) for t in tasks_data)
            snapshot.learning_gain_marks = delta_mu_day
            
            # Add exam projection if available
            if status_after.get('exam_projection'):
                snapshot.mu_exam = status_after['exam_projection'].get('mu_exam')
                snapshot.p_clear_exam = status_after['exam_projection'].get('p_clear_exam')
            
            # Create idempotency log
            response_data = {
                'success': True,
                'applied_tasks': len(task_ids_updated),
                'created_tasks': created_count,
                'updated_tasks': updated_count,
                'task_ids': task_ids_updated,
                'snapshot': {
                    'mu_before': round(mu_before, 2),
                    'mu_after': round(mu_after, 2),
                    'delta_mu_day': round(delta_mu_day, 2),
                    'sigma_after': round(sigma_after, 2),
                    'p_clear_before': round(p_clear_before, 4),
                    'p_clear_after': round(p_clear_after, 4)
                },
                'metadata': {
                    'plan_date': str(plan_date),
                    'goal_id': goal_id,
                    'persistence': True
                }
            }
            
            idem_log = IdempotencyLog(
                idempotency_key=idempotency_key,
                user_id=current_user.id,
                goal_id=goal_id,
                operation_type='apply_plan',
                operation_date=plan_date,
                request_hash=request_hash,
                response_data=json.dumps(response_data)
            )
            db.session.add(idem_log)
            
            # Stage 5: Check for virtual task retirement
            from app.services.retirement import auto_retire_check
            retirement_log = auto_retire_check(goal_id)
            if retirement_log:
                response_data['retirement'] = retirement_log
                current_app.logger.info(f"Auto-retired virtual tasks: {retirement_log}")
            
            # COMMIT TRANSACTION
            db.session.commit()
            
            return jsonify(response_data), 200
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Apply plan transaction failed: {e}")
            raise
            
    except Exception as e:
        current_app.logger.error(f"Apply plan error: {e}")
        return jsonify({
            'error': 'Failed to apply plan',
            'message': str(e)
        }), 500


@bp.route('/quiz', methods=['POST'])
@login_required
@prediction_required
@write_required
def quiz_update():
    """
    Update task mastery based on quiz/MCQ performance (Stage 4)
    
    Request:
    {
        "idempotency_key": "uuid-string",
        "task_id": 123,
        "mcq_percent": 75.0,  // MCQ score percentage
        "mains_score": 65.0,  // Optional mains score
        "total_questions": 20  // Optional, default 20
    }
    
    Response:
    {
        "success": true,
        "task_id": 123,
        "mastery_before": 0.65,
        "mastery_after": 0.72,
        "bayesian": {
            "alpha": 14.4,
            "beta": 5.6
        }
    }
    """
    import hashlib
    import json
    from app.extensions import db
    from app.models import Task, IdempotencyLog
    from app.services.predict import quiz_update as quiz_update_fn, mastery_from_beta
    
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data or 'idempotency_key' not in data:
            return jsonify({'error': 'idempotency_key required'}), 400
        
        if 'task_id' not in data:
            return jsonify({'error': 'task_id required'}), 400
        
        if 'mcq_percent' not in data:
            return jsonify({'error': 'mcq_percent required'}), 400
        
        idempotency_key = data['idempotency_key']
        task_id = data['task_id']
        mcq_percent = float(data['mcq_percent'])
        mains_score = float(data.get('mains_score', 0))
        total_questions = int(data.get('total_questions', 20))
        
        # Validate ranges
        if not (0 <= mcq_percent <= 100):
            return jsonify({'error': 'mcq_percent must be 0-100'}), 400
        
        if mains_score and not (0 <= mains_score <= 100):
            return jsonify({'error': 'mains_score must be 0-100'}), 400
        
        # Check idempotency
        request_hash = hashlib.sha256(
            json.dumps(data, sort_keys=True).encode()
        ).hexdigest()
        
        existing_log = IdempotencyLog.query.filter_by(
            idempotency_key=idempotency_key
        ).first()
        
        if existing_log:
            if existing_log.response_data:
                return jsonify(json.loads(existing_log.response_data)), 200
            else:
                return jsonify({'error': 'Duplicate request detected'}), 409
        
        # Get task with row lock
        task = Task.query.filter_by(
            task_id=task_id,
            user_id=current_user.id
        ).with_for_update().first_or_404()
        
        mastery_before = task.mastery
        
        # Convert MCQ% to k/n
        k_correct = int((mcq_percent / 100.0) * total_questions)
        n_total = total_questions
        
        # Get current Bayesian params (or initialize)
        alpha = task.bayesian_alpha or 1.0
        beta = task.bayesian_beta or 1.0
        
        # Apply Bayesian update
        alpha_new, beta_new = quiz_update_fn(alpha, beta, k_correct, n_total)
        
        # Calculate new mastery from Beta distribution
        mastery_new = mastery_from_beta(alpha_new, beta_new)
        
        # Apply mains floor if provided
        if mains_score > 0:
            mains_floor = (mains_score / 100.0) * 0.8  # 80% of mains score as floor
            mastery_new = max(mastery_new, mains_floor)
        
        # Update task
        task.bayesian_alpha = alpha_new
        task.bayesian_beta = beta_new
        task.mastery = mastery_new
        
        # Increment version
        if hasattr(task, 'version'):
            task.version = (task.version or 0) + 1
        
        # Prepare response
        response_data = {
            'success': True,
            'task_id': task_id,
            'mastery_before': round(mastery_before, 4),
            'mastery_after': round(mastery_new, 4),
            'delta_mastery': round(mastery_new - mastery_before, 4),
            'bayesian': {
                'alpha': round(alpha_new, 2),
                'beta': round(beta_new, 2)
            },
            'quiz_data': {
                'mcq_percent': mcq_percent,
                'correct': k_correct,
                'total': n_total,
                'mains_score': mains_score if mains_score > 0 else None
            },
            'metadata': {
                'persistence': True
            }
        }
        
        # Create idempotency log
        idem_log = IdempotencyLog(
            idempotency_key=idempotency_key,
            user_id=current_user.id,
            goal_id=task.topic.subject.goal_id,
            operation_type='quiz',
            operation_date=ist_today(),
            request_hash=request_hash,
            response_data=json.dumps(response_data)
        )
        db.session.add(idem_log)
        
        # Commit transaction
        db.session.commit()
        
        return jsonify(response_data), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Quiz update error: {e}")
        return jsonify({
            'error': 'Failed to update quiz results',
            'message': str(e)
        }), 500


@bp.route('/analytics', methods=['GET'])
@login_required
@prediction_required
def analytics_dashboard():
    """
    GET /api/predict/analytics?goal_id=X&days=30
    
    Stage 5: Analytics dashboard data
    Returns trends, subject contributions, and marginal task suggestions
    """
    try:
        goal_id = request.args.get('goal_id', type=int)
        days = request.args.get('days', 30, type=int)
        
        if not goal_id:
            return jsonify({'error': 'goal_id required'}), 400
        
        # Verify goal ownership
        goal = Goal.query.get_or_404(goal_id)
        if goal.user_id != current_user.id:
            return jsonify({'error': 'Access denied'}), 403
        
        from app.models import DailySnapshot
        from datetime import datetime, timedelta
        from app.services.predict import ist_today
        
        # Get trend data from daily snapshots
        start_date = ist_today() - timedelta(days=days)
        snapshots = DailySnapshot.query.filter(
            DailySnapshot.user_id == current_user.id,
            DailySnapshot.snapshot_date >= start_date
        ).order_by(DailySnapshot.snapshot_date).all()
        
        trends = []
        for snap in snapshots:
            trends.append({
                'date': snap.snapshot_date.isoformat(),
                'mu': round(snap.mu or 0, 2),
                'p_clear': round((snap.p_clear_exam or 0) * 100, 1),
                'delta_mu_day': round(snap.delta_mu_day or 0, 2)
            })
        
        # Calculate subject contributions
        subjects = Subject.query.filter_by(goal_id=goal_id).all()
        subject_contributions = []
        total_mu = 0
        
        for subject in subjects:
            # Get tasks for this subject
            tasks = Task.query.join(Topic).filter(
                Topic.subject_id == subject.subject_id,
                Task.retired_at == None  # Exclude retired tasks
            ).all()
            
            # Calculate contribution: sum(mastery * concept_weight * threshold)
            threshold = goal.threshold_marks or 100
            subject_mu = sum(
                (t.mastery or 0) * (t.concept_weight or 0) * threshold
                for t in tasks
            )
            total_mu += subject_mu
            
            subject_contributions.append({
                'id': subject.subject_id,
                'name': subject.name,
                'contribution': round(subject_mu, 2),
                'percentage': 0  # Will calculate after we know total
            })
        
        # Calculate percentages
        if total_mu > 0:
            for sc in subject_contributions:
                sc['percentage'] = round((sc['contribution'] / total_mu) * 100, 1)
        
        # Find top marginal Δμ tasks (highest efficiency)
        all_tasks = Task.query.join(Topic).join(Subject).filter(
            Subject.goal_id == goal_id,
            Task.retired_at == None,
            Task.mastery < 0.9  # Only consider tasks not yet mastered
        ).all()
        
        marginal_tasks = []
        for task in all_tasks:
            if not task.t_est_hours or task.t_est_hours == 0:
                continue
            
            # Estimate marginal gain: 30 minutes of study
            hours_delta = 0.5
            current_mastery = task.mastery or 0
            concept_weight = task.concept_weight or 0
            threshold = goal.threshold_marks or 100
            
            # Simple estimation: gain = hours * eta * weight * threshold
            eta = task.eta_learn if task.task_type == 'learn' else task.rho_revise
            delta_mu = hours_delta * (eta or 0.8) * concept_weight * threshold * (1 - current_mastery)
            efficiency = delta_mu / hours_delta if hours_delta > 0 else 0
            
            marginal_tasks.append({
                'id': task.task_id,
                'name': task.display_name,
                'subject': task.topic.subject.name if task.topic else 'Unknown',
                'delta_mu': round(delta_mu, 2),
                'efficiency': round(efficiency, 2),
                'estimated_hours': round(task.t_est_hours, 1),
                'current_mastery': round(current_mastery, 3)
            })
        
        # Sort by efficiency and take top 5
        marginal_tasks.sort(key=lambda x: x['efficiency'], reverse=True)
        top_marginal = marginal_tasks[:5]
        
        # Calculate days to exam
        days_to_exam = 0
        if goal.exam_date:
            days_to_exam = (goal.exam_date - ist_today()).days
        
        # Calculate efficiency (simplified)
        efficiency = 0
        if len(trends) > 1:
            first_mu = trends[0]['mu']
            last_mu = trends[-1]['mu']
            days_count = len(trends)
            if days_count > 0 and total_mu > 0:
                efficiency = round(((last_mu - first_mu) / days_count / total_mu) * 100, 1)
        
        return jsonify({
            'success': True,
            'trends': trends,
            'subject_contributions': subject_contributions,
            'top_marginal_tasks': top_marginal,
            'days_to_exam': days_to_exam,
            'efficiency': efficiency,
            'metadata': {
                'goal_id': goal_id,
                'days_requested': days,
                'snapshots_found': len(snapshots)
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Analytics error: {e}")
        return jsonify({
            'error': 'Failed to load analytics',
            'message': str(e)
        }), 500
