# Goal Tracker Application

A modern, mobile-first goal tracking application built with Flask and Material Design.

## Features

- **Mobile-First Design**: Responsive interface optimized for mobile devices
- **Material Design**: Modern UI with Material Design components
- **PWA Support**: Installable web application with offline capabilities
- **Multi-User Support**: Admin-managed user accounts
- **Comprehensive Tracking**: Tasks, goals, subjects, and completion metrics
- **Analytics Dashboard**: Daily, weekly, and monthly progress reports
- **API Access**: REST API for programmatic data entry

## Quick Start

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Initialize the database:
```bash
python init_db.py
```

3. Run the application:
```bash
python app.py
```

4. Access at `http://localhost:5000`

## Default Admin Login
- Username: `admin`
- Password: `admin123`

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