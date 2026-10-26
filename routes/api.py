from flask import Blueprint, jsonify, request
from models import Medicine, Batch
from datetime import date
from routes.auth import login_required

api_bp = Blueprint('api', __name__)

@api_bp.route("/api/search-medicines")
@login_required
def search_medicines():
    query = request.args.get("q", "").lower()
    
    # Get all medicines that match the search
    meds = Medicine.query.filter(Medicine.name.ilike(f"%{query}%")).limit(10).all()
    
    results = []
    for m in meds:
        # Calculate valid stock
        stock = sum(b.quantity for b in m.batches if b.expiry_date > date.today())
        
        results.append({
            "id": m.id,
            "name": m.name,
            "price": m.selling_price,
            "stock": stock
        })
        
    return jsonify(results)