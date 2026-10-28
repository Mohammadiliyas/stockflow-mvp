# StockFlow MVP

Inventory management SaaS MVP built with Flask, SQLAlchemy, and PostgreSQL-ready configuration.

This repository hosts the StockFlow hiring assignment implementation. See `render.yaml` for Render deployment configuration.

## Features
- Organization-scoped accounts and data
- Product CRUD with SKU uniqueness per organization
- Stock quantity, cost, selling price, and low-stock threshold
- Dashboard totals and low-stock alerts
- Organization settings for default low-stock threshold

## Local development
```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
flask --app app run --debug
```

## Deployment
Configured for Render using `render.yaml`. Connect this repository in Render and apply the Blueprint. Set required secrets only in Render's environment settings; never commit secrets.