import os
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import func

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-only-change-this-secret-key")
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

db_url = os.environ.get("DATABASE_URL") or "sqlite:///stockflow.db"
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql+psycopg://", 1)
elif db_url.startswith("postgresql://"):
    db_url = db_url.replace("postgresql://", "postgresql+psycopg://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = db_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)


class Organization(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    default_threshold = db.Column(db.Integer, nullable=False, default=5)
    user = db.relationship("User", backref="organization", uselist=False)
    products = db.relationship("Product", backref="organization", cascade="all, delete-orphan")


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    organization_id = db.Column(db.Integer, db.ForeignKey("organization.id"), nullable=False, unique=True)


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey("organization.id"), nullable=False, index=True)
    name = db.Column(db.String(160), nullable=False)
    sku = db.Column(db.String(80), nullable=False)
    description = db.Column(db.Text, nullable=True)
    quantity = db.Column(db.Integer, nullable=False, default=0)
    cost_price = db.Column(db.Float, nullable=True)
    selling_price = db.Column(db.Float, nullable=True)
    low_stock_threshold = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime, server_default=func.now(), nullable=False)
    updated_at = db.Column(db.DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    __table_args__ = (db.UniqueConstraint("organization_id", "sku", name="uq_org_sku"),)

    @property
    def threshold(self):
        return self.low_stock_threshold if self.low_stock_threshold is not None else self.organization.default_threshold

    @property
    def is_low_stock(self):
        return self.quantity <= self.threshold


def current_user():
    uid = session.get("user_id")
    return db.session.get(User, uid) if uid else None

@app.context_processor
def inject_current_user():
    return {"current_user": current_user}



def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not current_user():
            return redirect(url_for("login"))
        return fn(*args, **kwargs)
    return wrapper


def org_products():
    user = current_user()
    return Product.query.filter_by(organization_id=user.organization_id)


@app.route("/healthz")
def healthz():
    return jsonify(status="ok"), 200


@app.route("/healthz/db")
def database_healthz():
    """Read-only database connectivity check; never returns credentials or data."""
    dialect = db.engine.dialect.name
    try:
        db.session.execute(db.text("SELECT 1"))
        return jsonify(status="ok", database=dialect, connection="ok"), 200
    except Exception:
        db.session.rollback()
        app.logger.warning("Database connectivity check failed")
        return jsonify(status="error", database=dialect, connection="failed"), 503


@app.route("/")
def index():
    return redirect(url_for("dashboard") if current_user() else url_for("login"))


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if current_user():
        return redirect(url_for("dashboard"))
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")
        org_name = request.form.get("organization", "").strip()
        if not email or "@" not in email or len(password) < 8 or not org_name:
            flash("Enter a valid email, organization, and password with at least 8 characters.", "error")
        elif password != confirm:
            flash("Passwords do not match.", "error")
        elif User.query.filter_by(email=email).first():
            flash("An account with that email already exists.", "error")
        else:
            org = Organization(name=org_name, default_threshold=5)
            db.session.add(org)
            db.session.flush()
            user = User(email=email, password_hash=generate_password_hash(password), organization_id=org.id)
            db.session.add(user)
            db.session.commit()
            session["user_id"] = user.id
            flash("Your StockFlow workspace is ready.", "success")
            return redirect(url_for("dashboard"))
    return render_template("auth.html", mode="signup")


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user():
        return redirect(url_for("dashboard"))
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password_hash, request.form.get("password", "")):
            session.clear()
            session["user_id"] = user.id
            return redirect(url_for("dashboard"))
        flash("Email or password is incorrect.", "error")
    return render_template("auth.html", mode="login")


@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/dashboard")
@login_required
def dashboard():
    products = org_products().order_by(Product.updated_at.desc()).all()
    total_units = sum(p.quantity for p in products)
    low_stock = [p for p in products if p.is_low_stock]
    inventory_value = sum((p.cost_price or 0) * p.quantity for p in products)
    return render_template(
        "dashboard.html",
        products=products,
        total_units=total_units,
        low_stock=low_stock,
        inventory_value=inventory_value,
    )


@app.route("/products")
@login_required
def products():
    q = request.args.get("q", "").strip()
    query = org_products()
    if q:
        query = query.filter(db.or_(Product.name.ilike(f"%{q}%"), Product.sku.ilike(f"%{q}%")))
    items = query.order_by(Product.updated_at.desc()).all()
    return render_template("products.html", products=items, q=q)


def parse_product_form(product=None):
    name = request.form.get("name", "").strip()
    sku = request.form.get("sku", "").strip().upper()
    if not name or not sku:
        raise ValueError("Product name and SKU are required.")
    try:
        quantity = int(request.form.get("quantity", "0"))
        threshold_raw = request.form.get("low_stock_threshold", "").strip()
        threshold = int(threshold_raw) if threshold_raw else None
        cost_raw = request.form.get("cost_price", "").strip()
        selling_raw = request.form.get("selling_price", "").strip()
        cost = float(cost_raw) if cost_raw else None
        selling = float(selling_raw) if selling_raw else None
        if quantity < 0 or (threshold is not None and threshold < 0) or (cost is not None and cost < 0) or (selling is not None and selling < 0):
            raise ValueError()
    except (ValueError, TypeError):
        raise ValueError("Quantity, threshold, and prices must be valid non-negative numbers.")
    user = current_user()
    duplicate = Product.query.filter_by(organization_id=user.organization_id, sku=sku)
    if product:
        duplicate = duplicate.filter(Product.id != product.id)
    if duplicate.first():
        raise ValueError("That SKU already exists in your organization.")
    return {
        "name": name,
        "sku": sku,
        "description": request.form.get("description", "").strip() or None,
        "quantity": quantity,
        "low_stock_threshold": threshold,
        "cost_price": cost,
        "selling_price": selling,
    }


@app.route("/products/new", methods=["GET", "POST"])
@login_required
def create_product():
    if request.method == "POST":
        try:
            product = Product(organization_id=current_user().organization_id, **parse_product_form())
            db.session.add(product)
            db.session.commit()
            flash("Product added to inventory.", "success")
            return redirect(url_for("products"))
        except ValueError as exc:
            db.session.rollback()
            flash(str(exc), "error")
    return render_template("product_form.html", product=None)


@app.route("/products/<int:product_id>/edit", methods=["GET", "POST"])
@login_required
def edit_product(product_id):
    product = org_products().filter_by(id=product_id).first_or_404()
    if request.method == "POST":
        try:
            for key, value in parse_product_form(product).items():
                setattr(product, key, value)
            db.session.commit()
            flash("Product updated.", "success")
            return redirect(url_for("products"))
        except ValueError as exc:
            db.session.rollback()
            flash(str(exc), "error")
    return render_template("product_form.html", product=product)


@app.route("/products/<int:product_id>/delete", methods=["POST"])
@login_required
def delete_product(product_id):
    product = org_products().filter_by(id=product_id).first_or_404()
    db.session.delete(product)
    db.session.commit()
    flash("Product deleted.", "success")
    return redirect(url_for("products"))


@app.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    org = current_user().organization
    if request.method == "POST":
        try:
            threshold = int(request.form.get("default_threshold", "5"))
            if threshold < 0:
                raise ValueError()
            org.default_threshold = threshold
            db.session.commit()
            flash("Settings saved.", "success")
            return redirect(url_for("settings"))
        except ValueError:
            flash("Threshold must be a non-negative whole number.", "error")
    return render_template("settings.html", organization=org)


@app.errorhandler(404)
def not_found(_):
    return render_template("404.html"), 404


with app.app_context():
    db.create_all()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)
