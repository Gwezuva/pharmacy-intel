from flask import Blueprint, render_template, request, redirect, url_for
from models import db, Medicine, Batch, Sale, SaleItem
from routes.auth import login_required
from datetime import date
import json

pos_bp = Blueprint('pos', __name__)

@pos_bp.route("/new-sale")
@login_required
def new_sale():
    meds = Medicine.query.order_by(Medicine.name).all()
    return render_template("new_sale.html", medicines=meds)

@pos_bp.route("/checkout", methods=["POST"])
@login_required
def checkout():
    cart_json = request.form.get("cart")
    cart = json.loads(cart_json) if cart_json else []
    
    total = sum(Medicine.query.get(item['id']).selling_price * item['qty'] for item in cart if Medicine.query.get(item['id']))
    profit = sum((Medicine.query.get(item['id']).selling_price - Medicine.query.get(item['id']).cost_price) * item['qty'] for item in cart if Medicine.query.get(item['id']))

    return render_template("checkout.html", cart=cart, cart_json=cart_json, total=total, profit=profit)

@pos_bp.route("/process-sale", methods=["POST"])
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

        batch = Batch.query.filter(Batch.medicine_id == med.id, Batch.expiry_date > today, Batch.quantity >= qty).order_by(Batch.expiry_date.asc()).first()

        if batch:
            batch.quantity -= qty
            line_total = med.selling_price * qty
            line_profit = (med.selling_price - med.cost_price) * qty

            db.session.add(SaleItem(sale_id=sale.id, medicine_id=med.id, batch_id=batch.id, qty=qty, unit_price=med.selling_price, cost_price=med.cost_price))
            total += line_total
            profit += line_profit

    sale.total_amount = round(total, 2)
    sale.profit = round(profit, 2)
    db.session.commit()

    return redirect(url_for("pos.receipt", sale_id=sale.id))

@pos_bp.route("/receipt/<int:sale_id>")
@login_required
def receipt(sale_id):
    sale = Sale.query.get_or_404(sale_id)
    return render_template("receipt.html", sale=sale)