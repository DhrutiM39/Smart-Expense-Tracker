# Smart Expense Tracker

A full-stack web application built with Python (Flask) and MySQL to track and manage personal expenses.

## Features
- **User Authentication**: Secure signup and login with password hashing.
- **Expense CRUD**: Add, edit, and delete expenses with categories.
- **Dynamic Dashboard**: Total spending overview, category-wise breakdown (Doughnut Chart), and monthly trends (Line Chart).
- **Responsive UI**: Modern, glassmorphism-inspired design that works on mobile and desktop.

## Prerequisites
- Python 3.x
- MySQL Server (via XAMPP, WAMP, or standalone)

## Setup Instructions

### 1. Database Setup
1. Open your MySQL management tool (e.g., phpMyAdmin).
2. Create a new database named `expense_tracker`.
3. (Optional) If your MySQL has a password, update `config.py` with your credentials.

### 2. Install Dependencies
Run the following command in your terminal:
```bash
pip install flask mysql-connector-python
```

### 3. Run the Application
1. Navigate to the project directory.
2. Run the application:
```bash
python app.py
```
3. The app will automatically initialize the database tables on its first run.
4. Open your browser and go to `http://127.0.0.1:5000`.

## Project Structure
- `app.py`: Main entry point.
- `config.py`: Configuration for DB and Secret Key.
- `database.py`: Database connection and initialization.
- `routes/`: Backend logic for auth and expenses.
- `templates/`: HTML files using Jinja2.
- `static/`: CSS and Client-side JS.
