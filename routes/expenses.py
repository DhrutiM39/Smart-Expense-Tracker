from flask import Blueprint, render_template, redirect, url_for, request, flash, session
from database import get_db_connection
from datetime import datetime

expenses_bp = Blueprint('expenses', __name__)

def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@expenses_bp.route('/dashboard')
@login_required
def dashboard():
    user_id = session['user_id']
    conn = get_db_connection()
    if not conn:
        return "Database Connection Error"
    
    cursor = conn.cursor(dictionary=True)
    
    # Get all expenses for user
    cursor.execute("SELECT * FROM expenses WHERE user_id = %s ORDER BY expense_date DESC", (user_id,))
    expenses = cursor.fetchall()
    
    # Get category-wise totals
    cursor.execute("""
        SELECT category, SUM(amount) as total 
        FROM expenses 
        WHERE user_id = %s 
        GROUP BY category
    """, (user_id,))
    category_totals = cursor.fetchall()
    
    # Get total expense
    cursor.execute("SELECT SUM(amount) as total FROM expenses WHERE user_id = %s", (user_id,))
    total_expense = cursor.fetchone()['total'] or 0
    
    # Get monthly summary (last 6 months)
    cursor.execute("""
        SELECT DATE_FORMAT(expense_date, '%b %Y') as month, SUM(amount) as total 
        FROM expenses 
        WHERE user_id = %s 
        GROUP BY month 
        ORDER BY MIN(expense_date) DESC 
        LIMIT 6
    """, (user_id,))
    monthly_summary = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return render_template('dashboard.html', 
                         expenses=expenses, 
                         category_totals=category_totals, 
                         total_expense=total_expense,
                         monthly_summary=monthly_summary)

@expenses_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_expense():
    if request.method == 'POST':
        amount = request.form.get('amount')
        category = request.form.get('category')
        date = request.form.get('date')
        description = request.form.get('description')
        user_id = session['user_id']
        
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO expenses (user_id, amount, category, expense_date, description)
                VALUES (%s, %s, %s, %s, %s)
            """, (user_id, amount, category, date, description))
            conn.commit()
            cursor.close()
            conn.close()
            flash('Expense added successfully!', 'success')
            return redirect(url_for('expenses.dashboard'))
            
    return render_template('add_expense.html')

@expenses_bp.route('/edit/<int:expense_id>', methods=['GET', 'POST'])
@login_required
def edit_expense(expense_id):
    user_id = session['user_id']
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    if request.method == 'POST':
        amount = request.form.get('amount')
        category = request.form.get('category')
        date = request.form.get('date')
        description = request.form.get('description')
        
        cursor.execute("""
            UPDATE expenses 
            SET amount=%s, category=%s, expense_date=%s, description=%s 
            WHERE id=%s AND user_id=%s
        """, (amount, category, date, description, expense_id, user_id))
        conn.commit()
        cursor.close()
        conn.close()
        flash('Expense updated successfully!', 'success')
        return redirect(url_for('expenses.dashboard'))
    
    cursor.execute("SELECT * FROM expenses WHERE id=%s AND user_id=%s", (expense_id, user_id))
    expense = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if not expense:
        flash('Expense not found', 'error')
        return redirect(url_for('expenses.dashboard'))
        
    return render_template('edit_expense.html', expense=expense)

@expenses_bp.route('/delete/<int:expense_id>')
@login_required
def delete_expense(expense_id):
    user_id = session['user_id']
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM expenses WHERE id=%s AND user_id=%s", (expense_id, user_id))
        conn.commit()
        cursor.close()
        conn.close()
        flash('Expense deleted!', 'success')
    return redirect(url_for('expenses.dashboard'))
