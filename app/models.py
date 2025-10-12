"""
Database models for Goal Tracker application
Based on the comprehensive SQLite schema provided
"""

from datetime import datetime, date
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import CheckConstraint
from app.extensions import db

class User(UserMixin, db.Model):
    """User model with admin capabilities"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    
    # Relationships
    tasks = db.relationship('Task', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    goals = db.relationship('Goal', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    
    def set_password(self, password):
        """Set password hash"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check password against hash"""
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'

class Subject(db.Model):
    """Subject master table - now linked to goals"""
    __tablename__ = 'subjects'
    
    subject_id = db.Column(db.Integer, primary_key=True)
    goal_id = db.Column(db.Integer, db.ForeignKey('goals.goal_id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    short_code = db.Column(db.String(10))
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    goal = db.relationship('Goal', backref=db.backref('subjects', lazy='dynamic', cascade='all, delete-orphan'))
    topics = db.relationship('Topic', backref='subject', lazy='dynamic', cascade='all, delete-orphan')
    
    @property
    def completion_percentage(self):
        """Calculate subject completion based on tasks"""
        total_tasks = Task.query.join(Topic).filter(
            Topic.subject_id == self.subject_id
        ).count()
        
        if total_tasks == 0:
            return 0
        
        completed_tasks = Task.query.join(Topic).join(Completion).filter(
            Topic.subject_id == self.subject_id,
            Completion.completed == True
        ).count()
        
        return round((completed_tasks / total_tasks) * 100, 1)
    
    @property
    def total_tasks(self):
        """Get total tasks for this subject"""
        return Task.query.join(Topic).filter(Topic.subject_id == self.subject_id).count()
    
    @property
    def completed_tasks(self):
        """Get completed tasks for this subject"""
        return Task.query.join(Topic).join(Completion).filter(
            Topic.subject_id == self.subject_id,
            Completion.completed == True
        ).count()
    
    def __repr__(self):
        return f'<Subject {self.name}>'

class Topic(db.Model):
    """Topics (micro-concepts) - subdivisions of subjects"""
    __tablename__ = 'topics'
    
    topic_id = db.Column(db.Integer, primary_key=True)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.subject_id'), nullable=False)
    topic_name = db.Column(db.String(200), nullable=False)
    syllabus_ref = db.Column(db.String(200))
    default_priority = db.Column(db.Integer, default=2, nullable=False)
    suggested_source = db.Column(db.Text)
    doc_link = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        CheckConstraint('default_priority >= 1 AND default_priority <= 5'),
    )
    
    # Relationships
    tasks = db.relationship('Task', backref='topic', lazy='dynamic', cascade='all, delete-orphan')
    goal_topics = db.relationship('GoalTopic', backref='topic', lazy='dynamic', cascade='all, delete-orphan')
    
    @property
    def completion_percentage(self):
        """Calculate topic completion based on tasks"""
        total_tasks = self.tasks.count()
        if total_tasks == 0:
            return 0
        
        completed_tasks = Task.query.join(Completion).filter(
            Task.topic_id == self.topic_id,
            Completion.completed == True
        ).count()
        
        return round((completed_tasks / total_tasks) * 100, 1)
    
    @property
    def total_tasks(self):
        """Get total tasks for this topic"""
        return self.tasks.count()
    
    @property
    def completed_tasks(self):
        """Get completed tasks for this topic"""
        return Task.query.join(Completion).filter(
            Task.topic_id == self.topic_id,
            Completion.completed == True
        ).count()
    
    def __repr__(self):
        return f'<Topic {self.topic_name}>'

class Goal(db.Model):
    """High-level goals (monthly/SSB/UGC/Prelims etc.)"""
    __tablename__ = 'goals'
    
    goal_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)  # Main title column (NOT NULL in DB)
    goal_name = db.Column(db.Text)  # Additional name field
    description = db.Column(db.Text)
    start_date = db.Column(db.Date)
    target_date = db.Column(db.Date)
    goal_type = db.Column(db.Text)
    target_value = db.Column(db.Integer)
    unit = db.Column(db.Text)
    success_criteria = db.Column(db.Text)
    reward = db.Column(db.Text)
    status = db.Column(db.String(20), default='active')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Computed properties for compatibility
    @property
    def id(self):
        return self.goal_id
    
    # Relationships
    goal_topics = db.relationship('GoalTopic', backref='goal', lazy='dynamic', cascade='all, delete-orphan')
    
    @property
    def progress_percentage(self):
        """Calculate goal completion percentage from all tasks across subjects"""
        # Get all tasks for this goal through Subject → Topic → Task hierarchy
        total_tasks = Task.query.join(Topic).join(Subject).filter(
            Subject.goal_id == self.goal_id
        ).count()
        
        if total_tasks == 0:
            return 0
        
        completed_tasks = Task.query.join(Topic).join(Subject).join(Completion).filter(
            Subject.goal_id == self.goal_id,
            Completion.completed == True
        ).count()
        
        return round((completed_tasks / total_tasks) * 100, 1)
    
    @property
    def total_tasks(self):
        """Get total tasks for this goal"""
        return Task.query.join(Topic).join(Subject).filter(
            Subject.goal_id == self.goal_id
        ).count()
    
    @property
    def completed_tasks_count(self):
        """Get count of completed tasks for this goal"""
        return Task.query.join(Topic).join(Subject).join(Completion).filter(
            Subject.goal_id == self.goal_id,
            Completion.completed == True
        ).count()
    
    def __repr__(self):
        return f'<Goal {self.title}>'

class GoalTopic(db.Model):
    """Link topics to goals (many-to-many)"""
    __tablename__ = 'goal_topics'
    
    goal_topic_id = db.Column(db.Integer, primary_key=True)
    goal_id = db.Column(db.Integer, db.ForeignKey('goals.goal_id'), nullable=False)
    topic_id = db.Column(db.Integer, db.ForeignKey('topics.topic_id'), nullable=False)
    must_complete = db.Column(db.Boolean, default=True)
    
    def __repr__(self):
        return f'<GoalTopic {self.goal_id}-{self.topic_id}>'

class Task(db.Model):
    """Tasks: schedule a topic for a date or range"""
    __tablename__ = 'tasks'
    
    task_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    goal_id = db.Column(db.Integer, db.ForeignKey('goals.goal_id'))
    topic_id = db.Column(db.Integer, db.ForeignKey('topics.topic_id'), nullable=False)
    planned_date = db.Column(db.Date, nullable=False)
    planned_start = db.Column(db.String(10))  # HH:MM format
    planned_duration_min = db.Column(db.Integer)
    priority = db.Column(db.Integer, nullable=False)
    ssb_warmup = db.Column(db.Boolean, default=False)
    ugc_related = db.Column(db.Boolean, default=False)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        CheckConstraint('priority >= 1 AND priority <= 5'),
        db.UniqueConstraint('user_id', 'topic_id', 'planned_date', name='unique_user_topic_date'),
    )
    
    # Relationships
    goal = db.relationship('Goal', backref=db.backref('tasks', lazy='dynamic'))
    sessions = db.relationship('Session', backref='task', lazy='dynamic', cascade='all, delete-orphan')
    completions = db.relationship('Completion', backref='task', lazy='dynamic', cascade='all, delete-orphan')
    
    @property
    def latest_completion(self):
        """Get the latest completion for this task"""
        return self.completions.order_by(Completion.completion_id.desc()).first()
    
    @property
    def is_completed(self):
        """Check if task is completed"""
        completion = self.latest_completion
        return completion and completion.completed
    
    @property
    def status(self):
        """Get task status based on completion"""
        if self.is_completed:
            return 'completed'
        completion = self.latest_completion
        if completion and not completion.completed:
            return 'in_progress'
        return 'pending'
    
    @property
    def task_score(self):
        """Calculate task score based on completion and enthusiasm"""
        completion = self.latest_completion
        if not completion:
            return 0
        
        # Priority weights (P1=1.25, P2=1.0, P3=0.85, P4=0.70, P5=0.50)
        priority_weights = {1: 1.25, 2: 1.0, 3: 0.85, 4: 0.70, 5: 0.50}
        w_priority = priority_weights.get(self.priority, 1.0)
        
        # Normalize enthusiasm (0-10 -> 0-1)
        e_norm = (completion.enthusiasm_score or 0) / 10
        
        # Quality factor from MCQ and Mains scores
        mcq_norm = (completion.mcq_percent or 0) / 100
        mains_norm = (completion.mains_score or 0) / 100
        q = 0.6 * mcq_norm + 0.4 * mains_norm
        
        # Completion multiplier
        c = 1 if completion.completed else 0.2
        
        # Task score formula
        task_score = w_priority * (0.5 * e_norm + 0.5 * q) * c
        return round(task_score, 3)
    
    def __repr__(self):
        return f'<Task {self.task_id}: {self.topic.topic_name}>'

class Session(db.Model):
    """Study sessions (optional): multiple sessions can belong to a task"""
    __tablename__ = 'sessions'
    
    session_id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('tasks.task_id'), nullable=False)
    start_time = db.Column(db.DateTime)
    end_time = db.Column(db.DateTime)
    duration_min = db.Column(db.Integer)
    remark = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Session {self.session_id}>'

class Completion(db.Model):
    """Completions: record completion of a task with quality indicators"""
    __tablename__ = 'completions'
    
    completion_id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('tasks.task_id'), nullable=False)
    completion_date = db.Column(db.Date, default=date.today)
    completed = db.Column(db.Boolean, default=False)
    enthusiasm_score = db.Column(db.Integer)
    mcq_percent = db.Column(db.Float)
    mains_score = db.Column(db.Float)
    notes_link = db.Column(db.Text)
    attempts = db.Column(db.Integer, default=1)
    is_final = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        CheckConstraint('enthusiasm_score >= 0 AND enthusiasm_score <= 10'),
        CheckConstraint('mcq_percent >= 0 AND mcq_percent <= 100'),
        CheckConstraint('mains_score >= 0 AND mains_score <= 100'),
    )
    
    def __repr__(self):
        return f'<Completion {self.completion_id}>'

class DailySnapshot(db.Model):
    """Store aggregated daily snapshots for quick dashboard"""
    __tablename__ = 'daily_snapshots'
    
    snapshot_date = db.Column(db.Date, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    total_tasks_planned = db.Column(db.Integer)
    total_tasks_done = db.Column(db.Integer)
    weighted_score = db.Column(db.Float)
    total_duration_min = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<DailySnapshot {self.snapshot_date}>'