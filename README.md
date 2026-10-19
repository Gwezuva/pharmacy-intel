# 💊 PharmaIntel - Enterprise Pharmacy System

A secure, full-stack decision-support dashboard for modern pharmacies. Built to replace manual, error-prone inventory tracking with predictive analytics, intelligent stock management, and a world-class point-of-sale experience.

**Stack:** Python (Flask) · SQLite · SQLAlchemy · Tailwind CSS · Chart.js

---

## 🚀 Key Features

### 🧠 Business Intelligence Dashboard
- **Stock-Out Forecast:** Predicts when medicines will run out based on 30-day sales velocity.
- **Expiry Risk Analysis:** Flags batches expiring within 60 days and calculates the exact dollar value at risk.
- **Fast/Slow Movers:** Identifies dead stock tying up capital vs. high-demand products.
- **Live Charts:** Visualizes revenue trends and top-profit products.

### 🛒 Modern Point of Sale (POS)
- **Search & Cart:** Fast autocomplete search with a persistent side-cart.
- **Seamless Checkout:** Dedicated review page before confirming payment.
- **Thermal Printing:** Generates a clean receipt with print-optimized CSS for 80mm printers.
- **Auto-Deduction:** Intelligently deducts stock from the batch closest to expiring first (FEFO method).

### 📦 Inventory & Exports
- **Batch Management:** Restock items and track specific expiration dates.
- **CSV Exports:** Download expiry reports and full sales history for accounting.

### 🔐 Security
- Secure session-based login system to protect sensitive profit and inventory data.

---

## 📸 Screenshots

*(Add screenshots of the Login, Dashboard, and POS here)*

---

## 🛠️ Installation & Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/YOUR-USERNAME/pharmacy-intel.git
   cd pharmacy-intel