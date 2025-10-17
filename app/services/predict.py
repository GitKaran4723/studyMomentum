"""
Stage 2: Core Prediction Engine
Pure functions for mastery tracking, spaced repetition, Bayesian updates, and probability calculations
All functions are simulation-only (no database writes)
"""

import math
from datetime import date, datetime, timedelta
from typing import Tuple, List, Dict, Optional
import pytz

# IST Timezone helpers
IST = pytz.timezone('Asia/Kolkata')

def ist_today() -> date:
    """Get current date in IST timezone"""
    return datetime.now(IST).date()

def ist_now() -> datetime:
    """Get current datetime in IST timezone"""
    return datetime.now(IST)

def days_since(last_date: Optional[date], today: Optional[date] = None) -> int:
    """Calculate days since a given date"""
    if last_date is None:
        return 0
    if today is None:
        today = ist_today()
    delta = today - last_date
    return max(0, delta.days)


# ============================================================================
# FORGETTING CURVE
# ============================================================================

def apply_decay(mastery: float, lambda_forgetting: float, days: int) -> float:
    """
    Apply exponential forgetting curve
    
    Formula: m_new = m * exp(-λ * days)
    
    Args:
        mastery: Current mastery level (0.0-1.0)
        lambda_forgetting: Decay rate per day (default: 0.04)
        days: Days since last studied
    
    Returns:
        Decayed mastery level (0.0-1.0)
    """
    if days <= 0:
        return mastery
    
    decayed = mastery * math.exp(-lambda_forgetting * days)
    return max(0.0, min(1.0, decayed))


# ============================================================================
# PRIORITY CALCULATIONS
# ============================================================================

def sph(concept_weight: float, mastery: float, t_est_hours: float) -> float:
    """
    Study Priority Heuristic (SPH) for NEW learning
    
    Prioritizes:
    - High concept_weight (important topics)
    - Low mastery (not yet learned)
    - Lower t_est (quicker wins)
    
    Formula: SPH = concept_weight * (1 - mastery) / sqrt(t_est)
    
    Args:
        concept_weight: Importance weight (from subject distribution)
        mastery: Current mastery level (0.0-1.0)
        t_est_hours: Estimated hours to reach mastery
    
    Returns:
        Priority score (higher = more urgent)
    """
    if t_est_hours <= 0:
        t_est_hours = 1.0  # Avoid division by zero
    
    gap = 1.0 - mastery
    return concept_weight * gap / math.sqrt(t_est_hours)


def rpf(concept_weight: float, mastery: float, lambda_forgetting: float, days_since_last: int) -> float:
    """
    Revision Priority Factor (RPF) for REVISION
    
    Prioritizes:
    - High concept_weight (important topics)
    - High mastery (worth maintaining)
    - High decay risk (λ * days)
    
    Formula: RPF = concept_weight * mastery * (1 - exp(-λ * days))
    
    Args:
        concept_weight: Importance weight
        mastery: Current mastery level
        lambda_forgetting: Decay rate per day
        days_since_last: Days since last studied
    
    Returns:
        Priority score (higher = more urgent to revise)
    """
    if days_since_last <= 0:
        return 0.0  # Just studied, no urgency
    
    # Decay factor: how much has been forgotten
    decay_factor = 1.0 - math.exp(-lambda_forgetting * days_since_last)
    
    return concept_weight * mastery * decay_factor


# ============================================================================
# SPACED REPETITION
# ============================================================================

SPACED_STAGES = [1, 3, 7, 14, 30]  # Days between reviews

def next_due_date(last_studied: date, current_stage: int) -> date:
    """
    Calculate next due date for spaced repetition
    
    Stages: 0 → 1 day, 1 → 3 days, 2 → 7 days, 3 → 14 days, 4 → 30 days
    
    Args:
        last_studied: Date of last study
        current_stage: Index into SPACED_STAGES (0-4)
    
    Returns:
        Next review due date
    """
    if current_stage < 0:
        current_stage = 0
    if current_stage >= len(SPACED_STAGES):
        current_stage = len(SPACED_STAGES) - 1
    
    days_interval = SPACED_STAGES[current_stage]
    return last_studied + timedelta(days=days_interval)


def is_due_for_review(last_studied: Optional[date], current_stage: int, today: Optional[date] = None) -> bool:
    """
    Check if task is due for spaced repetition review
    
    Args:
        last_studied: Date of last study (None if never studied)
        current_stage: Current stage index (0-4)
        today: Reference date (defaults to IST today)
    
    Returns:
        True if due for review
    """
    if last_studied is None:
        return True  # Never studied, always due
    
    if today is None:
        today = ist_today()
    
    due_date = next_due_date(last_studied, current_stage)
    return today >= due_date


# ============================================================================
# STUDY UPDATES (Simulation Only)
# ============================================================================

def learn_update(current_mastery: float, hours_spent: float, t_est_hours: float, eta_learn: float) -> float:
    """
    Simulate mastery gain from NEW learning session
    
    Formula: Δm = η * (hours / t_est) * (1 - m_current)
    
    Args:
        current_mastery: Current mastery level (0.0-1.0)
        hours_spent: Hours spent learning
        t_est_hours: Estimated total hours to mastery
        eta_learn: Learning efficiency (default: 0.8)
    
    Returns:
        New mastery level after learning (0.0-1.0)
    """
    if t_est_hours <= 0:
        t_est_hours = 1.0
    
    # Remaining gap to perfect mastery
    gap = 1.0 - current_mastery
    
    # Gain proportional to time spent and learning efficiency
    gain = eta_learn * (hours_spent / t_est_hours) * gap
    
    new_mastery = current_mastery + gain
    return max(0.0, min(1.0, new_mastery))


def revise_update(current_mastery: float, hours_spent: float, t_est_hours: float, rho_revise: float) -> float:
    """
    Simulate mastery restoration from REVISION session
    
    Revision is less efficient than initial learning but helps maintain mastery
    
    Formula: Δm = ρ * (hours / t_est) * (1 - m_current)
    
    Args:
        current_mastery: Current mastery level (0.0-1.0)
        hours_spent: Hours spent revising
        t_est_hours: Estimated total hours to mastery
        rho_revise: Revision efficiency (default: 0.35, ~40% of learning)
    
    Returns:
        New mastery level after revision (0.0-1.0)
    """
    if t_est_hours <= 0:
        t_est_hours = 1.0
    
    gap = 1.0 - current_mastery
    gain = rho_revise * (hours_spent / t_est_hours) * gap
    
    new_mastery = current_mastery + gain
    return max(0.0, min(1.0, new_mastery))


# ============================================================================
# BAYESIAN UPDATES (Beta Distribution)
# ============================================================================

def bayes_init(initial_mastery: float = 0.5) -> Tuple[float, float]:
    """
    Initialize Beta distribution parameters (α, β) from initial mastery estimate
    
    Uses method of moments with assumed variance
    
    Args:
        initial_mastery: Initial mastery estimate (0.0-1.0)
    
    Returns:
        (alpha, beta) parameters for Beta distribution
    """
    # Assume some initial uncertainty (variance = 0.1)
    mean = max(0.01, min(0.99, initial_mastery))  # Avoid 0 or 1
    variance = 0.1
    
    # Method of moments for Beta distribution
    # mean = α / (α + β)
    # variance = (α * β) / ((α + β)² * (α + β + 1))
    
    # Solving for α and β
    temp = mean * (1 - mean) / variance - 1
    alpha = mean * temp
    beta = (1 - mean) * temp
    
    return (max(1.0, alpha), max(1.0, beta))


def quiz_update(alpha: float, beta: float, correct: int, total: int) -> Tuple[float, float]:
    """
    Update Beta distribution parameters based on quiz results (Bayesian update)
    
    Args:
        alpha: Current alpha parameter
        beta: Current beta parameter
        correct: Number of correct answers
        total: Total number of questions
    
    Returns:
        Updated (alpha, beta) parameters
    """
    incorrect = total - correct
    
    # Bayesian update: add successes to α, failures to β
    new_alpha = alpha + correct
    new_beta = beta + incorrect
    
    return (new_alpha, new_beta)


def mastery_from_beta(alpha: float, beta: float) -> float:
    """
    Get mastery estimate from Beta distribution (posterior mean)
    
    Args:
        alpha: Alpha parameter
        beta: Beta parameter
    
    Returns:
        Mastery estimate (0.0-1.0)
    """
    return alpha / (alpha + beta)


# ============================================================================
# PROBABILITY CALCULATIONS
# ============================================================================

def expected_and_var(tasks: List[Dict]) -> Tuple[float, float]:
    """
    Calculate expected marks (μ) and variance (σ²) across all tasks
    
    Assumes tasks are independent. Each task contributes:
    - Expected marks: concept_weight * mastery * total_marks
    - Variance: concept_weight² * mastery * (1 - mastery) * total_marks²
    
    Args:
        tasks: List of task dicts with keys:
               - concept_weight: Task importance (sums to 1.0 across all tasks)
               - mastery: Current mastery level (0.0-1.0)
               - total_marks: Total marks for exam (e.g., 200 for UPSC Prelims)
    
    Returns:
        (mu, sigma2): Expected marks and variance
    """
    mu = 0.0
    sigma2 = 0.0
    
    for task in tasks:
        w = task.get('concept_weight', 0.0)
        m = task.get('mastery', 0.0)
        total_marks = task.get('total_marks', 200)  # Default UPSC Prelims
        
        # Expected marks from this task
        mu += w * m * total_marks
        
        # Variance (binomial-like uncertainty)
        sigma2 += (w ** 2) * m * (1 - m) * (total_marks ** 2)
    
    return (mu, sigma2)


def prob_clear(mu: float, sigma2: float, threshold: float) -> float:
    """
    Calculate probability of clearing exam using normal approximation
    
    P(score >= threshold) where score ~ N(μ, σ²)
    
    Uses complementary error function (erfc) for numerical stability
    
    Args:
        mu: Expected marks
        sigma2: Variance
        threshold: Passing marks threshold
    
    Returns:
        Probability of clearing (0.0-1.0)
    """
    if sigma2 <= 0:
        # No uncertainty: deterministic
        return 1.0 if mu >= threshold else 0.0
    
    sigma = math.sqrt(sigma2)
    
    # Standardize: Z = (threshold - μ) / σ
    z = (threshold - mu) / sigma
    
    # P(X >= threshold) = P(Z >= z) = 1 - Φ(z) = 0.5 * erfc(z / sqrt(2))
    prob = 0.5 * math.erfc(z / math.sqrt(2))
    
    return max(0.0, min(1.0, prob))


# ============================================================================
# PROJECTION TO EXAM DATE
# ============================================================================

def project_mu(current_mu: float, daily_delta: float, days_remaining: int, delta_decay: float = 0.7) -> float:
    """
    Project expected marks at exam date with diminishing returns
    
    Assumes daily learning gains decay as exam approaches (burnout/saturation)
    
    Formula: μ_exam = μ_now + Σ(daily_delta * decay^t) for t=0 to days_remaining-1
    
    Geometric series: sum = daily_delta * (1 - decay^days) / (1 - decay)
    
    Args:
        current_mu: Current expected marks
        daily_delta: Average daily gain in marks (Δμ per day)
        days_remaining: Days until exam
        delta_decay: Decay factor for daily gains (default: 0.7, ~30% reduction per day)
    
    Returns:
        Projected marks at exam date
    """
    if days_remaining <= 0:
        return current_mu
    
    if abs(delta_decay - 1.0) < 0.001:
        # No decay: linear projection
        total_gain = daily_delta * days_remaining
    else:
        # Geometric series with decay
        total_gain = daily_delta * (1 - delta_decay ** days_remaining) / (1 - delta_decay)
    
    return current_mu + total_gain


# ============================================================================
# DAILY PLANNING ALGORITHM
# ============================================================================

def allocate_time_by_priority(tasks: List[Dict], total_hours: float, key: str = 'priority') -> List[Dict]:
    """
    Allocate study time to tasks proportional to their priority
    
    Args:
        tasks: List of task dicts with 'task_id' and priority score
        total_hours: Total hours available
        key: Key for priority score (default: 'priority')
    
    Returns:
        List of tasks with 'allocated_hours' added
    """
    if not tasks or total_hours <= 0:
        return []
    
    # Calculate total priority
    total_priority = sum(t.get(key, 0.0) for t in tasks)
    
    if total_priority <= 0:
        # Equal distribution
        hours_each = total_hours / len(tasks)
        for task in tasks:
            task['allocated_hours'] = hours_each
    else:
        # Proportional allocation
        for task in tasks:
            priority = task.get(key, 0.0)
            task['allocated_hours'] = (priority / total_priority) * total_hours
    
    return tasks


def simulate_daily_plan(
    tasks: List[Dict],
    daily_hours: float = 6.0,
    split_new: float = 0.6,
    today: Optional[date] = None
) -> Dict:
    """
    Simulate a full daily study plan (NEW + REVISION)
    
    This is a READ-ONLY simulation. No database changes.
    
    Args:
        tasks: List of task dicts with fields:
               - task_id, concept_weight, mastery, t_est_hours,
                 lambda_forgetting, eta_learn, rho_revise,
                 last_studied_at, spaced_stage, task_type
        daily_hours: Total study hours available (default: 6.0)
        split_new: Fraction for new learning (default: 0.6 = 60%)
        today: Reference date (defaults to IST today)
    
    Returns:
        Dict with keys:
        - 'new_tasks': List of tasks for new learning with allocated_hours
        - 'revision_tasks': List of tasks for revision with allocated_hours
        - 'hours_new': Total hours for new learning
        - 'hours_revision': Total hours for revision
        - 'projected_gains': Dict with 'before' and 'after' stats (μ, σ², P(clear))
    """
    if today is None:
        today = ist_today()
    
    # Step 1: Apply decay to all tasks
    for task in tasks:
        last_studied = task.get('last_studied_at')
        days = days_since(last_studied, today)
        task['mastery_after_decay'] = apply_decay(
            task.get('mastery', 0.0),
            task.get('lambda_forgetting', 0.04),
            days
        )
        task['days_since_last'] = days
    
    # Step 2: Split hours
    hours_new = daily_hours * split_new
    hours_revision = daily_hours * (1 - split_new)
    
    # Step 3: Calculate priorities
    new_candidates = []
    revision_candidates = []
    
    for task in tasks:
        w = task.get('concept_weight', 0.0)
        m = task.get('mastery_after_decay', 0.0)
        t_est = task.get('t_est_hours', 4.0)
        λ = task.get('lambda_forgetting', 0.04)
        days = task.get('days_since_last', 0)
        stage = task.get('spaced_stage', 0)
        task_type = task.get('task_type', 'learn')
        
        # Priority for NEW learning
        if m < 0.9:  # Not yet mastered
            task['sph_priority'] = sph(w, m, t_est)
            new_candidates.append(task)
        
        # Priority for REVISION
        if m > 0.3 and days >= 3:  # Has some mastery and not recently studied
            task['rpf_priority'] = rpf(w, m, λ, days)
            revision_candidates.append(task)
        
        # Spaced repetition overrides
        if is_due_for_review(task.get('last_studied_at'), stage, today):
            if m > 0.3:  # Has mastery worth maintaining
                task['rpf_priority'] = task.get('rpf_priority', 0.0) * 1.5  # Boost priority
    
    # Step 4: Select top tasks by priority
    new_candidates.sort(key=lambda t: t.get('sph_priority', 0.0), reverse=True)
    revision_candidates.sort(key=lambda t: t.get('rpf_priority', 0.0), reverse=True)
    
    # Select top N tasks (up to 10 each)
    selected_new = new_candidates[:10]
    selected_revision = revision_candidates[:8]
    
    # Step 5: Allocate time
    new_tasks = allocate_time_by_priority(selected_new, hours_new, 'sph_priority')
    revision_tasks = allocate_time_by_priority(selected_revision, hours_revision, 'rpf_priority')
    
    # Step 6: Simulate learning outcomes
    for task in new_tasks:
        task['mastery_after_study'] = learn_update(
            task.get('mastery_after_decay', 0.0),
            task.get('allocated_hours', 0.0),
            task.get('t_est_hours', 4.0),
            task.get('eta_learn', 0.8)
        )
        task['derived'] = task.get('concept_weight', 0.0) is not None  # From virtual task
    
    for task in revision_tasks:
        task['mastery_after_study'] = revise_update(
            task.get('mastery_after_decay', 0.0),
            task.get('allocated_hours', 0.0),
            task.get('t_est_hours', 4.0),
            task.get('rho_revise', 0.35)
        )
        task['derived'] = task.get('concept_weight', 0.0) is not None
    
    # Step 7: Calculate projections (before and after)
    # Prepare task data for expected_and_var
    tasks_before = [
        {
            'concept_weight': t.get('concept_weight', 0.0),
            'mastery': t.get('mastery_after_decay', 0.0),
            'total_marks': 200  # Assume UPSC Prelims default
        }
        for t in tasks
    ]
    
    mu_before, sigma2_before = expected_and_var(tasks_before)
    
    # Update mastery for selected tasks
    mastery_updates = {}
    for task in new_tasks + revision_tasks:
        mastery_updates[task['task_id']] = task['mastery_after_study']
    
    tasks_after = []
    for t in tasks:
        tid = t.get('task_id')
        mastery_after = mastery_updates.get(tid, t.get('mastery_after_decay', 0.0))
        tasks_after.append({
            'concept_weight': t.get('concept_weight', 0.0),
            'mastery': mastery_after,
            'total_marks': 200
        })
    
    mu_after, sigma2_after = expected_and_var(tasks_after)
    
    return {
        'new_tasks': new_tasks,
        'revision_tasks': revision_tasks,
        'hours_new': hours_new,
        'hours_revision': hours_revision,
        'projected_gains': {
            'before': {
                'mu': mu_before,
                'sigma2': sigma2_before,
                'p_clear_today': prob_clear(mu_before, sigma2_before, 120)  # Assume threshold 120
            },
            'after': {
                'mu': mu_after,
                'sigma2': sigma2_after,
                'p_clear_today': prob_clear(mu_after, sigma2_after, 120),
                'delta_mu': mu_after - mu_before
            }
        }
    }


# ============================================================================
# GOAL STATUS COMPUTATION
# ============================================================================

def compute_goal_status(
    tasks: List[Dict],
    threshold_marks: float = 120.0,
    exam_date: Optional[date] = None,
    daily_hours: float = 6.0,
    split_new: float = 0.6,
    delta_decay: float = 0.7,
    today: Optional[date] = None
) -> Dict:
    """
    Compute comprehensive status for a goal (READ-ONLY)
    
    Args:
        tasks: List of task dicts with all fields
        threshold_marks: Passing marks threshold
        exam_date: Target exam date (None for no projection)
        daily_hours: Average daily study hours
        split_new: New vs revision split
        delta_decay: Decay factor for projections
        today: Reference date
    
    Returns:
        Dict with comprehensive stats:
        - mu, sigma2, p_clear_today
        - mu_exam, p_clear_exam (if exam_date provided)
        - days_remaining
        - total_tasks, mastered_tasks (m >= 0.8)
        - avg_mastery
    """
    if today is None:
        today = ist_today()
    
    # Apply decay
    for task in tasks:
        last_studied = task.get('last_studied_at')
        days = days_since(last_studied, today)
        task['mastery_current'] = apply_decay(
            task.get('mastery', 0.0),
            task.get('lambda_forgetting', 0.04),
            days
        )
    
    # Calculate current state
    tasks_for_calc = [
        {
            'concept_weight': t.get('concept_weight', 0.0),
            'mastery': t.get('mastery_current', 0.0),
            'total_marks': threshold_marks * 1.67  # Approximate total marks (200 for threshold 120)
        }
        for t in tasks
    ]
    
    mu, sigma2 = expected_and_var(tasks_for_calc)
    p_clear_today = prob_clear(mu, sigma2, threshold_marks)
    
    # Projection to exam date
    mu_exam = mu
    p_clear_exam = p_clear_today
    days_remaining = 0
    
    if exam_date:
        days_remaining = (exam_date - today).days
        if days_remaining > 0:
            # Estimate daily delta from recent plan simulation
            plan = simulate_daily_plan(tasks, daily_hours, split_new, today)
            daily_delta = plan['projected_gains']['after']['delta_mu']
            
            mu_exam = project_mu(mu, daily_delta, days_remaining, delta_decay)
            p_clear_exam = prob_clear(mu_exam, sigma2, threshold_marks)
    
    # Task statistics
    total_tasks = len(tasks)
    mastered_tasks = sum(1 for t in tasks if t.get('mastery_current', 0.0) >= 0.8)
    avg_mastery = sum(t.get('mastery_current', 0.0) for t in tasks) / total_tasks if total_tasks > 0 else 0.0
    
    return {
        'mu': mu,
        'sigma2': sigma2,
        'p_clear_today': p_clear_today,
        'mu_exam': mu_exam,
        'p_clear_exam': p_clear_exam,
        'days_remaining': days_remaining,
        'total_tasks': total_tasks,
        'mastered_tasks': mastered_tasks,
        'avg_mastery': avg_mastery,
        'threshold_marks': threshold_marks
    }
