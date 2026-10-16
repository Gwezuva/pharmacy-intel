import random
from datetime import date, timedelta
from app import app
from models import db, Supplier, Medicine, Batch, Sale, SaleItem

random.seed(42)

SUPPLIERS = ["MediCore Ltd", "PharmaLink", "HealthBridge", "Apex Drugs",
             "CureWell Supplies", "BioSource", "GlobalRx", "NovaMeds"]

MEDICINES = [
    ("Paracetamol 500mg", "Painkiller", 0.05, 0.15),
    ("Ibuprofen 400mg", "Painkiller", 0.08, 0.20),
    ("Aspirin 75mg", "Painkiller", 0.04, 0.12),
    ("Amoxicillin 250mg", "Antibiotic", 0.15, 0.40),
    ("Azithromycin 500mg", "Antibiotic", 0.40, 0.90),
    ("Ciprofloxacin 500mg", "Antibiotic", 0.25, 0.60),
    ("Metformin 500mg", "Diabetes", 0.06, 0.18),
    ("Glibenclamide 5mg", "Diabetes", 0.07, 0.20),
    ("Insulin (10ml)", "Diabetes", 4.50, 8.00),
    ("Atorvastatin 20mg", "Cardiac", 0.12, 0.35),
    ("Amlodipine 5mg", "Cardiac", 0.08, 0.25),
    ("Losartan 50mg", "Cardiac", 0.10, 0.28),
    ("Omeprazole 20mg", "Gastric", 0.09, 0.25),
    ("Ranitidine 150mg", "Gastric", 0.06, 0.18),
    ("Cetirizine 10mg", "Antihistamine", 0.05, 0.15),
    ("Loratadine 10mg", "Antihistamine", 0.07, 0.18),
    ("Vitamin C 1000mg", "Supplement", 0.08, 0.25),
    ("Vitamin D3", "Supplement", 0.10, 0.30),
    ("Multivitamin", "Supplement", 0.12, 0.35),
    ("Iron Tablets", "Supplement", 0.06, 0.18),
    ("Cough Syrup 100ml", "Respiratory", 0.80, 2.00),
    ("Salbutamol Inhaler", "Respiratory", 3.00, 6.50),
    ("ORS Sachet", "Rehydration", 0.15, 0.40),
    ("Antacid Suspension", "Gastric", 0.70, 1.80),
    ("Betadine Ointment", "Topical", 1.20, 2.80),
    ("Hydrocortisone Cream", "Topical", 0.90, 2.20),
    ("Eye Drops", "Ophthalmic", 1.50, 3.50),
    ("Antifungal Cream", "Topical", 1.10, 2.60),
    ("Insulin Pen", "Diabetes", 6.00, 12.00),
    ("Zinc Tablets", "Supplement", 0.05, 0.15),
]


def run():
    with app.app_context():
        db.drop_all()
        db.create_all()
        print("Cleared old data, tables recreated.")

        # Suppliers
        suppliers = []
        for name in SUPPLIERS:
            s = Supplier(
                name=name,
                contact=f"+1-555-{random.randint(1000,9999)}",
                lead_time_days=random.randint(2, 7),
            )
            db.session.add(s)
            suppliers.append(s)
        db.session.commit()
        print(f"Added {len(suppliers)} suppliers.")

        # Medicines
        medicines = []
        for name, cat, cost, price in MEDICINES:
            m = Medicine(
                name=name,
                category=cat,
                unit="unit",
                cost_price=cost,
                selling_price=price,
                reorder_level=random.randint(15, 50),
                supplier_id=random.choice(suppliers).id,
            )
            db.session.add(m)
            medicines.append(m)
        db.session.commit()
        print(f"Added {len(medicines)} medicines.")

        # Batches — mix of fresh, near-expiry, and expired
        batches = []
        today = date.today()
        for m in medicines:
            n_batches = random.randint(1, 4)
            for i in range(n_batches):
                # Random expiry between -10 days (expired) and +400 days
                days_offset = random.choice([
                    random.randint(-10, 20),      # already/nearly expired
                    random.randint(30, 90),       # near expiry
                    random.randint(120, 400),     # healthy
                    random.randint(120, 400),
                ])
                b = Batch(
                    medicine_id=m.id,
                    batch_no=f"B{random.randint(10000,99999)}",
                    quantity=random.randint(20, 300),
                    expiry_date=today + timedelta(days=days_offset),
                    received_date=today - timedelta(days=random.randint(5, 120)),
                    cost_price=m.cost_price,
                )
                db.session.add(b)
                batches.append(b)
        db.session.commit()
        print(f"Added {len(batches)} batches.")

        # Sales — last 90 days
        sales_count = 0
        items_count = 0
        for day_offset in range(90, -1, -1):
            sale_date = today - timedelta(days=day_offset)
            # more sales on recent days, fewer on weekends
            n_sales = random.randint(2, 8) if sale_date.weekday() < 5 else random.randint(1, 4)

            for _ in range(n_sales):
                sale = Sale(
                    date=sale_date,
                    payment_method=random.choice(["cash", "card", "mobile"]),
                    total_amount=0.0,
                    profit=0.0,
                )
                db.session.add(sale)
                db.session.flush()  # get sale.id

                total = 0.0
                profit = 0.0
                n_items = random.randint(1, 4)
                chosen = random.sample(medicines, n_items)

                for m in chosen:
                    qty = random.randint(1, 5)
                    unit_price = m.selling_price
                    cost = m.cost_price
                    line_total = qty * unit_price
                    line_profit = qty * (unit_price - cost)

                    # pick a non-expired batch if possible
                    valid_batches = [b for b in m.batches if b.expiry_date >= today and b.quantity > 0]
                    batch = random.choice(valid_batches) if valid_batches else None
                    if batch:
                        batch.quantity = max(0, batch.quantity - qty)

                    item = SaleItem(
                        sale_id=sale.id,
                        medicine_id=m.id,
                        batch_id=batch.id if batch else None,
                        qty=qty,
                        unit_price=unit_price,
                        cost_price=cost,
                    )
                    db.session.add(item)
                    total += line_total
                    profit += line_profit
                    items_count += 1

                sale.total_amount = round(total, 2)
                sale.profit = round(profit, 2)
                sales_count += 1

        db.session.commit()
        print(f"Added {sales_count} sales with {items_count} line items.")
        print("\n✅ Seed complete!")


if __name__ == "__main__":
    run()