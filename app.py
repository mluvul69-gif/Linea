from flask import Flask, render_template, g, session, redirect, url_for, request
from dotenv import load_dotenv
import os
import sqlite3

# =========================
# LOAD ENVIRONMENT VARIABLES
# =========================
load_dotenv()
app = Flask(__name__)
app.secret_key = "ebc60edce7b9ed46d32bb5a2544b0c13e587785a9c4376b961c041425ed1bf01"

# WhatsApp Business number
domain=os.getenv("DOMAIN_NAME")
WHATSAPP_NUMBER = 27610835100

# =========================
# DATABASE CONFIG
# =========================
DATABASE = os.path.join(app.root_path, "products.db")

def get_db():
    db = getattr(g, "_database", None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row  # Access columns by name
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, "_database", None)
    if db is not None:
        db.close()

# =========================
# INITIALIZE DB + SAMPLE PRODUCTS
# =========================
def init_db_with_samples():
    db = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row
    cursor = db.cursor()

    # Create products table
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

    # Insert sample products if table is empty
    cursor.execute("SELECT COUNT(*) AS count FROM products")
    result = cursor.fetchone()
    if result['count'] == 0:
        sample_products = [
            ('Series II-Black Hoodie',"Men",128, 'Black', 'S,M,L', 'static/images/products/black-hood.png', 'High-quality hoodie: heavyweight cotton fleece, soft brushed inside, strong stitching, thick ribbing, and a double-layer hood.'),
            ('Series II-White Hoodie', 'Men', 128, 'White', 'M,L,XL', 'static/images/products/white-hood.png', 'High-quality hoodie: heavyweight cotton fleece, soft brushed inside, strong stitching, thick ribbing, and a double-layer hood.'),
            ('Series I Cap', 'Men', 48, 'White', 'M,L', 'static/images/products/hat.png', 'Premium wool-blend hat crafted from heavyweight fabric with structured design.'),
            ('White-Form Trousers',"Men",128, 'Black', 'M,L,XL', 'static/images/products/trousers.png', 'Tailored men’s trousers crafted from premium wool-blend suiting fabric.'),
            ('Black Signature-Trousers',"Boys",88, 'Black', 'S,M,L', 'static/images/products/black-pant.png', 'Modern tailored trousers cut from high-grade wool-blend suiting fabric.'),
            ('White Signature-Trousers', 'Men', 88, 'White', 'M,L,XL', 'static/images/products/white-pant.png', 'Modern tailored trousers cut from high-grade wool-blend suiting fabric.'),
            ('First Collection-Black tee', 'Boys', 102, 'Black', 'M,L', 'static/images/products/black-tee.png', 'Luxury heavyweight T-shirt crafted from premium combed cotton.'),
            ('First Collection-White tee',"Boys",102, 'White', 'M,L,XL', 'static/images/products/white-tee.png', 'Luxury heavyweight T-shirt crafted from premium combed cotton.'),
            ('White Soft-Socks',"Boys",22, 'White', 'M,L,XL', 'static/images/products/socks.png', 'Premium soft-socks to keep you going.'),
            ('Edition II Mens-Shorts',"Boys",62, 'White', 'M,L,XL', 'static/images/products/shorts.png', 'Quality made shorts.'),
            ('Linea Women-Duo',"Boys",342, 'White', 'M,L,XL', 'static/images/products/duo.png', 'Our special premium offer, high quality women clothing.')
        ]
        cursor.executemany("""
        INSERT INTO products (name, category, price, color, size, image_path, description)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, sample_products)
        print("✅ Sample products inserted.")

    db.commit()
    db.close()

# =========================
# HELPER FUNCTION
# =========================
def get_product_by_id(product_id):
    db = get_db()
    cursor = db.execute("SELECT * FROM products WHERE id=?", (product_id,))
    return cursor.fetchone()

# =========================
# ROUTES
# =========================
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/shop")
def shop():
    db = get_db()
    cursor = db.execute("SELECT * FROM products")
    products = cursor.fetchall()
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
        db = get_db()
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

    # Update quantity if already in cart
    for item in session['cart']:
        if item['id'] == product_id:
            item['quantity'] += quantity
            break
    else:
        session['cart'].append({
            'id': product_id,
            'quantity': quantity
        })

    session.modified = True
    return redirect(url_for('cart'))

# =========================
# CHECKOUT PAGE
# =========================
@app.route("/checkout")
def checkout():
    total_price = 0
    if 'cart' in session:
        for item in session['cart']:
            product = get_product_by_id(item['id'])
            if product:
                total_price += product['price'] * item['quantity']
    return render_template("checkout.html", total_price=total_price)

# =========================
# PROCESS PAYMENT VIA WHATSAPP
# =========================
@app.route("/process-payment", methods=["POST"])
def process_payment():
    total_price = request.form.get("total_price")
    cart_details = ""
    if 'cart' in session:
        for item in session['cart']:
            product = get_product_by_id(item['id'])
            if product:
                cart_details += f"{product['name']} x{item['quantity']}, "

    # WhatsApp pre-filled message link
    message = f"New order! Total: R{total_price}. Items: {cart_details}"
    whatsapp_link = f"https://api.whatsapp.com/send?phone={WHATSAPP_NUMBER}&text={message}"

    # Clear cart
    session.pop('cart', None)

    # Redirect to success page
    return redirect(url_for("payment_success", whatsapp=whatsapp_link))

# =========================
# PAYMENT SUCCESS PAGE
# =========================
@app.route("/payment-success")
def payment_success():
    whatsapp_link = request.args.get("whatsapp")
    return render_template("payment-success.html", whatsapp_link=whatsapp_link)

# =========================
# RUN APP
# =========================
if __name__ == "__main__":
    init_db_with_samples()
    app.run(host=domain, port=5000, debug=True)


