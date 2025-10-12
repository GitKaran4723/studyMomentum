# 📚 Study Momentum - Goal Tracker Application

A modern, hierarchical goal tracking application built for students and learners. Track your study goals, subjects, topics, and tasks with intelligent completion percentage calculations.

## ✨ Features

- 🎯 **Hierarchical Goal Structure**: Goal → Subject → Topic → Task with automatic completion tracking
- 📱 **Mobile-First Design**: Responsive interface optimized for all devices
- 🎨 **Modern UI**: Beautiful gradients and Material Design components
- 👥 **Multi-User Support**: Admin-managed user accounts
- 📊 **Smart Analytics**: Daily, weekly, and monthly progress reports
- ✅ **Task Management**: Create, track, and complete tasks with detailed metrics
- 📈 **Progress Tracking**: Real-time completion percentages at all levels
- 🔐 **Secure Authentication**: Session-based with role management

## 🚀 Quick Start (Local Development)

### 1. Clone and Setup
```bash
git clone https://github.com/GitKaran4723/studyMomentum.git
cd studyMomentum
pip install -r requirements.txt
```

### 2. Initialize Database
```bash
python -c "from app import create_app, db; app = create_app(); app.app_context().push(); db.create_all(); print('Database created!')"
```

### 3. Run Application
```bash
python wsgi.py
```

### 4. Access Application
Open browser: `http://localhost:5000`

**Default Admin Login:**
- Username: `admin`
- Password: `admin123`
- ⚠️ **Change password after first login!**

---

## 🌐 PythonAnywhere Deployment

### One-Command Setup
```bash
cd ~/studyMomentum
chmod +x setup.sh
./setup.sh
```

This automatically:
- ✅ Creates virtual environment
- ✅ Installs all packages
- ✅ Creates database with all tables
- ✅ Creates admin user
- ✅ Shows you exact paths for Web tab configuration

**📖 Detailed Guides:**
- [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) - Visual step-by-step guide
- [SETUP_COMMANDS.md](SETUP_COMMANDS.md) - Quick command reference
- [PYTHONANYWHERE_QUICKSTART.md](PYTHONANYWHERE_QUICKSTART.md) - Comprehensive setup
- [FIX_PYTHONANYWHERE.md](FIX_PYTHONANYWHERE.md) - Troubleshooting

## Architecture

- **Backend**: Flask with SQLAlchemy ORM
- **Database**: SQLite (easily upgradeable to PostgreSQL)
- **Frontend**: Material Design with responsive layout
- **PWA**: Service worker for offline functionality
- **Authentication**: Session-based with role management

## API Endpoints

- `GET/POST /api/tasks` - Task management
- `GET/POST /api/goals` - Goal management
- `GET /api/dashboard` - Analytics data
- `GET /api/progress/{goal_id}` - Goal progress

## License

MIT License