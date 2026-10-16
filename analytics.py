from datetime import date, timedelta
from sqlalchemy import func


def build_dashboard_data(db):
    from models import Medicine, Batch, Sale, SaleItem

    today = date.today()
    last_30 = today - timedelta(days=30)
    last_90 = today - timedelta(days=90)

    # ---------- KPI: total stock value ----------
    stock_value = db.session.query(
        func.sum(Batch.quantity * Batch.cost_price)
    ).filter(Batch.expiry_date > today).scalar() or 0

    # ---------- KPI: sales this month ----------
    month_start = today.replace(day=1)
    month_sales = db.session.query(
        func.sum(Sale.total_amount), func.sum(Sale.profit)
    ).filter(Sale.date >= month_start).first()
    month_revenue = month_sales[0] or 0
    month_profit = month_sales[1] or 0

    # ---------- KPI: today's sales ----------
    today_sales = db.session.query(
        func.sum(Sale.total_amount)
    ).filter(Sale.date == today).scalar() or 0

    # ---------- STOCK-OUT FORECAST ----------
    stock_alerts = []
    for med in Medicine.query.all():
        sold_30 = db.session.query(
            func.sum(SaleItem.qty)
        ).join(Sale).filter(
            SaleItem.medicine_id == med.id,
            Sale.date >= last_30
        ).scalar() or 0

        current_stock = db.session.query(
            func.sum(Batch.quantity)
        ).filter(
            Batch.medicine_id == med.id,
            Batch.expiry_date > today
        ).scalar() or 0

        if sold_30 == 0 or current_stock == 0:
            continue

        avg_daily = sold_30 / 30
        days_left = current_stock / avg_daily

        if days_left <= 14:
            stock_alerts.append({
                "medicine": med.name,
                "days_left": round(days_left, 1),
                "current_stock": current_stock,
                "avg_daily": round(avg_daily, 1),
                "status": "critical" if days_left <= 5 else "warning",
                "reorder_qty": max(
                    0,
                    int(avg_daily * ((med.supplier.lead_time_days if med.supplier else 3) + 7)
                        - current_stock)
                ),
            })

    stock_alerts.sort(key=lambda x: x["days_left"])

    # ---------- EXPIRY RISK ----------
    horizon = today + timedelta(days=60)
    expiring = db.session.query(Batch).filter(
        Batch.expiry_date <= horizon,
        Batch.expiry_date > today,
        Batch.quantity > 0,
    ).all()

    expiry_alerts = [{
        "medicine": b.medicine.name,
        "batch_no": b.batch_no,
        "quantity": b.quantity,
        "expiry_date": b.expiry_date,
        "days_to_expiry": (b.expiry_date - today).days,
        "value_at_risk": round(b.quantity * b.cost_price, 2),
    } for b in expiring]
    expiry_alerts.sort(key=lambda x: x["value_at_risk"], reverse=True)
    expiry_value = sum(e["value_at_risk"] for e in expiry_alerts)

    # ---------- FAST / SLOW MOVERS ----------
    velocities = []
    for med in Medicine.query.all():
        sold_30 = db.session.query(
            func.sum(SaleItem.qty)
        ).join(Sale).filter(
            SaleItem.medicine_id == med.id,
            Sale.date >= last_30
        ).scalar() or 0

        sold_90 = db.session.query(
            func.sum(SaleItem.qty)
        ).join(Sale).filter(
            SaleItem.medicine_id == med.id,
            Sale.date >= last_90
        ).scalar() or 0

        velocities.append({
            "medicine": med.name,
            "category": med.category,
            "sold_30": sold_30,
            "sold_90": sold_90,
        })

    velocities.sort(key=lambda x: x["sold_30"], reverse=True)
    fast_movers = velocities[:5]
    slow_movers = [v for v in velocities if v["sold_90"] == 0][:5]

    # ---------- TOP PRODUCTS BY PROFIT (this month) ----------
    top = db.session.query(
        Medicine.name,
        func.sum(SaleItem.qty * (SaleItem.unit_price - SaleItem.cost_price)).label("profit"),
        func.sum(SaleItem.qty * SaleItem.unit_price).label("revenue"),
    ).join(SaleItem).join(Sale).filter(
        Sale.date >= month_start
    ).group_by(Medicine.name).order_by(
        func.sum(SaleItem.qty * (SaleItem.unit_price - SaleItem.cost_price)).desc()
    ).limit(5).all()

    top_products = [{
        "name": t[0],
        "profit": round(t[1] or 0, 2),
        "revenue": round(t[2] or 0, 2),
    } for t in top]

    # ---------- Daily sales trend (last 30 days) ----------
    trend_rows = db.session.query(
        Sale.date,
        func.sum(Sale.total_amount)
    ).filter(Sale.date >= last_30).group_by(Sale.date).order_by(Sale.date).all()

    trend = [{"date": str(r[0]), "amount": round(r[1] or 0, 2)} for r in trend_rows]

    return {
        "today": today,
        "stock_value": round(stock_value, 2),
        "month_revenue": round(month_revenue, 2),
        "month_profit": round(month_profit, 2),
        "today_sales": round(today_sales, 2),
        "stock_alerts": stock_alerts[:8],
        "stock_alert_count": len(stock_alerts),
        "expiry_alerts": expiry_alerts[:8],
        "expiry_alert_count": len(expiry_alerts),
        "expiry_value": round(expiry_value, 2),
        "fast_movers": fast_movers,
        "slow_movers": slow_movers,
        "top_products": top_products,
        "trend": trend,
        "total_medicines": Medicine.query.count(),
        "total_batches": Batch.query.count(),
        "total_sales": Sale.query.count(),
    }