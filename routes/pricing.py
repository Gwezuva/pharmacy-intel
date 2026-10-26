from flask import Blueprint, render_template, request, redirect, url_for
from models import db, Medicine
from routes.auth import login_required, admin_required

pricing_bp = Blueprint('pricing', __name__)

@pricing_bp.route("/pricing")
@login_required
@admin_required
def manage_pricing():
    """View all medicines with their cost, selling price, and profit margins."""
    medicines = Medicine.query.order_by(Medicine.name).all()
    return render_template("pricing.html", medicines=medicines)

@pricing_bp.route("/pricing/update/<int:med_id>", methods=["POST"])
@login_required
@admin_required
def update_selling_price(med_id):
    """Update the selling price of a specific medicine."""
    med = Medicine.query.get_or_404(med_id)
    new_price = request.form.get("new_price")
    
    if new_price:
        try:
            med.selling_price = float(new_price)
            db.session.commit()
        except ValueError:
            pass # Silently ignore bad input, or add a flash message later
            
    return redirect(url_for('pricing.manage_pricing'))