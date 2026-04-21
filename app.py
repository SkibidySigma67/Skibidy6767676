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
















<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Products | Forest Grove</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            background: #e8f0e6;
            color: #1e3a2f;
        }

        /* Navbar */
        .navbar {
            background: #1e4a3a;
            padding: 1rem 2rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 1rem;
        }

        .logo {
            color: white;
            font-size: 1.5rem;
            font-weight: 700;
        }

        .logo span {
            font-size: 1.8rem;
        }

        .nav-links {
            display: flex;
            gap: 1rem;
            align-items: center;
        }

        .nav-link {
            color: white;
            text-decoration: none;
            padding: 0.5rem 1.2rem;
            border-radius: 25px;
            background: rgba(255,255,255,0.1);
            transition: 0.2s;
            font-weight: 500;
        }

        .nav-link:hover {
            background: rgba(255,255,255,0.2);
        }

        .login-btn {
            background: #2e7d64;
            color: white;
            text-decoration: none;
            padding: 0.5rem 1.5rem;
            border-radius: 25px;
            font-weight: 600;
            transition: 0.2s;
        }

        .login-btn:hover {
            background: #236b54;
            transform: translateY(-1px);
        }

        /* Main Content */
        .container {
            max-width: 1200px;
            margin: 2rem auto;
            padding: 0 1.5rem;
        }

        /* Header */
        .header {
            text-align: center;
            margin-bottom: 2rem;
        }

        .header h1 {
            font-size: 2rem;
            color: #1e4a3a;
            margin-bottom: 0.5rem;
        }

        .header p {
            color: #7f9e8f;
            font-size: 1rem;
        }

        /* Search Bar */
        .search-bar {
            margin-bottom: 2rem;
            display: flex;
            justify-content: center;
        }

        .search-bar input {
            width: 100%;
            max-width: 400px;
            padding: 0.8rem 1.2rem;
            border-radius: 50px;
            border: 1px solid #c8e0d4;
            font-size: 1rem;
            outline: none;
            transition: 0.2s;
        }

        .search-bar input:focus {
            border-color: #2e7d64;
            box-shadow: 0 0 0 3px rgba(46, 125, 100, 0.1);
        }

        /* Products Grid - exactly 6 items */
        .products-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 1.5rem;
            margin-bottom: 2rem;
        }

        .product-card {
            background: white;
            border-radius: 20px;
            padding: 1.5rem;
            border: 1px solid #d4e4dc;
            transition: 0.3s;
            position: relative;
        }

        .product-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            border-color: #2e7d64;
        }

        .product-icon {
            font-size: 3rem;
            margin-bottom: 0.5rem;
        }

        .product-category {
            display: inline-block;
            background: #e0f5ee;
            color: #2e7d64;
            font-size: 0.7rem;
            padding: 0.2rem 0.8rem;
            border-radius: 20px;
            margin-bottom: 1rem;
            font-weight: 600;
        }

        .product-name {
            font-size: 1.3rem;
            font-weight: 700;
            color: #1e3a2f;
            margin-bottom: 0.5rem;
        }

        .product-description {
            color: #7f9e8f;
            font-size: 0.85rem;
            margin-bottom: 1rem;
            line-height: 1.5;
            min-height: 60px;
        }

        .product-price {
            font-size: 1.5rem;
            font-weight: 700;
            color: #2e7d64;
            margin-bottom: 0.3rem;
        }

        .product-stock {
            font-size: 0.75rem;
            color: #9ec0ae;
            margin-bottom: 1rem;
        }

        .order-btn {
            width: 100%;
            background: #2e7d64;
            color: white;
            border: none;
            padding: 0.7rem;
            border-radius: 30px;
            font-size: 0.9rem;
            font-weight: 600;
            cursor: pointer;
            transition: 0.2s;
            margin-top: 0.5rem;
        }

        .order-btn:hover {
            background: #236b54;
            transform: translateY(-2px);
        }

        /* Flash Messages */
        .flash {
            padding: 0.8rem;
            border-radius: 12px;
            margin-bottom: 1rem;
            font-size: 0.85rem;
            text-align: center;
        }

        .flash.success {
            background: #e0f5ee;
            color: #2e7d64;
            border-left: 4px solid #2e7d64;
        }

        .flash.error {
            background: #fee9e0;
            color: #c97e5a;
            border-left: 4px solid #c97e5a;
        }

        /* Footer */
        .footer {
            text-align: center;
            padding: 1.5rem;
            color: #9ec0ae;
            font-size: 0.75rem;
            border-top: 1px solid #d4e4dc;
            margin-top: 2rem;
            background: white;
        }

        /* Responsive */
        @media (max-width: 900px) {
            .products-grid {
                grid-template-columns: repeat(2, 1fr);
            }
        }

        @media (max-width: 600px) {
            .products-grid {
                grid-template-columns: 1fr;
            }
            .navbar {
                flex-direction: column;
                text-align: center;
            }
        }
    </style>
</head>
<body>
    <nav class="navbar">
        <div class="logo">
            <span>🌿</span> Forest Grove
        </div>
        <div class="nav-links">
            <a href="{{ url_for('products') }}" class="nav-link">Products</a>
            {% if session.user_id %}
                <a href="{{ url_for('account') }}" class="nav-link">My Account</a>
                <a href="{{ url_for('logout') }}" class="nav-link">Logout</a>
            {% else %}
                <a href="{{ url_for('login') }}" class="login-btn">Login / Sign Up</a>
            {% endif %}
        </div>
    </nav>

    <div class="container">
        <!-- Flash Messages -->
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                    <div class="flash {{ category }}">{{ message }}</div>
                {% endfor %}
            {% endif %}
        {% endwith %}

        <!-- Header -->
        <div class="header">
            <h1>🌱 Fresh from the Forest</h1>
            <p>Organic, locally-sourced ingredients for your table</p>
        </div>

        <!-- Search Bar -->
        <div class="search-bar">
            <input type="text" id="searchInput" placeholder="🔍 Search products..." onkeyup="filterProducts()">
        </div>

        <!-- Products Grid -->
        <div id="productsGrid" class="products-grid">
            {% for product in products %}
            <div class="product-card" data-name="{{ product.name.lower() }}" data-category="{{ product.category.lower() }}">
                <div class="product-icon">{{ product.image }}</div>
                <span class="product-category">{{ product.category }}</span>
                <div class="product-name">{{ product.name }}</div>
                <div class="product-description">{{ product.description }}</div>
                <div class="product-price">${{ "%.2f"|format(product.price) }}</div>
                <div class="product-stock">🌿 In stock: {{ product.stock }} units</div>
                {% if session.user_id %}
                    <button class="order-btn" onclick="orderProduct('{{ product.name }}', {{ product.price }})">Order Now</button>
                {% else %}
                    <button class="order-btn" onclick="window.location.href='{{ url_for('login') }}'">Login to Order</button>
                {% endif %}
            </div>
            {% endfor %}
        </div>
    </div>

    <footer class="footer">
        <p>🌲 Forest Grove • Farm-to-table • Organic • Sustainable • Local</p>
        <p style="margin-top: 0.5rem;">© 2024 Forest Grove. All rights reserved.</p>
    </footer>

    <script>
        // Search filter function
        function filterProducts() {
            const searchTerm = document.getElementById('searchInput').value.toLowerCase();
            const products = document.querySelectorAll('.product-card');
            
            products.forEach(product => {
                const name = product.getAttribute('data-name');
                const category = product.getAttribute('data-category');
                if (name.includes(searchTerm) || category.includes(searchTerm)) {
                    product.style.display = '';
                } else {
                    product.style.display = 'none';
                }
            });
        }

        // Order product function
        function orderProduct(productName, productPrice) {
            alert(`🍽️ "${productName}" has been added to your cart!\n\nPrice: $${productPrice.toFixed(2)}\n\nPlease proceed to checkout.`);
            // You can expand this to add actual cart functionality
        }
    </script>
</body>
</html>

























from flask import Flask, render_template, request, redirect, url_for, session, flash
from functools import wraps
import sqlite3
import hashlib

app = Flask(__name__)
app.secret_key = 'forest-grove-secret-key-2024'

DATABASE = 'greenfield.db'

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    
    # Users table only (no products table)
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
    
    # Orders table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_number TEXT UNIQUE NOT NULL,
            user_id INTEGER,
            customer_name TEXT,
            items TEXT,
            total REAL,
            status TEXT,
            order_date TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    conn.commit()
    conn.close()
    print("✅ Database initialized with users table only!")

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to access your account', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Hardcoded products - 6 items exactly
PRODUCTS = [
    {
        'id': 1,
        'name': 'Organic Kale',
        'category': 'Vegetables',
        'description': 'Fresh, crisp kale from local organic farms. Rich in vitamins A, C, and K. Perfect for salads and smoothies.',
        'price': 3.99,
        'stock': 45,
        'image': '🥬'
    },
    {
        'id': 2,
        'name': 'Wild Mushrooms',
        'category': 'Mushrooms',
        'description': 'Foraged wild mushroom mix including chanterelles and morels. Earthy, aromatic, and full of umami flavor.',
        'price': 8.99,
        'stock': 12,
        'image': '🍄'
    },
    {
        'id': 3,
        'name': 'Heirloom Tomatoes',
        'category': 'Vegetables',
        'description': 'Colorful, ripe heirloom tomatoes. Sweet, juicy, and perfect for salads, sandwiches, or fresh eating.',
        'price': 4.50,
        'stock': 30,
        'image': '🍅'
    },
    {
        'id': 4,
        'name': 'Forest Honey',
        'category': 'Pantry',
        'description': 'Raw, unfiltered local honey from sustainable apiaries. Naturally sweet with wildflower notes.',
        'price': 12.99,
        'stock': 25,
        'image': '🍯'
    },
    {
        'id': 5,
        'name': 'Artisan Bread',
        'category': 'Bakery',
        'description': 'Sourdough loaf baked fresh daily. Crispy crust, soft interior, made with organic flour.',
        'price': 5.99,
        'stock': 8,
        'image': '🍞'
    },
    {
        'id': 6,
        'name': 'Maple Syrup',
        'category': 'Pantry',
        'description': 'Pure Vermont maple syrup. Grade A dark and robust flavor. Perfect for pancakes and baking.',
        'price': 14.99,
        'stock': 18,
        'image': '🍁'
    }
]

@app.route('/')
def index():
    return redirect(url_for('products'))

@app.route('/products')
def products():
    """Products page - hardcoded products, no database needed"""
    return render_template('products.html', products=PRODUCTS)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        conn = get_db()
        cursor = conn.cursor()
        hashed_pw = hash_password(password)
        user = cursor.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, hashed_pw)).fetchone()
        conn.close()
        
        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['full_name'] = user['full_name']
            flash(f'Welcome back, {user["full_name"]}!', 'success')
            return redirect(url_for('products'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('login.html')

@app.route('/signup', methods=['POST'])
def signup():
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '')
    confirm_password = request.form.get('confirm_password', '')
    full_name = request.form.get('full_name', '').strip()
    email = request.form.get('email', '').strip()
    phone = request.form.get('phone', '').strip()
    address = request.form.get('address', '').strip()
    
    errors = []
    if not username or len(username) < 3:
        errors.append('Username must be at least 3 characters')
    if not password or len(password) < 4:
        errors.append('Password must be at least 4 characters')
    if password != confirm_password:
        errors.append('Passwords do not match')
    if not full_name:
        errors.append('Full name is required')
    
    if errors:
        for error in errors:
            flash(error, 'error')
        return redirect(url_for('login'))
    
    conn = get_db()
    cursor = conn.cursor()
    existing = cursor.execute('SELECT id FROM users WHERE username = ?', (username,)).fetchone()
    
    if existing:
        flash('Username already exists', 'error')
        conn.close()
        return redirect(url_for('login'))
    
    hashed_pw = hash_password(password)
    cursor.execute('INSERT INTO users (username, password, full_name, email, phone, address) VALUES (?, ?, ?, ?, ?, ?)',
                   (username, hashed_pw, full_name, email, phone, address))
    conn.commit()
    
    user = cursor.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
    conn.close()
    
    session['user_id'] = user['id']
    session['username'] = user['username']
    session['full_name'] = user['full_name']
    
    flash(f'Account created! Welcome, {full_name}!', 'success')
    return redirect(url_for('products'))

@app.route('/account')
@login_required
def account():
    conn = get_db()
    cursor = conn.cursor()
    user = cursor.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
    
    # Get past orders
    past_orders = cursor.execute('''
        SELECT * FROM orders WHERE user_id = ? AND status = 'delivered' ORDER BY id DESC
    ''', (session['user_id'],)).fetchall()
    
    conn.close()
    
    return render_template('account.html', user=user, past_orders=past_orders)

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully', 'success')
    return redirect(url_for('products'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5000)
