from flask import Blueprint, render_template, request, redirect, url_for
from models import db, Medicine, Batch
from routes.auth import login_required, admin_required
from datetime import date
import random

inventory_bp = Blueprint('inventory', __name__)

@inventory_bp.route("/medicines")
@login_required
def medicines():
    items = Medicine.query.order_by(Medicine.name).all()
    return render_template("medicines.html", medicines=items, today=date.today())

@inventory_bp.route("/medicine/<int:med_id>")
@login_required
def medicine_detail(med_id):
    med = Medicine.query.get_or_404(med_id)
    batches = Batch.query.filter_by(medicine_id=med.id).order_by(Batch.expiry_date.asc()).all()
    total_stock = sum(b.quantity for b in batches if b.expiry_date > date.today())
    return render_template("medicine_detail.html", med=med, batches=batches, total_stock=total_stock, today=date.today())

@inventory_bp.route("/medicine/<int:med_id>/restock", methods=["POST"])
@login_required
@admin_required  # <--- CASHIERS CANNOT DO THIS
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
    return redirect(url_for("inventory.medicine_detail", med_id=med.id))