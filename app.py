from flask import Flask, render_template, request, jsonify, redirect, url_for
from models import db, Medicine, Batch, Sale, SaleItem, Supplier
from analytics import build_dashboard_data
from datetime import date
import os

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///pharmacy.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)


@app.route("/")
def dashboard():
    data = build_dashboard_data(db)
    return render_template("dashboard.html", **data)


@app.route("/medicines")
def medicines():
    items = Medicine.query.order_by(Medicine.name).all()
    return render_template("medicines.html", medicines=items)


# ---------- POS: New Sale ----------
@app.route("/new-sale", methods=["GET", "POST"])
def new_sale():
    if request.method == "GET":
        meds = Medicine.query.order_by(Medicine.name).all()
        recent = Sale.query.order_by(Sale.id.desc()).limit(10).all()
        return render_template("new_sale.html", medicines=meds, recent=recent)

    # POST — create the sale
    data = request.get_json()
    if not data or not data.get("items"):
        return jsonify({"ok": False, "error": "Cart is empty"}), 400

    today = date.today()
    sale = Sale(
        date=today,
        payment_method=data.get("payment_method", "cash"),
        total_amount=0.0,
        profit=0.0,
    )
    db.session.add(sale)
    db.session.flush()

    total = 0.0
    profit = 0.0
    errors = []

    for line in data["items"]:
        med = Medicine.query.get(line["medicine_id"])
        qty = int(line["qty"])
        if not med or qty <= 0:
            continue

        # pick earliest-expiring non-expired batch with stock
        batch = Batch.query.filter(
            Batch.medicine_id == med.id,
            Batch.expiry_date > today,
            Batch.quantity >= qty,
        ).order_by(Batch.expiry_date.asc()).first()

        if not batch:
            errors.append(f"Not enough stock for {med.name}")
            continue

        batch.quantity -= qty

        unit_price = med.selling_price
        cost_price = med.cost_price
        line_total = unit_price * qty
        line_profit = (unit_price - cost_price) * qty

        item = SaleItem(
            sale_id=sale.id,
            medicine_id=med.id,
            batch_id=batch.id,
            qty=qty,
            unit_price=unit_price,
            cost_price=cost_price,
        )
        db.session.add(item)
        total += line_total
        profit += line_profit

    if errors and not sale.items:
        db.session.rollback()
        return jsonify({"ok": False, "error": "; ".join(errors)}), 400

    sale.total_amount = round(total, 2)
    sale.profit = round(profit, 2)
    db.session.commit()

    return jsonify({
        "ok": True,
        "sale_id": sale.id,
        "total": sale.total_amount,
        "profit": sale.profit,
        "warnings": errors,
    })


if __name__ == "__main__":
    with app.app_context():
        os.makedirs("instance", exist_ok=True)
        db.create_all()
    app.run(debug=True)