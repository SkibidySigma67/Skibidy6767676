from flask import Flask, render_template, request, redirect, session
import sqlite3 as sql

 ## Create App ##
app = Flask(__name__)
app.secret_key = "secret123"

## Create app Routes 
@app.route("/")
def Home():
    return render_template("index.html")

@app.route("/Login", methods=["GET", "POST"])
def Login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        
        conn = sql.connect('your_database.db')
        conn.row_factory = sql.Row
        cursor = conn.cursor()
        
        # Get user by email
        cursor.execute("SELECT * FROM Member WHERE Email = ?", (email,))
        member = cursor.fetchone()
        conn.close()
        
        # Direct password comparison (NO hashing)
        if member and member['Password'] == password:  # Plain text comparison
            # Store user info in session
            session['member_id'] = member['MemID']
            session['first_name'] = member['First Name']
            session['last_name'] = member['Last_Name']
            session['email'] = member['Email']
            
            return "Welcome Admin!"  # Or redirect to dashboard
        else:
            return render_template("login.html", error="Invalid email or password")
    
    return render_template("login.html")
    

@app.route("/CreateAccount", methods=["GET", "POST"])
def CreateAccount():
    if request.method == "POST":
        # Get form data
        first_name = request.form.get("first_name")
        last_name = request.form.get("last_name")
        email = request.form.get("email")
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")
        
        # Basic validation
        if not first_name or not last_name or not email or not password:
            return render_template("create_account.html", error="All fields are required!")
        
        if password != confirm_password:
            return render_template("create_account.html", error="Passwords do not match!")
        
        try:
            # Connect to database
            conn = sql.connect('your_database.db')
            cursor = conn.cursor()
            
            # Insert new member with PLAIN TEXT password (NOT recommended for production!)
            cursor.execute("""
                INSERT INTO Member ("First Name", Last_Name, Email, Password) 
                VALUES (?, ?, ?, ?)
            """, (first_name, last_name, email, password))  # Password stored as-is
            
            conn.commit()
            conn.close()
            
            # Redirect to login page with success message
            return render_template("login.html", success="Account created successfully! Please login.")
            
        except sql.IntegrityError:
            return render_template("create_account.html", error="Email already registered!")
        except Exception as e:
            return render_template("create_account.html", error=f"An error occurred: {str(e)}")
    
    # GET request - show the create account form
    return render_template("create_account.html")
    

@app.route("/Fitness_Center")
def Fitness_Center():
    return render_template("Fitness_Center.html")

@app.route("/Membership")
def Membership():
    return render_template("Membership.html")

@app.route("/Room_Hire")
def Room_Hire():
    return render_template("Room_Hire.html")

if __name__ == "__main__":
    app.run(debug=True)
