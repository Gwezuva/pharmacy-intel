from models import db, Supplier, Medicine, Batch, Sale, SaleItem, User
from config import Config
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

def migrate():
    print("Starting migration from SQLite to PostgreSQL...")

    # 1. Connect to the old SQLite database
    sqlite_engine = create_engine('sqlite:///instance/pharmacy.db')
    SQLiteSession = sessionmaker(bind=sqlite_engine)
    source_session = SQLiteSession()

    # 2. Connect to the new PostgreSQL database
    pg_engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
    PGSession = sessionmaker(bind=pg_engine)
    dest_session = PGSession()

    # 3. Create all tables in PostgreSQL using the metadata from models.py
    db.metadata.create_all(pg_engine)
    print("✅ Tables created in PostgreSQL.")

    # 4. Fetch data from SQLite
    suppliers = source_session.query(Supplier).all()
    medicines = source_session.query(Medicine).all()
    batches = source_session.query(Batch).all()
    sales = source_session.query(Sale).all()
    sale_items = source_session.query(SaleItem).all()
    users = source_session.query(User).all()
    print("Data fetched from SQLite.")

    # 5. Insert into PostgreSQL in the correct order
    for s in suppliers:
        dest_session.add(Supplier(id=s.id, name=s.name, contact=s.contact, lead_time_days=s.lead_time_days))
    
    for u in users:
        dest_session.add(User(id=u.id, full_name=u.full_name, username=u.username, password_hash=u.password_hash, role=u.role, is_active=u.is_active))
        
    for m in medicines:
        dest_session.add(Medicine(id=m.id, name=m.name, category=m.category, unit=m.unit, cost_price=m.cost_price, selling_price=m.selling_price, reorder_level=m.reorder_level, supplier_id=m.supplier_id))
        
    for b in batches:
        dest_session.add(Batch(id=b.id, medicine_id=b.medicine_id, batch_no=b.batch_no, quantity=b.quantity, expiry_date=b.expiry_date, received_date=b.received_date, cost_price=b.cost_price))
        
    for sale in sales:
        dest_session.add(Sale(id=sale.id, date=sale.date, total_amount=sale.total_amount, profit=sale.profit, payment_method=sale.payment_method))
        
    for item in sale_items:
        dest_session.add(SaleItem(id=item.id, sale_id=item.sale_id, medicine_id=item.medicine_id, batch_id=item.batch_id, qty=item.qty, unit_price=item.unit_price, cost_price=item.cost_price))

    # 6. Save everything
    dest_session.commit()
    print("✅ Migration complete! All data transferred to PostgreSQL.")

if __name__ == "__main__":
    migrate()