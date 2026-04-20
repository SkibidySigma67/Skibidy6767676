=from flask import Flask, render_template, request, redirect, url_for, session, flash
from functools import wraps
import sqlite3
import hashlib
import re

app = Flask(__name__)
app.secret_key = 'forest-grove-secret-key-2024'  # Change this in production

DATABASE = 'greenfield.db'

def get_db():
    """Get database connection"""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize database with users table"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            full_name TEXT NOT NULL,
            email TEXT,
            phone TEXT,
            address TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()
    print("✅ Database 'greenfield.db' initialized successfully!")

def hash_password(password):
    """Hash password using SHA256"""
    return hashlib.sha256(password.encode()).hexdigest()

def login_required(f):
    """Decorator to require login for protected routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to access your account', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    """Home page - redirect to login or account"""
    if 'user_id' in session:
        return redirect(url_for('account'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login page"""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        if not username or not password:
            flash('Please enter both username and password', 'error')
            return render_template('login.html')
        
        conn = get_db()
        cursor = conn.cursor()
        
        # Hash the password and check against database
        hashed_pw = hash_password(password)
        user = cursor.execute(
            'SELECT * FROM users WHERE username = ? AND password = ?',
            (username, hashed_pw)
        ).fetchone()
        
        conn.close()
        
        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['full_name'] = user['full_name']
            flash(f'✨ Welcome back, {user["full_name"]}!', 'success')
            return redirect(url_for('account'))
        else:
            flash('❌ Invalid username or password', 'error')
    
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    """User registration page"""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        full_name = request.form.get('full_name', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        address = request.form.get('address', '').strip()
        
        # Validation
        errors = []
        
        if not username:
            errors.append('Username is required')
        elif len(username) < 3:
            errors.append('Username must be at least 3 characters')
        elif not re.match(r'^[a-zA-Z0-9_]+$', username):
            errors.append('Username can only contain letters, numbers, and underscores')
        
        if not password:
            errors.append('Password is required')
        elif len(password) < 4:
            errors.append('Password must be at least 4 characters')
        
        if password != confirm_password:
            errors.append('Passwords do not match')
        
        if not full_name:
            errors.append('Full name is required')
        
        if email and not re.match(r'^[^@]+@[^@]+\.[^@]+$', email):
            errors.append('Please enter a valid email address')
        
        if errors:
            for error in errors:
                flash(error, 'error')
            return render_template('login.html', show_signup=True, 
                                 username=username, full_name=full_name, 
                                 email=email, phone=phone, address=address)
        
        # Check if username already exists
        conn = get_db()
        cursor = conn.cursor()
        existing_user = cursor.execute('SELECT id FROM users WHERE username = ?', (username,)).fetchone()
        
        if existing_user:
            conn.close()
            flash('❌ Username already exists. Please choose another one.', 'error')
            return render_template('login.html', show_signup=True,
                                 username=username, full_name=full_name, 
                                 email=email, phone=phone, address=address)
        
        # Create new user
        try:
            hashed_pw = hash_password(password)
            cursor.execute('''
                INSERT INTO users (username, password, full_name, email, phone, address) 
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (username, hashed_pw, full_name, email, phone, address))
            conn.commit()
            
            # Get the newly created user
            user = cursor.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
            conn.close()
            
            # Log the user in automatically
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['full_name'] = user['full_name']
            
            flash(f'🎉 Account created successfully! Welcome to Forest Grove, {full_name}!', 'success')
            return redirect(url_for('account'))
            
        except Exception as e:
            conn.close()
            flash('An error occurred. Please try again.', 'error')
            return render_template('login.html', show_signup=True,
                                 username=username, full_name=full_name, 
                                 email=email, phone=phone, address=address)
    
    # GET request - show signup form
    return render_template('login.html', show_signup=True)

@app.route('/account')
@login_required
def account():
    """User account dashboard - protected page"""
    conn = get_db()
    cursor = conn.cursor()
    user = cursor.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
    conn.close()
    
    return render_template('account.html', user=user)

@app.route('/logout')
def logout():
    """Logout user"""
    session.clear()
    flash('👋 You have been logged out successfully', 'success')
    return redirect(url_for('login'))

# Initialize database when app starts
if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5000)
