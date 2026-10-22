from flask import Blueprint, render_template, Response
from models import db, Sale, Batch
from analytics import build_dashboard_data
from routes.auth import login_required
from datetime import date, timedelta
import csv
from io import StringIO

main_bp = Blueprint('main', __name__)

@main_bp.route("/")
@login_required
def dashboard():
    data = build_dashboard_data(db)
    return render_template("dashboard.html", **data)

@main_bp.route("/export/expiry")
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

@main_bp.route("/export/sales")
@login_required
def export_sales():
    sales = Sale.query.order_by(Sale.date.desc()).all()
    si = StringIO()
    cw = csv.writer(si)
    cw.writerow(["Sale ID", "Date", "Payment Method", "Total Amount", "Profit", "Items"])
    for s in sales:
        cw.writerow([s.id, s.date, s.payment_method, f"{s.total_amount:.2f}", f"{s.profit:.2f}", len(s.items)])
    return Response(si.getvalue(), mimetype="text/csv", headers={"Content-Disposition": f"attachment;filename=sales_history_{date.today()}.csv"})