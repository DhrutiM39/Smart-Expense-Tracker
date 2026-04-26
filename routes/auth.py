from flask import Blueprint, render_template, redirect, url_for, request, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from database import get_db_connection

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        
        if not name or not email or not password:
            flash('All fields are required', 'error')
            return redirect(url_for('auth.signup'))

        conn = get_db_connection()
        if not conn:
            flash('Database error. Please try again later.', 'error')
            return redirect(url_for('auth.signup'))
            
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
        if cursor.fetchone():
            cursor.close()
            conn.close()
            flash('Email already registered', 'error')
            return redirect(url_for('auth.signup'))
        
        password_hash = generate_password_hash(password)
        cursor.execute("INSERT INTO users (name, email, password_hash) VALUES (%s, %s, %s)",
                     (name, email, password_hash))
        conn.commit()
        cursor.close()
        conn.close()
        flash('Welcome! Please log in with your new account.', 'success')
        return redirect(url_for('auth.login'))
            
    return render_template('signup.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        
        if not email or not password:
            flash('Please enter both email and password', 'error')
            return redirect(url_for('auth.login'))

        conn = get_db_connection()
        if not conn:
            flash('Database error', 'error')
            return redirect(url_for('auth.login'))
            
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if user and check_password_hash(user['password_hash'], password):
            session.clear()
            session['user_id'] = user['id']
            session['user_name'] = user['name']
            return redirect(url_for('expenses.dashboard'))
        else:
            flash('Invalid login credentials', 'error')
            
    return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login'))


