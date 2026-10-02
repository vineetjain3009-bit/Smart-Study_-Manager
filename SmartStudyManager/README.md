# Smart Study Manager

Smart Study Manager is an offline Python desktop application for college students to organise subjects, assignments, study sessions, attendance, and semester progress from one place. It is designed to be small enough to understand for a B.Tech/college project viva while still looking polished in a demonstration.

## Features

- Local registration and login with SHA-256 password hashing
- Modern dashboard with subject, task, study-time, and attendance statistics
- Subject CRUD: add, view, edit, and delete subjects
- Task/assignment CRUD with deadline, priority, status, and pending/completed filters
- Study-session logging with date, duration, notes, history, and total hours
- Attendance tracking with automatic percentage calculation and a 75% warning
- Matplotlib charts using the student's real database records
- On-screen semester summary plus TXT or CSV report export
- Optional one-click sample data for a fresh demo account
- SQLite database created automatically; no internet or cloud account required

## Technology Stack

- Python 3.10+
- Tkinter (desktop GUI, included with standard Python installations)
- SQLite3 (local database, included with Python)
- Matplotlib (charts)

## Python Concepts Demonstrated

- Variables, strings, integers, floats, lists, dictionaries, and tuples
- Conditional statements, loops, functions, and exception handling
- Object-oriented programming with classes for the app, database, and pages
- Modules and imports
- SQLite database operations, SQL, foreign keys, and CRUD operations
- Date/time validation and basic percentage calculations
- File handling for TXT and CSV report exports
- GUI programming with Tkinter and ttk widgets

## Database Details

The app automatically creates `database/study_manager.db` the first time it runs. It contains five tables:

- `users` — local account details and password hash
- `subjects` — course code, name, and teacher
- `tasks` — assignments, deadlines, priorities, and status
- `study_sessions` — logged study duration and notes
- `attendance` — total and attended classes for each subject

All records are associated with the logged-in user. Deleting a subject also removes its related attendance and study-session records, preventing orphaned data.

## Installation

1. Install Python 3.10 or newer from [python.org](https://www.python.org/downloads/). During installation, select **Add Python to PATH**.
2. Open a terminal in this project folder.
3. Install the only external dependency:

```powershell
python -m pip install -r requirements.txt
```

## How to Run

From the `SmartStudyManager` folder, run:

```powershell
python main.py
```

On first use, choose **Create an account**, then log in. The dashboard includes an optional sample-data button for a demonstration account that has no subjects yet.

## Project Structure

```text
SmartStudyManager/
├── main.py             # App startup, sidebar navigation, login/logout flow
├── database.py         # SQLite setup and all database CRUD methods
├── login.py            # Local login and registration screen
├── dashboard.py        # Dashboard statistics and optional sample data
├── subjects.py         # Subject management screen
├── tasks.py            # Assignment/task management screen
├── study_sessions.py   # Study session logging and history
├── attendance.py       # Attendance tracking and percentage calculation
├── analytics.py        # Matplotlib charts from stored data
├── reports.py          # On-screen report and TXT/CSV export
├── ui_helpers.py       # Shared colours, styles, cards, and table helpers
├── utils.py            # Small validation and calculation helpers
├── requirements.txt    # Matplotlib dependency
└── database/           # Automatically stores the SQLite database
```

## Screenshots

Add screenshots of the Login page, Dashboard, Subject list, Task list, Analytics page, and Report page here before submission.

## Future Enhancements

- Deadline reminders and overdue-task highlighting
- A start/stop study timer
- Search and sorting for large task lists
- PDF report export
- Theme switcher (light/dark mode)

## Author

Author: [Your Name]  
College: [Your College]  
Department: [Your Department]  
Year/Section: [Your Year/Section]
