```markdown
# 🍕 Pizza Stock Management & On-Site Ordering System (Pure Django)

## 🧩 Overview
A full-featured Django web application for a **multi-branch pizza shop** with centralized inventory, forecasting, BI, and on-site ordering via QR code.

**Key Features**
- Multi-branch inventory management  
- Sales tracking and forecasting  
- Business Intelligence (BI) dashboards  
- QR-based on-site ordering system  
- Demo online payments (GCash/PayMaya)  
- Staff & admin roles for control and analytics  

Everything is **pure Django** — no React, no external frontend frameworks.

---

## 🧱 Tech Stack

| Layer | Tool |
|-------|------|
| Web Framework | Django 5.x |
| Templates/UI | Django Templates + TailwindCSS + HTMX (optional) |
| Database | PostgreSQL |
| Background Jobs | `django-crontab` or Celery |
| Charts | Chart.js |
| Payments | Demo GCash / PayMaya simulation |
| QR Codes | `qrcode` Python library |

---

## 🗂️ Project Structure

```

pizza_stock/
├── config/               # Settings, URLs, WSGI, ASGI
├── users/                # Custom user model, roles, branch mapping
├── inventory/            # SKU, stock, transactions
├── sales/                # Sales records
├── orders/               # On-site ordering + payments
├── forecast/             # Demand prediction
├── reports/              # Dashboards and BI
├── templates/            # HTML templates
├── static/               # Tailwind, Chart.js, QR images
└── manage.py

````

---

## ⚙️ Core Django Apps and Functions

### 1. `users` — Authentication & Roles
**Functions**
- Custom `User` model linked to one or more `Branch`
- Role groups: `Admin`, `Manager`, `Staff`
- Middleware for branch context
- Permissions restrict access by branch

---

### 2. `inventory` — SKU & Stock Management
**Functions**
- CRUD for pizza SKUs (name, price, category)
- Maintain per-branch stock via `InventoryRecord`
- Log all movements in `StockTransaction`

```python
def apply_stock_transaction(branch, sku, qty, txn_type, user):
    """Atomic stock update + create StockTransaction record."""
````

Transaction types: `restock`, `sale`, `transfer`, `waste`

Auto low-stock detection: `if qty < safety_stock`

---

### 3. `sales` — Sales Tracking

**Functions**

* `record_sale(branch, sku, qty, price, user)`

  * Creates a `Sale` record and deducts inventory
* Aggregate daily sales → used by forecast + reports
* Connects with `orders` app for customer orders

---

### 4. `orders` — On-Site Ordering System

Handles **customer-facing** QR orders and **staff dashboards**.

**Core Models**

```python
class Order(models.Model):
    STATUS = [
        ('pending', 'Pending Payment'),
        ('paid', 'Paid'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    PAYMENT = [
        ('counter', 'Pay at Counter'),
        ('online', 'Online Payment'),
    ]
    branch = models.ForeignKey('inventory.Branch', on_delete=models.CASCADE)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT)
    status = models.CharField(max_length=20, choices=STATUS, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    paid_at = models.DateTimeField(null=True, blank=True)
```

```python
class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    sku = models.ForeignKey('inventory.SKU', on_delete=models.CASCADE)
    qty = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=8, decimal_places=2)
```

**Public URLs**

* `/order/<branch_code>/` → display active menu
* `/order/cart/` → session-based cart
* `/order/checkout/` → choose payment (counter/online)
* `/order/confirm/` → finalize order

**Staff URLs**

* `/orders/dashboard/` → all branch orders
* `/orders/<id>/update/` → mark as paid/completed

**Flow**

1. Customer scans QR (→ `/order/<branch_code>/`)
2. Selects items, proceeds to checkout
3. Chooses payment type:

   * **Counter** → order saved as `pending`
   * **Online** → simulate payment gateway → auto-marks `paid`
4. When marked `paid`:

   ```python
   apply_stock_transaction(branch, sku, qty, 'sale', user=None)
   ```
5. Staff marks order `completed` → finalizes sale

---

### 5. `payments` (within `orders`) — Demo Online Payment

Simulated flow for GCash/PayMaya.

**Functions**

```python
def initiate_payment(order):
    """Creates fake payment reference and redirects to demo page."""
```

```python
def payment_webhook(request):
    """Simulated callback marking order as paid."""
```

Routes:

* `/payment/initiate/`
* `/payment/success/`
* `/payment/fail/`

> ⚠️ This is a **demonstration** integration — no actual payment API calls.

---

### 6. `forecast` — Demand Prediction

**Functions**

* Aggregate last 7-day sales per SKU per branch
* Simple moving average forecast:

```python
def moving_average_forecast(series, window=7):
    return series.rolling(window).mean().iloc[-1]
```

* Save results to `Forecast` model
* Run via cron (`python manage.py run_forecast`)

---

### 7. `reports` — BI Dashboards

**Functions**

* Generate analytics:

  * Sales per day/branch
  * Top SKUs
  * Stock turnover
  * Forecast vs Actual
* Render via Chart.js charts in Django templates

Example:

```html
<canvas id="salesChart"></canvas>
<script>
const ctx = document.getElementById('salesChart');
new Chart(ctx, {type:'bar', data:{labels:..., datasets:...}});
</script>
```

---

## 🖼️ QR Code Generation

Each branch generates its own QR code pointing to `/order/<branch_code>/`.

```python
import qrcode

def generate_branch_qr(branch):
    url = f"https://pizzashop.com/order/{branch.code}/"
    img = qrcode.make(url)
    img.save(f"static/qr/{branch.code}.png")
```

Show QR codes on tables or posters for customers.

---

## 🔔 Notifications

**Functions**

* `send_low_stock_alerts()` → email to branch manager
* `notify_new_order()` → staff dashboard refresh via HTMX polling
* Optional Telegram/email integration for alerts

---

## 🔁 Background Jobs

All automated jobs scheduled using `django-crontab`.

| Job                          | Description               |
| ---------------------------- | ------------------------- |
| `aggregate_sales_daily()`    | Summarize daily sales     |
| `run_forecast()`             | Update forecasts          |
| `auto_close_unpaid_orders()` | Cancel old pending orders |
| `send_low_stock_alerts()`    | Alert for low inventory   |

```bash
python manage.py crontab add
python manage.py crontab show
```

---

## 📈 Inter-App Integrations

| From       | To          | Trigger                     |
| ---------- | ----------- | --------------------------- |
| `orders`   | `sales`     | On paid order → create Sale |
| `sales`    | `inventory` | Deduct SKU stock            |
| `sales`    | `forecast`  | Feed daily sales data       |
| `forecast` | `reports`   | BI visualization            |

---

## 🔒 Security

* Django `Groups` and `Permissions` control access
* Branch-level filters per user
* CSRF + HTTPS enforced
* Payment webhook signature check (demo)
* All stock changes logged in `StockTransaction`

---

## 🧪 Testing

| Area        | Test Type                            |
| ----------- | ------------------------------------ |
| Inventory   | CRUD + atomic stock updates          |
| Orders      | Cart → Checkout → Payment simulation |
| Forecast    | Calculation accuracy                 |
| BI          | Chart data correctness               |
| Permissions | Role & branch restrictions           |

---

## 🚀 Deployment

**Functions**

* Gunicorn + Nginx deployment
* PostgreSQL database
* `collectstatic` for CSS/JS
* Cron jobs for daily tasks
* Regular DB backups (`pg_dump`)

---

## 🧱 Directory Scaffold

```
inventory/
    models.py
    views.py
    admin.py
    utils.py
sales/
    models.py
    views.py
    services.py
orders/
    models.py
    views.py
    payments.py
    urls.py
forecast/
    models.py
    tasks.py
    management/commands/run_forecast.py
reports/
    views.py
    templates/reports/
users/
    models.py
    views.py
    middleware.py
config/
    settings.py
    urls.py
    wsgi.py
    asgi.py
```

---

## ✅ Core Functions Summary

| Function                     | Responsibility                  |
| ---------------------------- | ------------------------------- |
| `apply_stock_transaction()`  | Atomic inventory update         |
| `record_sale()`              | Create sale + adjust stock      |
| `create_order()`             | Save new order + items          |
| `mark_order_paid()`          | Update status + stock deduction |
| `generate_branch_qr()`       | Generate branch QR code         |
| `initiate_payment()`         | Start demo payment flow         |
| `payment_webhook()`          | Simulate payment callback       |
| `moving_average_forecast()`  | Forecast demand                 |
| `aggregate_sales_daily()`    | Summarize for BI/forecast       |
| `send_low_stock_alerts()`    | Notify managers                 |
| `auto_close_unpaid_orders()` | Cancel stale orders             |

---

## 🧠 Notes

* 100% **Pure Django** (no React, no API frontend)
* On-site ordering works with QR scan or manual link
* Online payment is simulated only (GCash/PayMaya demo)
* Fully extendable to real payment APIs later
* Can run standalone or scaled to multi-branch operations
