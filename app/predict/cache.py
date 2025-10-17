"""
Stage 5: In-Memory Caching for Prediction API
==============================================
Implements 5-minute TTL cache for /api/predict/plan endpoint
Keyed by (user_id, goal_id, input_hash)
"""

import hashlib
import json
import time
from functools import wraps
from flask import request, jsonify

# Simple in-memory cache with TTL
# Format: {cache_key: (timestamp, response_data)}
_cache = {}
CACHE_TTL_SECONDS = 300  # 5 minutes

def generate_cache_key(user_id, goal_id, request_data):
    """
    Generate cache key from user, goal, and request parameters
    Format: user_{user_id}_goal_{goal_id}_{hash}
    """
    # Extract relevant fields for cache key
    cache_params = {
        'exam_date': request_data.get('exam_date'),
        'threshold_marks': request_data.get('threshold_marks'),
        'daily_hours': request_data.get('daily_hours'),
        'split_new': request_data.get('split_new'),
    }
    
    # Create hash of parameters
    param_str = json.dumps(cache_params, sort_keys=True)
    param_hash = hashlib.md5(param_str.encode()).hexdigest()[:12]
    
    return f"user_{user_id}_goal_{goal_id}_{param_hash}"

def cache_plan_response(cache_ttl=CACHE_TTL_SECONDS):
    """
    Decorator to cache /api/predict/plan responses for 5 minutes
    Uses (user_id, goal_id, input_hash) as cache key
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Check if we should use caching (can be disabled via env)
            import os
            use_cache = os.environ.get('ENABLE_PLAN_CACHE', 'true').lower() == 'true'
            
            if not use_cache:
                return func(*args, **kwargs)
            
            # Get request data
            data = request.get_json() or {}
            goal_id = data.get('goal_id')
            
            # Get user_id from current_user (assume Flask-Login)
            from flask_login import current_user
            if not current_user.is_authenticated:
                return func(*args, **kwargs)  # No cache for anonymous
            
            user_id = current_user.id
            
            # Generate cache key
            cache_key = generate_cache_key(user_id, goal_id, data)
            
            # Check cache
            now = time.time()
            if cache_key in _cache:
                timestamp, cached_response = _cache[cache_key]
                age = now - timestamp
                
                if age < cache_ttl:
                    # Cache hit - return cached response
                    cached_response['_cache_hit'] = True
                    cached_response['_cache_age_seconds'] = round(age, 1)
                    return jsonify(cached_response), 200
                else:
                    # Expired - remove from cache
                    del _cache[cache_key]
            
            # Cache miss - call original function
            response = func(*args, **kwargs)
            
            # Cache the response if successful
            if isinstance(response, tuple):
                response_data, status_code = response
            else:
                response_data = response
                status_code = 200
            
            if status_code == 200 and hasattr(response_data, 'get_json'):
                response_json = response_data.get_json()
                _cache[cache_key] = (now, response_json)
                
                # Clean old cache entries (simple cleanup)
                _cleanup_expired_cache(now)
            
            return response
        
        return wrapper
    return decorator

def _cleanup_expired_cache(current_time):
    """Remove expired entries from cache"""
    expired_keys = [
        key for key, (timestamp, _) in _cache.items()
        if current_time - timestamp > CACHE_TTL_SECONDS
    ]
    for key in expired_keys:
        del _cache[key]

def clear_cache_for_user(user_id):
    """Clear all cache entries for a specific user"""
    prefix = f"user_{user_id}_"
    keys_to_remove = [key for key in _cache.keys() if key.startswith(prefix)]
    for key in keys_to_remove:
        del _cache[key]

def clear_all_cache():
    """Clear entire cache (admin utility)"""
    _cache.clear()

def get_cache_stats():
    """Get cache statistics for monitoring"""
    now = time.time()
    total_entries = len(_cache)
    valid_entries = sum(1 for timestamp, _ in _cache.values() if now - timestamp < CACHE_TTL_SECONDS)
    
    return {
        'total_entries': total_entries,
        'valid_entries': valid_entries,
        'expired_entries': total_entries - valid_entries,
        'cache_ttl_seconds': CACHE_TTL_SECONDS
    }
