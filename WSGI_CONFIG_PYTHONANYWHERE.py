"""
WSGI Configuration for PythonAnywhere
Copy this ENTIRE file content to your PythonAnywhere WSGI configuration file

Steps:
1. Go to PythonAnywhere Web tab
2. Click on the WSGI configuration file link
3. DELETE EVERYTHING in that file
4. PASTE this entire content
5. Replace 'jaihanuman' with your actual PythonAnywhere username
6. Save and Reload
"""

import sys
import os

# ============================================================================
# IMPORTANT: Replace 'jaihanuman' with your actual PythonAnywhere username
# ============================================================================
path = '/home/jaihanuman/studyMomentum'
if path not in sys.path:
    sys.path.insert(0, path)

# Set production environment
os.environ['FLASK_ENV'] = 'production'

# Import the application
from wsgi import application

# This is what PythonAnywhere will use
# Do not change the variable name 'application'
