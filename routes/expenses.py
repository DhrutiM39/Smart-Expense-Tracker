from flask import Blueprint, render_template, redirect, url_for, request, flash, session, make_response
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
    
    # Get filters
    category_filter = request.args.get('category')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    query = "SELECT * FROM expenses WHERE user_id = %s"
    params = [user_id]
    
    if category_filter:
        query += " AND category = %s"
        params.append(category_filter)
    if start_date:
        query += " AND expense_date >= %s"
        params.append(start_date)
    if end_date:
        query += " AND expense_date <= %s"
        params.append(end_date)
        
    query += " ORDER BY expense_date DESC"
    
    cursor.execute(query, tuple(params))
    expenses = cursor.fetchall()
    
    # Get user budget
    cursor.execute("SELECT monthly_budget FROM users WHERE id = %s", (user_id,))
    user_budget = cursor.fetchone()['monthly_budget'] or 0
    
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
                         monthly_summary=monthly_summary,
                         user_budget=user_budget,
                         filters={'category': category_filter, 'start_date': start_date, 'end_date': end_date})

@expenses_bp.route('/export')
@login_required
def export_expenses():
    user_id = session['user_id']
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT expense_date, category, amount, description FROM expenses WHERE user_id = %s ORDER BY expense_date DESC", (user_id,))
    expenses = cursor.fetchall()
    
    si = StringIO()
    cw = csv.writer(si)
    cw.writerow(['Date', 'Category', 'Amount (INR)', 'Description'])
    for exp in expenses:
        cw.writerow([exp['expense_date'], exp['category'], exp['amount'], exp['description']])
    
    output = make_response(si.getvalue())
    output.headers["Content-Disposition"] = "attachment; filename=expenses.csv"
    output.headers["Content-type"] = "text/csv"
    return output

@expenses_bp.route('/set_budget', methods=['POST'])
@login_required
def set_budget():
    budget = request.form.get('budget')
    user_id = session['user_id']
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET monthly_budget = %s WHERE id = %s", (budget, user_id))
        conn.commit()
        cursor.close()
        conn.close()
        flash('Budget updated!', 'success')
    return redirect(url_for('expenses.dashboard'))

@expenses_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_expense():
    if request.method == 'POST':
        try:
            amount = float(request.form.get('amount', 0))
            category = request.form.get('category')
            date = request.form.get('date')
            description = request.form.get('description', '')
            user_id = session['user_id']
            
            if amount <= 0:
                flash('Amount must be greater than zero', 'error')
                return redirect(url_for('expenses.add_expense'))
            
            valid_categories = ['Food', 'Travel', 'Shopping', 'Bills', 'Others']
            if category not in valid_categories:
                flash('Invalid category selected', 'error')
                return redirect(url_for('expenses.add_expense'))

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
                flash('Expense recorded successfully!', 'success')
                return redirect(url_for('expenses.dashboard'))
            else:
                flash('Database connection failed. Please try again.', 'error')
        except ValueError:
            flash('Invalid amount format', 'error')
            
    return render_template('add_expense.html')

@expenses_bp.route('/edit/<int:expense_id>', methods=['GET', 'POST'])
@login_required
def edit_expense(expense_id):
    user_id = session['user_id']
    conn = get_db_connection()
    if not conn:
        flash('Database error', 'error')
        return redirect(url_for('expenses.dashboard'))
        
    cursor = conn.cursor(dictionary=True)
    
    if request.method == 'POST':
        try:
            amount = float(request.form.get('amount', 0))
            category = request.form.get('category')
            date = request.form.get('date')
            description = request.form.get('description', '')
            
            if amount <= 0:
                flash('Amount must be greater than zero', 'error')
                return redirect(url_for('expenses.edit_expense', expense_id=expense_id))

            cursor.execute("""
                UPDATE expenses 
                SET amount=%s, category=%s, expense_date=%s, description=%s 
                WHERE id=%s AND user_id=%s
            """, (amount, category, date, description, expense_id, user_id))
            conn.commit()
            flash('Expense updated!', 'success')
            return redirect(url_for('expenses.dashboard'))
        except ValueError:
            flash('Invalid amount format', 'error')
        finally:
            cursor.close()
            conn.close()
    
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


import csv
from io import StringIO

