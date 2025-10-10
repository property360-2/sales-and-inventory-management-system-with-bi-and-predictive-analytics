# 🧩 SariSariStock: Sales & Inventory Management System

A complete **Sales, Inventory, Business Intelligence (BI), and Forecasting System** for small retail stores — built using **Django + Python**.

---

## 📘 Overview

**Project Name:** SariSariStock  
**Purpose:** Simplify and automate sales, inventory, and reporting for a sari-sari store.  
**Tech Stack:** Django (Python), Tailwind/Bootstrap, Chart.js, Pandas, Scikit-learn, ReportLab  
**Users:**  
- **Admin / Owner (Tita)** — full access, BI dashboard, forecasting, reports  
- **Staff / Cashier** — POS, receipts, daily sales view

---

## ⚙️ System Functions

### 1. 🔐 Authentication & User Management
**Functions**
- User login/logout (Django Auth)
- Role-based access (Admin, Staff)
- CRUD for user accounts (Admin only)
- Password change/reset
- Optional profile info and avatar

**Model**
- `User`
  - username, password, role [admin, staff], contact_info

---

### 2. 📦 Product & Inventory Management
**Functions**
- CRUD: Add, edit, delete products
- Group products by category
- Manage supplier info (optional)
- Track stock quantity
- Update stock (restock, adjustment)
- Auto low-stock alerts
- Search by name or barcode
- Import/export product list (CSV/Excel)

**Models**
- `Category`
- `Product`
  - name, category (FK), barcode, price, cost_price, unit, stock_qty, reorder_level
- `Supplier` *(optional)*
- `StockTransaction`
  - product, quantity_change, remarks (“restock”, “adjustment”), date

---

### 3. 💰 Point of Sale (POS) / Sales Management
**Functions**
- POS kiosk interface (clean, fast)
- Product search (by name/barcode)
- Add to cart, edit quantity, remove
- Auto-compute totals, tax, change
- Generate and print receipts (PDF)
- Save sales to database
- Auto-update stock after sale
- Staff can view daily sales summary
- Admin can filter by cashier/date

**Models**
- `Sale`
  - cashier (FK → User), total_amount, payment_type, date_time
- `SaleItem`
  - sale (FK), product (FK), quantity, price, subtotal

---

### 4. 📊 Dashboard & Business Intelligence (BI)
**Functions**
- Admin dashboard with charts and KPIs:
  - Total Sales (today, week, month)
  - Profit summary
  - Top 5 best-selling products
  - Low-stock alerts
  - Category performance
  - Sales by cashier
  - Sales trends (daily/monthly)
- Filter by date range
- Auto-refresh using HTMX or AJAX

**Tools**
- Django ORM for aggregation
- Pandas for analysis
- Chart.js or Plotly for visualization

---

### 5. 🧮 Forecasting & Analytics
**Functions**
- Forecast next 7 / 30 days of sales
- Predict top-selling products
- Suggest restocks based on demand trends
- Display forecast charts (actual vs. predicted)
- Export forecast summary (PDF/Excel)

**Libraries**
- Pandas (data prep)
- Scikit-learn (Linear Regression / ARIMA)
- Chart.js or Matplotlib (charts)

**Model**
- `ForecastResult`
  - date_generated, period (7/30 days), predicted_sales, method_used

---

### 6. 📑 Reports & Exports
**Functions**
- Generate reports in PDF/Excel:
  - Daily / Weekly / Monthly Sales
  - Inventory Summary
  - Low-stock Products
  - Staff Sales Summary
  - Profit/Loss Report
- Filter by date or user
- Auto-format with store info and totals
- Downloadable and printable

**Libraries**
- `ReportLab` — PDF
- `openpyxl` / `xlsxwriter` — Excel

---

### 7. 🔔 Alerts & Notifications
**Functions**
- Low-stock alerts (dashboard)
- Success/error flash messages
- Optional email alert to admin for out-of-stock
- “Sales Target Achieved” notification (optional fun metric)

---

### 8. ⚙️ Settings & Configuration
**Functions**
- Store info setup (name, logo, address)
- Tax rate configuration
- Receipt footer text
- Currency and format options
- Toggle features (forecasting, supplier tracking)
- Database backup/download (SQLite/Postgres)

**Model**
- `SystemSettings`

---

### 9. 🧾 Receipt Generation & Printing
**Functions**
- Auto-generate printable receipt per sale
- Include store name, date/time, cashier, items, totals, change
- Compact format for 58mm/80mm printers
- Downloadable PDF receipts

**Library**
- ReportLab (PDF generation)

---

### 10. 🔍 Search & Filtering
**Functions**
- Global search for products, sales, users
- Advanced filters (date, category, cashier, supplier)
- Pagination and sorting (Django + HTMX)

---

### 11. 🖥️ User Interface / Experience Design
**Goals**
- Fast, clean, responsive (usable on tablet/phone)
- Consistent layout (dashboard, sidebar, modals)
- Accessible design (clear buttons, icons, contrast)
- Tailwind CSS or Bootstrap 5
- Heroicons / FontAwesome icons

**Page Layouts**
- `/dashboard/`
- `/pos/`
- `/inventory/`
- `/reports/`
- `/forecast/`
- `/users/`
- `/settings/`

---

### 12. 🧰 Utilities & Backend Services
**Functions**
- Reusable utilities:
  - Inventory stock update
  - Sales summaries
  - Report generation
  - Forecast computations
- Optional background jobs (Celery) for heavy tasks
- API endpoints for charts and data

---

## 🗄️ Database Schema Overview

```text
User
 ├── username
 ├── role [admin, staff]
 └── contact_info

Category
 └── name

Product
 ├── name
 ├── category (FK)
 ├── barcode
 ├── price
 ├── cost_price
 ├── unit
 ├── stock_qty
 ├── reorder_level
 └── date_added

Supplier (optional)
 ├── name
 ├── contact
 └── address

StockTransaction
 ├── product (FK)
 ├── quantity_change (+/-)
 ├── remarks
 └── date

Sale
 ├── cashier (FK → User)
 ├── total_amount
 ├── payment_type
 └── date_time

SaleItem
 ├── sale (FK)
 ├── product (FK)
 ├── quantity
 ├── price
 └── subtotal

ForecastResult
 ├── date_generated
 ├── period (7/30 days)
 ├── predicted_sales
 └── method_used

SystemSettings
 ├── store_name
 ├── logo
 ├── tax_rate
 ├── receipt_footer
 └── backup_path
````

---

## 🧭 Summary of Key Functional Areas

| Module             | Description                                     |
| ------------------ | ----------------------------------------------- |
| **Authentication** | User login/logout, roles                        |
| **Inventory**      | Product CRUD, categories, stock updates, alerts |
| **POS**            | Sales, receipts, auto stock deduction           |
| **Dashboard (BI)** | Charts, KPIs, sales/profit tracking             |
| **Forecasting**    | Predict sales/demand using past data            |
| **Reports**        | Export PDF/Excel for all key modules            |
| **Settings**       | Store configuration and backups                 |
| **UI/UX**          | Tailwind/Bootstrap, responsive, mobile-ready    |

---

## ✅ Final Outcome

A **modern, full-featured Django system** with:

* Smooth POS workflow
* Accurate stock tracking
* Clean analytics dashboard
* Smart forecasting
* PDF & Excel reporting
* Tita-friendly interface (simple yet powerful)

This plan serves as the **complete specification** and **AI-readable base document** for development, generation, and system design.
