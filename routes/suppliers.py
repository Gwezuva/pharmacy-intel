from flask import Blueprint, render_template, request, redirect, url_for
from models import db, Supplier, Medicine, Batch
from routes.auth import login_required, admin_required
from datetime import date
from sqlalchemy import func

suppliers_bp = Blueprint('suppliers', __name__)

@suppliers_bp.route("/suppliers")
@login_required
@admin_required
def manage_suppliers():
    all_suppliers = Supplier.query.order_by(Supplier.name).all()
    supplier_data = []
    for s in all_suppliers:
        stock_val = db.session.query(func.sum(Batch.quantity * Batch.cost_price)).join(Medicine).filter(Medicine.supplier_id == s.id, Batch.expiry_date > date.today()).scalar() or 0
        supplier_data.append({"id": s.id, "name": s.name, "contact": s.contact, "lead_time": s.lead_time_days, "stock_val": round(stock_val, 2)})
    return render_template("suppliers.html", suppliers=supplier_data)

@suppliers_bp.route("/suppliers/add", methods=["POST"])
@login_required
@admin_required
def add_supplier():
    name = request.form.get("name")
    contact = request.form.get("contact")
    lead_time = int(request.form.get("lead_time", 3))
    if name:
        db.session.add(Supplier(name=name, contact=contact, lead_time_days=lead_time))
        db.session.commit()
    return redirect(url_for('suppliers.manage_suppliers'))

@suppliers_bp.route("/suppliers/delete/<int:supplier_id>")
@login_required
@admin_required
def delete_supplier(supplier_id):
    supplier = Supplier.query.get_or_404(supplier_id)
    Medicine.query.filter_by(supplier_id=supplier.id).update({"supplier_id": None})
    db.session.delete(supplier)
    db.session.commit()
    return redirect(url_for('suppliers.manage_suppliers'))

@suppliers_bp.route("/supplier/<int:supplier_id>")
@login_required
@admin_required
def supplier_detail(supplier_id):
    supplier = Supplier.query.get_or_404(supplier_id)
    meds = Medicine.query.filter_by(supplier_id=supplier.id).order_by(Medicine.name).all()
    unassigned_meds = Medicine.query.filter((Medicine.supplier_id != supplier.id) | (Medicine.supplier_id == None)).order_by(Medicine.name).all()
    
    meds_data = []
    for m in meds:
        current_stock = sum(b.quantity for b in m.batches if b.expiry_date > date.today())
        meds_data.append({
            "id": m.id, "name": m.name, "cost": m.cost_price, "stock": current_stock, "reorder_level": m.reorder_level,
            "needs_order": current_stock <= m.reorder_level
        })
    return render_template("supplier_detail.html", supplier=supplier, medicines=meds_data, unassigned_meds=unassigned_meds)

@suppliers_bp.route("/supplier/<int:supplier_id>/add-medicine", methods=["POST"])
@login_required
@admin_required
def add_medicine_to_supplier(supplier_id):
    med_id = request.form.get("medicine_id")
    if med_id:
        med = Medicine.query.get(med_id)
        if med:
            med.supplier_id = supplier_id
            db.session.commit()
    return redirect(url_for('suppliers.supplier_detail', supplier_id=supplier_id))

@suppliers_bp.route("/supplier/<int:supplier_id>/remove-medicine/<int:med_id>")
@login_required
@admin_required
def remove_medicine_from_supplier(supplier_id, med_id):
    med = Medicine.query.get_or_404(med_id)
    med.supplier_id = None
    db.session.commit()
    return redirect(url_for('suppliers.supplier_detail', supplier_id=supplier_id))

# --- NEW ROUTE: Update the price of a medicine ---
@suppliers_bp.route("/supplier/<int:supplier_id>/update-price/<int:med_id>", methods=["POST"])
@login_required
@admin_required
def update_medicine_price(supplier_id, med_id):
    med = Medicine.query.get_or_404(med_id)
    new_cost = request.form.get("new_cost")
    if new_cost:
        try:
            med.cost_price = float(new_cost)
            db.session.commit()
        except ValueError:
            pass # Handle bad input silently for now
    return redirect(url_for('suppliers.supplier_detail', supplier_id=supplier_id))

@suppliers_bp.route("/supplier/<int:supplier_id>/purchase-order")
@login_required
@admin_required
def generate_po(supplier_id):
    supplier = Supplier.query.get_or_404(supplier_id)
    meds = Medicine.query.filter_by(supplier_id=supplier.id).all()
    order_items = []
    for m in meds:
        current_stock = sum(b.quantity for b in m.batches if b.expiry_date > date.today())
        if current_stock <= m.reorder_level:
            order_items.append({
                "id": m.id, "name": m.name, "current_stock": current_stock,
                "suggested_qty": max((m.reorder_level * 3) - current_stock, 10),
                "unit_cost": m.cost_price
            })
    return render_template("purchase_order.html", supplier=supplier, order_items=order_items, today=date.today())