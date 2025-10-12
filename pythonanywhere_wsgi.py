# ========================================================================
# COPY THIS ENTIRE CONTENT TO YOUR PYTHONANYWHERE WSGI FILE
# ========================================================================
# 
# Location: /var/www/jaihanuman_pythonanywhere_com_wsgi.py
#
# Steps:
# 1. Go to PythonAnywhere Web tab
# 2. Click on the WSGI configuration file link
# 3. DELETE EVERYTHING in that file
# 4. PASTE this entire content below
# 5. Save and Reload
#
# ========================================================================

import sys
import os

# ========================================================================
# CRITICAL: Set the correct path to your project
# ========================================================================
project_home = '/home/jaihanuman/studyMomentum'

# Add project directory to Python path
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# ========================================================================
# Set environment variables for production
# ========================================================================
os.environ['FLASK_ENV'] = 'production'
os.environ['FLASK_APP'] = 'wsgi.py'

# Optional: Set a production secret key (change this!)
# os.environ['SECRET_KEY'] = 'your-super-secret-production-key-here'

# ========================================================================
# Import the Flask application
# ========================================================================
try:
    from wsgi import application
    print(f"✅ Successfully imported application from wsgi.py")
    print(f"✅ Project path: {project_home}")
    print(f"✅ Python path: {sys.path[:3]}")
except Exception as e:
    print(f"❌ Error importing application: {e}")
    print(f"❌ Current directory: {os.getcwd()}")
    print(f"❌ Python path: {sys.path}")
    print(f"❌ Files in project directory: {os.listdir(project_home) if os.path.exists(project_home) else 'PATH NOT FOUND'}")
    raise

# ========================================================================
# This is what PythonAnywhere will use
# DO NOT change the variable name 'application'
# ========================================================================
