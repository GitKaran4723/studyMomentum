"""Main application forms"""
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, IntegerField, DateField, SelectField, BooleanField, FloatField, SubmitField
from wtforms.validators import DataRequired, Length, NumberRange, Optional, URL, ValidationError
from datetime import date

class SubjectForm(FlaskForm):
    goal_id = SelectField('Goal', coerce=int, validators=[DataRequired(message='Select a goal')])
    name = StringField('Subject Name', validators=[DataRequired(), Length(max=100)])
    short_code = StringField('Short Code', validators=[Length(max=10)])
    description = TextAreaField('Description')
    submit = SubmitField('Save Subject')

class TopicForm(FlaskForm):
    topic_name = StringField('Topic Name', validators=[DataRequired(), Length(max=200)])
    subject_id = SelectField('Subject', coerce=int, validators=[DataRequired()])
    syllabus_ref = StringField('Syllabus Reference', validators=[Length(max=200)])
    default_priority = SelectField('Default Priority', choices=[
        (1, 'P1 - Highest'), (2, 'P2 - High'), (3, 'P3 - Medium'), 
        (4, 'P4 - Low'), (5, 'P5 - Lowest')
    ], coerce=int, default=2)
    suggested_source = TextAreaField('Suggested Source')
    doc_link = StringField('Documentation Link', validators=[Optional(), URL()])
    submit = SubmitField('Save Topic')

class GoalForm(FlaskForm):
    goal_name = StringField('Goal Name', validators=[DataRequired(), Length(max=200)])
    description = TextAreaField('Description')
    goal_type = SelectField('Goal Type', choices=[
        ('learning', 'Learning'), ('fitness', 'Fitness'), ('career', 'Career'), 
        ('personal', 'Personal'), ('other', 'Other')
    ], default='learning')
    target_date = DateField('Target Date', validators=[DataRequired()])
    target_value = IntegerField('Target Value', validators=[Optional(), NumberRange(min=1)])
    unit = StringField('Unit', validators=[Optional(), Length(max=50)])
    success_criteria = TextAreaField('Success Criteria')
    reward = StringField('Achievement Reward', validators=[Optional(), Length(max=200)])
    status = SelectField('Status', choices=[
        ('active', 'Active'), ('completed', 'Completed'), ('paused', 'Paused')
    ], default='active')
    submit = SubmitField('Save Goal')

class TaskForm(FlaskForm):
    goal_id = SelectField('Goal', coerce=int, validators=[DataRequired(message='Select a goal')])
    topic_id = SelectField('Topic', coerce=int, validators=[DataRequired()])
    task_name = StringField('Task Name', validators=[DataRequired(), Length(max=200)])
    planned_date = DateField('Planned Date', validators=[DataRequired()], default=date.today)
    planned_start = StringField('Start Time (HH:MM)', validators=[Optional()])
    planned_duration_min = IntegerField('Duration (minutes)', validators=[Optional(), NumberRange(min=1)])
    priority = SelectField('Priority', choices=[
        (1, 'P1 - Highest'), (2, 'P2 - High'), (3, 'P3 - Medium'), 
        (4, 'P4 - Low'), (5, 'P5 - Lowest')
    ], coerce=int, validators=[DataRequired()])
    ssb_warmup = BooleanField('SSB Warmup')
    ugc_related = BooleanField('UGC Related')
    notes = TextAreaField('Notes')
    submit = SubmitField('Save Task')

    def validate_goal_id(self, field):
        if field.data <= 0:
            raise ValidationError('Please choose a goal for this task.')

class CompletionForm(FlaskForm):
    completed = BooleanField('Task Completed', default=True)
    enthusiasm_score = IntegerField('Enthusiasm Score (0-10)', validators=[
        Optional(), NumberRange(min=0, max=10)])
    mcq_percent = FloatField('MCQ Score (%)', validators=[
        Optional(), NumberRange(min=0, max=100)])
    mains_score = FloatField('Mains Score (%)', validators=[
        Optional(), NumberRange(min=0, max=100)])
    notes_link = StringField('Notes Link', validators=[Optional(), URL()])
    submit = SubmitField('Save Completion')

class SessionForm(FlaskForm):
    start_time = StringField('Start Time', validators=[Optional()])
    end_time = StringField('End Time', validators=[Optional()])
    duration_min = IntegerField('Duration (minutes)', validators=[Optional(), NumberRange(min=1)])
    remark = TextAreaField('Remarks')
    submit = SubmitField('Save Session')