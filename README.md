# 💊 Pharmacy Intelligence System

A decision-support dashboard for independent pharmacies. Instead of just
recording sales, it analyses them — predicting stock-outs, quantifying
expiry risk, and surfacing which products actually make money.

**Stack:** Flask · SQLite · SQLAlchemy · Pandas · Chart.js

---

## 🎯 The Problem

Small pharmacies lose money in three silent ways:

1. **Stock-outs** — fast movers run out while slow movers fill the shelves
2. **Expiry write-offs** — batches quietly expire before they sell
3. **Blind purchasing** — restocking by gut feel, not by data

Traditional "pharmacy management systems" only record transactions.
They don't help the owner decide anything.

---

## 💡 What This Does Differently

| Feature | Decision it enables |
|---------|---------------------|
| **Stock-out forecast** | "Paracetamol runs out in 5 days — reorder 120 units" |
| **Expiry risk report** | "18 batches expire in 60 days — $1,860 at risk" |
| **Fast/slow movers** | "Stop reordering these 5 products — they haven't sold in 90 days" |
| **Profit ranking** | "Vitamin C is your #1 profit driver this month — protect its stock" |
| **Sales trend chart** | Spot demand shifts before they become losses |
| **Live POS** | Sales feed analytics in real time |

---

## 🖥️ Screenshots

*(Add your own screenshots here — dashboard, POS, alerts)*

| Dashboard | New Sale |
|-----------|----------|
| `docs/dashboard.png` | `docs/pos.png` |

---

## 🏗️ Architecture

```
Data Layer          Intelligence Layer        Decision Layer
─────────────       ────────────────────      ──────────────────
medicines           stock_out_forecast()      🔴 Stock alerts
batches             expiry_risk()             🟠 Expiry warnings
sales / sale_items  fast_slow_movers()        🏆 Top products
suppliers           profit_report()           📊 Trend charts
                    reorder_suggestions()     🧾 POS screen
```

---

## 🔬 Key Analytics

**Stock-out prediction** — velocity-based:

```
avg_daily_sales = qty_sold_last_30d / 30
days_of_cover   = current_stock / avg_daily_sales
```

Flags any item with ≤14 days of cover and computes a reorder quantity
that accounts for supplier lead time + 7-day safety buffer.

**Expiry risk** — batch-level, valued in dollars:

```
value_at_risk = quantity × cost_price
```

Sorted by dollar impact, not by date — a $500 batch expiring beats a $5 one.

**Fast/slow movers** — 30-day velocity vs. 90-day dead-stock scan.

**Profit estimation** — calculated per sale line using stored cost basis:

```
line_profit = qty × (unit_price - cost_price)
```

---

## 🚀 Setup

```bash
# Clone
git clone <your-repo-url>
cd pharmacy-intel

# Virtual environment
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Mac/Linux

# Install
python -m pip install -r requirements.txt

# Load 90 days of demo data
python seed.py

# Run
python app.py
```

Open http://127.0.0.1:5000

---

## 📁 Project Structure

```
pharmacy-intel/
├── app.py              # Flask routes (dashboard, POS, medicines)
├── models.py           # SQLAlchemy models
├── analytics.py        # Intelligence layer
├── seed.py             # Demo data generator
├── templates/
│   ├── base.html
│   ├── dashboard.html  # KPIs + charts + alerts
│   ├── new_sale.html   # POS screen
│   └── medicines.html
├── static/style.css
└── requirements.txt
```

---

## 🗺️ Roadmap

- [x] Core data model (medicines, batches, sales, suppliers)
- [x] Stock-out forecasting
- [x] Expiry risk valuation
- [x] Fast/slow movers
- [x] Profit-ranked top products
- [x] Dashboard with Chart.js visualizations
- [x] Live POS screen with batch-level stock deduction
- [ ] CSV/Excel export of reports
- [ ] Sale detail view
- [ ] Supplier lead-time analytics
- [ ] Email/SMS low-stock alerts
- [ ] Role-based access (owner vs. cashier)

---

## 🧠 What Makes It "Intelligent"

Most pharmacy tools answer *what happened*.
This one answers *what to do next*:

- It doesn't just show stock — it predicts **when it will run out**
- It doesn't just list batches — it ranks them **by financial exposure**
- It doesn't just count sales — it identifies **which products are worth pushing**

That's the difference between a records system and a **business intelligence system**.

---

## 📜 License

MIT — free to use, modify, and learn from.