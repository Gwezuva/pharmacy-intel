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

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('role') != 'admin':
            return "Access Denied: Admins Only", 403
        return f(*args, **kwargs)
    return decorated_function

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        try:
            username = request.form.get("username", "").strip()
            password = request.form.get("password", "").strip()
            
            user = User.query.filter_by(username=username).first()
            
            if user and user.is_active and bcrypt.check_password_hash(user.password_hash, password):
                session['logged_in'] = True
                session['user_id'] = user.id
                session['username'] = user.username
                session['role'] = user.role
                
                if user.role == 'admin':
                    return redirect(url_for('main.dashboard'))
                else:
                    return redirect(url_for('pos.new_sale'))
            else:
                error = "Invalid credentials or inactive account. Please try again."
        except Exception as e:
            # THIS IS THE MAGIC LINE: It will print the exact error on your screen
            return f"<h1>System Error Debug</h1><p style='color:red; font-size:20px;'>{str(e)}</p>"
            
    return render_template("login.html", error=error)

@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for('auth.login'))