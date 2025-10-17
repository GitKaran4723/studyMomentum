"""
Prediction API Blueprint
Stage 2: Read-only prediction endpoints with feature flag guards
"""

from flask import Blueprint

bp = Blueprint('predict', __name__)

from app.predict import routes
