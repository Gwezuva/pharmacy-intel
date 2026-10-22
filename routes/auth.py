from flask import Blueprint, render_template, request, redirect, url_for, session
from functools import wraps
from models import db, User, bcrypt

auth_bp = Blueprint('auth', __name__)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        
        # Query the database for the user
        user = User.query.filter_by(username=username).first()
        
        # Check if user exists, account is active, and password is correct
        if user and user.is_active and bcrypt.check_password_hash(user.password_hash, password):
            session['logged_in'] = True
            session['user_id'] = user.id
            session['username'] = user.username
            session['role'] = user.role
            return redirect(url_for('main.dashboard'))
        else:
            error = "Invalid credentials or inactive account. Please try again."
            
    return render_template("login.html", error=error)

@auth_bp.route("/logout")
def logout():
    session.clear() # Clears all session data securely
    return redirect(url_for('auth.login'))