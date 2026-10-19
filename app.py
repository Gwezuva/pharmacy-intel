from flask import Flask, render_template, request, jsonify, Response, redirect, url_for, session
from models import db, Medicine, Batch, Sale, SaleItem, Supplier
from analytics import build_dashboard_data
from datetime import date, timedelta
from functools import wraps
import csv
from io import StringIO
import os
import json
import random

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///pharmacy.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
# CRITICAL: This is required for sessions (login) to work!
app.secret_key = "pharmaintel-super-secret-key-change-me-later"

db.init_app(app)


# ---------- AUTHENTICATION ----------
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        
        if username == "admin" and password == "admin123":
            session['logged_in'] = True
            return redirect(url_for('dashboard'))
        else:
            error = "Invalid credentials. Please try again."
            
    return render_template("login.html", error=error)

@app.route("/logout")
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))


# ---------- PROTECTED ROUTES ----------
@app.route("/")
@login_required
def dashboard():
    data = build_dashboard_data(db)
    return render_template("dashboard.html", **data)


@app.route("/medicines")
@login_required
def medicines():
    items = Medicine.query.order_by(Medicine.name).all()
    return render_template("medicines.html", medicines=items, today=date.today())


@app.route("/medicine/<int:med_id>")
@login_required
def medicine_detail(med_id):
    med = Medicine.query.get_or_404(med_id)
    batches = Batch.query.filter_by(medicine_id=med.id).order_by(Batch.expiry_date.asc()).all()
    total_stock = sum(b.quantity for b in batches if b.expiry_date > date.today())
    return render_template("medicine_detail.html", med=med, batches=batches, total_stock=total_stock, today=date.today())


@app.route("/medicine/<int:med_id>/restock", methods=["POST"])
@login_required
def restock(med_id):
    med = Medicine.query.get_or_404(med_id)
    qty = int(request.form.get("quantity", 0))
    expiry_str = request.form.get("expiry_date")
    
    if qty > 0 and expiry_str:
        new_batch = Batch(
            medicine_id=med.id,
            batch_no=request.form.get("batch_no") or f"B{random.randint(10000,99999)}",
            quantity=qty,
            expiry_date=date.fromisoformat(expiry_str),
            received_date=date.today(),
            cost_price=float(request.form.get("cost_price", med.cost_price))
        )
        db.session.add(new_batch)
        db.session.commit()
    return redirect(url_for("medicine_detail", med_id=med.id))


# ---------- POS FLOW ----------
@app.route("/new-sale")
@login_required
def new_sale():
    meds = Medicine.query.order_by(Medicine.name).all()
    return render_template("new_sale.html", medicines=meds)


@app.route("/checkout", methods=["POST"])
@login_required
def checkout():
    cart_json = request.form.get("cart")
    cart = json.loads(cart_json) if cart_json else []
    
    total = 0.0
    profit = 0.0
    for item in cart:
        med = Medicine.query.get(item['id'])
        if med:
            total += med.selling_price * item['qty']
            profit += (med.selling_price - med.cost_price) * item['qty']

    return render_template("checkout.html", cart=cart, cart_json=cart_json, total=total, profit=profit)


@app.route("/process-sale", methods=["POST"])
@login_required
def process_sale():
    cart_json = request.form.get("cart")
    cart = json.loads(cart_json) if cart_json else []
    payment_method = request.form.get("payment_method", "cash")
    
    today = date.today()
    sale = Sale(date=today, payment_method=payment_method, total_amount=0.0, profit=0.0)
    db.session.add(sale)
    db.session.flush()

    total = 0.0
    profit = 0.0

    for item in cart:
        med = Medicine.query.get(item['id'])
        qty = int(item['qty'])
        if not med: continue

        batch = Batch.query.filter(
            Batch.medicine_id == med.id,
            Batch.expiry_date > today,
            Batch.quantity >= qty,
        ).order_by(Batch.expiry_date.asc()).first()

        if batch:
            batch.quantity -= qty
            line_total = med.selling_price * qty
            line_profit = (med.selling_price - med.cost_price) * qty

            db.session.add(SaleItem(
                sale_id=sale.id, medicine_id=med.id, batch_id=batch.id,
                qty=qty, unit_price=med.selling_price, cost_price=med.cost_price
            ))
            total += line_total
            profit += line_profit

    sale.total_amount = round(total, 2)
    sale.profit = round(profit, 2)
    db.session.commit()

    return redirect(url_for("receipt", sale_id=sale.id))


@app.route("/receipt/<int:sale_id>")
@login_required
def receipt(sale_id):
    sale = Sale.query.get_or_404(sale_id)
    return render_template("receipt.html", sale=sale)


# ---------- EXPORTS ----------
@app.route("/export/expiry")
@login_required
def export_expiry():
    today = date.today()
    horizon = today + timedelta(days=60)
    expiring = db.session.query(Batch).filter(Batch.expiry_date <= horizon, Batch.expiry_date > today, Batch.quantity > 0).all()
    
    si = StringIO()
    cw = csv.writer(si)
    cw.writerow(["Medicine", "Batch", "Qty", "Expiry", "Days", "Value"])
    for b in expiring:
        cw.writerow([b.medicine.name, b.batch_no, b.quantity, b.expiry_date, (b.expiry_date - today).days, f"{b.quantity * b.cost_price:.2f}"])
        
    return Response(si.getvalue(), mimetype="text/csv", headers={"Content-Disposition": "attachment;filename=expiry.csv"})


@app.route("/export/sales")
@login_required
def export_sales():
    sales = Sale.query.order_by(Sale.date.desc()).all()

    si = StringIO()
    cw = csv.writer(si)
    cw.writerow(["Sale ID", "Date", "Payment Method", "Total Amount", "Profit", "Items"])

    for s in sales:
        cw.writerow([
            s.id,
            s.date,
            s.payment_method,
            f"{s.total_amount:.2f}",
            f"{s.profit:.2f}",
            len(s.items)
        ])

    output = si.getvalue()
    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment;filename=sales_history_{date.today()}.csv"}
    )


if __name__ == "__main__":
    with app.app_context():
        os.makedirs("instance", exist_ok=True)
        db.create_all()
    app.run(debug=True)