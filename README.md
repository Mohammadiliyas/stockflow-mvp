# StockFlow MVP

Inventory management SaaS MVP built with Flask, SQLAlchemy, and a responsive HTML/CSS interface.

**Live demo:** https://stockflow-mvp-4vao.onrender.com  
**Health endpoint:** https://stockflow-mvp-4vao.onrender.com/healthz

## Features
- Email/password signup and login with Werkzeug password hashing
- An organization/workspace created at signup; every product query and mutation is scoped to the signed-in user's organization
- Product create, read, update, and delete
- Organization-unique SKU validation
- Quantity, cost and selling price, optional product-specific low-stock threshold, and description
- Dashboard with product count, total units, stock cost value, recent products, and low-stock alerts
- Configurable workspace default low-stock threshold
- Search by product name or SKU, server-side validation, delete confirmation, and responsive layout
- SQLite fallback for local development; PostgreSQL is supported through `DATABASE_URL`

## Local development
Python 3.10+ recommended.

```bash
python -m venv .venv
# Windows PowerShell: .venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Open http://127.0.0.1:5000 and create an account. The SQLite database is created automatically.

## Deployment and storage
The included `render.yaml` Blueprint defines a web service and PostgreSQL database, and wires the database connection into `DATABASE_URL`. Apply the Blueprint from Render to use PostgreSQL-backed storage.

The currently running web service was created directly, outside the Blueprint flow. It therefore uses the SQLite fallback until its `DATABASE_URL` is connected to the Render PostgreSQL instance. **SQLite data on a free hosted instance may be lost after a restart or redeploy; do not use this direct instance for durable data until PostgreSQL is connected.**

## Data model
- `Organization`: name and default low-stock threshold
- `User`: unique email, password hash, organization ID (one owner per organization in this MVP)
- `Product`: organization ID, name, SKU, description, quantity, prices, optional threshold, timestamps; unique constraint on `(organization_id, sku)`

## Scope notes
This intentionally reduced MVP does not include password reset, team invites, role management, stock movement history, purchase orders, billing, or external integrations, matching the assessment scope.
