from flask import Flask, render_template, redirect, url_for, session
from config import Config
from database import init_db
import os

app = Flask(__name__)
app.config.from_object(Config)

# Initialize database
init_db()

# Import and register blueprints
from routes.auth import auth_bp
from routes.expenses import expenses_bp

app.register_blueprint(auth_bp)
app.register_blueprint(expenses_bp)

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('expenses.dashboard'))
    return redirect(url_for('auth.login'))

if __name__ == '__main__':
    app.run(debug=True)
