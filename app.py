from flask import Flask, render_template, g, session, redirect, url_for, request, flash
from dotenv import load_dotenv
import os
import sqlite3
import stripe
from flask import jsonify
import smtplib
from email.mime.text import MIMEText
from argon2 import PasswordHasher

# =========================
# LOAD ENV VARIABLES
# =========================
load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")
if not app.secret_key:
    raise ValueError("SECRET_KEY is not set in .env")

# Stripe keys
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")
STRIPE_PUBLIC_KEY = os.getenv("STRIPE_PUBLIC_KEY")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")
DOMAIN_URL = os.getenv("DOMAIN_URL")

if not STRIPE_SECRET_KEY:
    raise ValueError("STRIPE_SECRET_KEY missing in .env")
stripe.api_key = STRIPE_SECRET_KEY

# Email settings
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL")

# Admin credentials (hashed using Argon2)
ph = PasswordHasher()
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME")
ADMIN_PASSWORD_HASH = os.getenv("ADMIN_PASSWORD_HASH")  # store hashed password in .env

# =========================
# DATABASE CONFIG
# =========================
DATABASE = os.path.join(app.root_path, "products.db")

def get_db():
    db = getattr(g, "_database", None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, "_database", None)
    if db:
        db.close()

# =========================
# INIT DB
# =========================
def init_db():
    db = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row
    cursor = db.cursor()

    # Products table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        category TEXT NOT NULL,
        price REAL NOT NULL,
        color TEXT,
        size TEXT,
        image_path TEXT NOT NULL,
        description TEXT,
        popularity INTEGER DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Orders table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        stripe_session_id TEXT,
        customer_email TEXT,
        total_amount REAL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Order items table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS order_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id INTEGER,
        product_name TEXT,
        quantity INTEGER,
        price REAL,
        FOREIGN KEY(order_id) REFERENCES orders(id)
    )
    """)

    # Admin table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS admin (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password_hash TEXT
    )
    """)

    # Insert sample products if empty
    cursor.execute("SELECT COUNT(*) AS count FROM products")
    result = cursor.fetchone()
    if result['count'] == 0:
        sample_products = [
            ('Series II-Black Hoodie',"Men",128, 'Black', 'S,M,L', 'static/images/products/black-hood.png', 'Premium hoodie'),
            ('Series II-White Hoodie', 'Men', 128, 'White', 'M,L,XL', 'static/images/products/white-hood.png', 'Premium hoodie'),
            ('Series I Cap', 'Men', 48, 'White', 'M,L', 'static/images/products/hat.png', 'Premium cap'),
        ]
        cursor.executemany("""
        INSERT INTO products (name, category, price, color, size, image_path, description)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, sample_products)

    # Insert admin if empty
    cursor.execute("SELECT COUNT(*) AS count FROM admin")
    if cursor.fetchone()['count'] == 0:
        cursor.execute("INSERT INTO admin (username, password_hash) VALUES (?, ?)", 
                       (ADMIN_USERNAME, ADMIN_PASSWORD_HASH))

    db.commit()
    db.close()

# =========================
# HELPERS
# =========================
def get_product_by_id(product_id):
    db = get_db()
    cursor = db.execute("SELECT * FROM products WHERE id=?", (product_id,))
    return cursor.fetchone()

def save_order(session_data):
    db = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row
    cursor = db.cursor()

    stripe_session_id = session_data["id"]
    customer_email = session_data.get("customer_details", {}).get("email")
    total_amount = session_data["amount_total"] / 100
    shipping_info = session.get("shipping_info", {})

    full_address = f"""
Name: {shipping_info.get('full_name')}
Email: {shipping_info.get('email')}
Phone: {shipping_info.get('phone')}
Address Line 1: {shipping_info.get('line1')}
Address Line 2: {shipping_info.get('line2')}
City: {shipping_info.get('city')}
Postal Code: {shipping_info.get('postal_code')}
Country: {shipping_info.get('country')}
"""

    cursor.execute("""
        INSERT INTO orders (stripe_session_id, customer_email, total_amount)
        VALUES (?, ?, ?)
    """, (stripe_session_id, customer_email, total_amount))

    order_id = cursor.lastrowid

    line_items = stripe.checkout.Session.list_line_items(stripe_session_id)
    product_summary = ""
    for item in line_items.data:
        cursor.execute("""
            INSERT INTO order_items (order_id, product_name, quantity, price)
            VALUES (?, ?, ?, ?)
        """, (
            order_id,
            item.description,
            item.quantity,
            item.amount_total / 100
        ))
        product_summary += f"{item.description} x{item.quantity} - R{item.amount_total / 100}\n"

    session.pop('shipping_info', None)
    db.commit()
    db.close()

    send_confirmation_email(customer_email, total_amount, product_summary)
    send_admin_email(total_amount, product_summary, full_address)

def send_confirmation_email(customer_email, total_amount, products):
    msg = MIMEText(f"Thank you for your purchase.\n\nOrder Summary:\n{products}\nTotal Paid: R{total_amount}\n")
    msg["Subject"] = "Order Confirmation - LINEA SOLENNE"
    msg["From"] = EMAIL_USER
    msg["To"] = customer_email
    server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
    server.login(EMAIL_USER, EMAIL_PASS)
    server.sendmail(EMAIL_USER, customer_email, msg.as_string())
    server.quit()

def send_admin_email(total_amount, products, address):
    msg = MIMEText(f"NEW ORDER ALERT\n\nProducts:\n{products}\nTotal Paid: R{total_amount}\n\nShipping Details:\n{address}")
    msg["Subject"] = "🔥 NEW ORDER RECEIVED - LINEA SOLENNE"
    msg["From"] = EMAIL_USER
    msg["To"] = ADMIN_EMAIL
    server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
    server.login(EMAIL_USER, EMAIL_PASS)
    server.sendmail(EMAIL_USER, ADMIN_EMAIL, msg.as_string())
    server.quit()

def admin_required(func):
    from functools import wraps
    @wraps(func)
    def wrapper(*args, **kwargs):
        if 'admin_logged_in' not in session:
            return redirect(url_for('admin_login'))
        return func(*args, **kwargs)
    return wrapper

# =========================
# ROUTES
# =========================
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/shop")
def shop():
    db = get_db()
    products = db.execute("SELECT * FROM products").fetchall()
    return render_template("shop.html", products=products)

@app.route("/product/<int:product_id>")
def product_detail(product_id):
    product = get_product_by_id(product_id)
    if not product:
        return "Product not found", 404
    return render_template("product-detail.html", product=product)

@app.route("/cart", methods=["GET", "POST"])
def cart():
    cart_items = []
    total_price = 0
    if 'cart' in session:
        for item in session['cart']:
            product = get_product_by_id(item['id'])
            if product:
                subtotal = product['price'] * item['quantity']
                total_price += subtotal
                cart_items.append({
                    'id': product['id'],
                    'name': product['name'],
                    'price': product['price'],
                    'image_path': product['image_path'],
                    'quantity': item['quantity'],
                    'subtotal': subtotal
                })
    return render_template("cart.html", cart_items=cart_items, total_price=total_price)

@app.route("/add-to-cart", methods=["POST"])
def add_to_cart():
    product_id = int(request.form.get("product_id"))
    quantity = int(request.form.get("quantity", 1))

    if 'cart' not in session:
        session['cart'] = []

    for item in session['cart']:
        if item['id'] == product_id:
            item['quantity'] += quantity
            break
    else:
        session['cart'].append({'id': product_id, 'quantity': quantity})

    session.modified = True
    return redirect(url_for('cart'))

@app.route("/checkout")
def checkout():
    if 'cart' not in session or len(session['cart']) == 0:
        return redirect(url_for("cart"))
    return render_template("checkout.html")

@app.route("/create-checkout-session", methods=["POST"])
def create_checkout_session():
    if 'cart' not in session:
        return redirect(url_for("cart"))

    session['shipping_info'] = {
        "full_name": request.form.get("full_name"),
        "email": request.form.get("email"),
        "phone": request.form.get("phone"),
        "line1": request.form.get("line1"),
        "line2": request.form.get("line2"),
        "city": request.form.get("city"),
        "postal_code": request.form.get("postal_code"),
        "country": request.form.get("country"),
    }

    line_items = []
    for item in session['cart']:
        product = get_product_by_id(item['id'])
        if product:
            line_items.append({
                "price_data": {
                    "currency": "zar",
                    "product_data": {"name": product['name']},
                    "unit_amount": int(product['price'] * 100),
                },
                "quantity": item['quantity'],
            })

    checkout_session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=line_items,
        mode="payment",
        customer_email=session['shipping_info']['email'],
        success_url=DOMAIN_URL + "/payment-success",
        cancel_url=DOMAIN_URL + "/cart",
    )
    return redirect(checkout_session.url)

@app.route("/stripe-webhook", methods=["POST"])
def stripe_webhook():
    payload = request.data
    sig_header = request.headers.get("Stripe-Signature")
    try:
        event = stripe.Webhook.construct_event(payload, sig_header, STRIPE_WEBHOOK_SECRET)
    except Exception:
        return "Webhook error", 400

    if event["type"] == "checkout.session.completed":
        save_order(event["data"]["object"])
    return jsonify(success=True)

@app.route("/payment-success")
def payment_success():
    session.pop('cart', None)
    return render_template("payment-success.html")

# =========================
# ADMIN ROUTES
# =========================
@app.route("/admin-login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        db = get_db()
        admin = db.execute("SELECT * FROM admin WHERE username=?", (username,)).fetchone()
        if admin:
            try:
                ph.verify(admin['password_hash'], password)
                session['admin_logged_in'] = True
                return redirect(url_for("admin_dashboard"))
            except:
                flash("Invalid credentials")
        else:
            flash("Invalid credentials")
    return render_template("admin-login.html")

@app.route("/admin-dashboard")
@admin_required
def admin_dashboard():
    db = get_db()
    products = db.execute("SELECT * FROM products").fetchall()
    return render_template("admin-dashboard.html", products=products)

@app.route("/admin-add-product", methods=["POST"])
@admin_required
def admin_add_product():
    name = request.form.get("name")
    category = request.form.get("category")
    price = float(request.form.get("price"))
    color = request.form.get("color")
    size = request.form.get("size")
    image_path = request.form.get("image_path")
    description = request.form.get("description")
    db = get_db()
    db.execute("""
    INSERT INTO products (name, category, price, color, size, image_path, description)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (name, category, price, color, size, image_path, description))
    db.commit()
    return redirect(url_for("admin_dashboard"))

# =========================
# RUN APP
# =========================
if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=True)