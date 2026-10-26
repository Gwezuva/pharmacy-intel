from flask import Blueprint, render_template, request, redirect, url_for, session
from models import db, User, bcrypt
from routes.auth import login_required, admin_required

users_bp = Blueprint('users', __name__)

def is_strong_password(password):
    """Check if password is at least 8 chars, contains a letter and a number."""
    if len(password) < 8: return False
    has_letter = any(c.isalpha() for c in password)
    has_number = any(c.isdigit() for c in password)
    return has_letter and has_number

@users_bp.route("/staff")
@login_required
@admin_required
def manage_staff():
    staff = User.query.all()
    return render_template("staff.html", staff=staff)

@users_bp.route("/staff/add", methods=["POST"])
@login_required
@admin_required
def add_staff():
    full_name = request.form.get("full_name")
    username = request.form.get("username")
    password = request.form.get("password")
    role = request.form.get("role")

    # 1. Enforce Strong Password
    if not is_strong_password(password):
        return "Error: Password must be at least 8 characters long and contain both letters and numbers.", 400

    # 2. Check if username exists
    if User.query.filter_by(username=username).first():
        return "Error: Username already exists.", 400

    # 3. Create User
    hashed_pw = bcrypt.generate_password_hash(password).decode('utf-8')
    new_user = User(full_name=full_name, username=username, password_hash=hashed_pw, role=role)
    db.session.add(new_user)
    db.session.commit()

    return redirect(url_for('users.manage_staff'))

@users_bp.route("/staff/change-password/<int:user_id>", methods=["POST"])
@login_required
def change_password(user_id):
    # Users can change their own password, but only Admins can change others
    if session.get('role') != 'admin' and session.get('user_id') != user_id:
        return "Access Denied", 403

    new_password = request.form.get("new_password")

    if not is_strong_password(new_password):
        return "Error: Password must be at least 8 characters long and contain both letters and numbers.", 400

    user = User.query.get_or_404(user_id)
    user.password_hash = bcrypt.generate_password_hash(new_password).decode('utf-8')
    db.session.commit()
    return redirect(url_for('users.manage_staff' if session.get('role') == 'admin' else 'main.dashboard'))

@users_bp.route("/staff/toggle/<int:user_id>")
@login_required
@admin_required
def toggle_staff(user_id):
    user = User.query.get_or_404(user_id)
    if user.username != "admin": # Prevent admin from locking themselves out
        user.is_active = not user.is_active
        db.session.commit()
    return redirect(url_for('users.manage_staff'))