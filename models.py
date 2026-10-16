from flask_sqlalchemy import SQLAlchemy
from datetime import date

db = SQLAlchemy()


class Supplier(db.Model):
    __tablename__ = "suppliers"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    contact = db.Column(db.String(120))
    lead_time_days = db.Column(db.Integer, default=3)

    medicines = db.relationship("Medicine", backref="supplier", lazy=True)


class Medicine(db.Model):
    __tablename__ = "medicines"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    category = db.Column(db.String(80))
    unit = db.Column(db.String(20), default="tablet")
    cost_price = db.Column(db.Float, default=0.0)
    selling_price = db.Column(db.Float, default=0.0)
    reorder_level = db.Column(db.Integer, default=20)
    supplier_id = db.Column(db.Integer, db.ForeignKey("suppliers.id"))

    batches = db.relationship("Batch", backref="medicine", lazy=True)
    sale_items = db.relationship("SaleItem", backref="medicine", lazy=True)


class Batch(db.Model):
    __tablename__ = "batches"
    id = db.Column(db.Integer, primary_key=True)
    medicine_id = db.Column(db.Integer, db.ForeignKey("medicines.id"), nullable=False)
    batch_no = db.Column(db.String(60))
    quantity = db.Column(db.Integer, default=0)
    expiry_date = db.Column(db.Date, nullable=False)
    received_date = db.Column(db.Date, default=date.today)
    cost_price = db.Column(db.Float, default=0.0)


class Sale(db.Model):
    __tablename__ = "sales"
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, default=date.today)
    total_amount = db.Column(db.Float, default=0.0)
    profit = db.Column(db.Float, default=0.0)
    payment_method = db.Column(db.String(30), default="cash")

    items = db.relationship("SaleItem", backref="sale", lazy=True,
                            cascade="all, delete-orphan")


class SaleItem(db.Model):
    __tablename__ = "sale_items"
    id = db.Column(db.Integer, primary_key=True)
    sale_id = db.Column(db.Integer, db.ForeignKey("sales.id"), nullable=False)
    medicine_id = db.Column(db.Integer, db.ForeignKey("medicines.id"), nullable=False)
    batch_id = db.Column(db.Integer, db.ForeignKey("batches.id"))
    qty = db.Column(db.Integer, default=1)
    unit_price = db.Column(db.Float, default=0.0)
    cost_price = db.Column(db.Float, default=0.0)