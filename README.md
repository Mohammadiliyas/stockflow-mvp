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
The live demo is hosted on Render and has been verified to connect to PostgreSQL through the `DATABASE_URL` environment variable. Keep the database URL and `SECRET_KEY` configured in Render Environment settings; never commit their values to Git.

The app supports SQLite as a local-development fallback when `DATABASE_URL` is not set. On a hosted deployment, configure PostgreSQL explicitly and verify the live connection before relying on persistent data. The included `render.yaml` is a sample Blueprint; review its database name and service settings before applying it to an existing Render workspace to avoid creating duplicate resources.

## Data model
- `Organization`: name and default low-stock threshold
- `User`: unique email, password hash, organization ID (one owner per organization in this MVP)
- `Product`: organization ID, name, SKU, description, quantity, prices, optional threshold, timestamps; unique constraint on `(organization_id, sku)`

## Scope notes
This intentionally reduced MVP does not include password reset, team invites, role management, stock movement history, purchase orders, billing, or external integrations, matching the assessment scope.
