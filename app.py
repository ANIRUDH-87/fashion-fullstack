import sqlite3
from flask import Flask, render_template, request, session, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "secret123"

def is_valid_password(password):
    if len(password) < 8:
        return False

    has_upper = False
    has_lower = False
    has_digit = False
    has_special = False

    for ch in password:
        if ch.isupper():
            has_upper = True
        elif ch.islower():
            has_lower = True
        elif ch.isdigit():
            has_digit = True
        elif ch in "@#$!%&*":
            has_special = True

    return has_upper and has_lower and has_digit and has_special


# ---------------- PRODUCT DATA ----------------
PRODUCT_PRICES = {
    "shoes1": 1999,
    "shoes2": 1799,
    "shirt2": 999,
    "shirt3": 1099,
    "shirt4": 1199,
    "pant2": 1399,
    "pant3": 1299,
    "pant4": 1499,
    "watch1": 2499,
    "watch2": 2299,
    "watch3": 2199,
    "watch4": 2099
}

PRODUCT_NAMES = {
    "shoes1": "Sports Shoes",
    "shoes2": "Casual Shoes",
    "shirt2": "Formal Shirt",
    "shirt3": "Printed Shirt",
    "shirt4": "Denim Shirt",
    "pant2": "Jeans Pants",
    "pant3": "Cotton Pants",
    "pant4": "Formal Pants",
    "watch1": "Smart Watch",
    "watch2": "Leather Watch",
    "watch3": "Classic Watch",
    "watch4": "Digital Watch"
}

# ---------------- DATABASE ----------------
def get_db_connection():
    conn = sqlite3.connect("fashion.db")
    conn.row_factory = sqlite3.Row
    return conn

def create_users_table():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT UNIQUE,
            password TEXT
        )
    """)

    conn.commit()
    conn.close()

# ---------------- HOME ----------------
@app.route("/")
def home():
    if "user_id" not in session:
        return redirect(url_for("login"))

    cart = session.get("cart", {})
    cart_count = sum(cart.values())

    return render_template("index.html", cart_count=cart_count)

# ---------------- SIGNUP ----------------
@app.route("/signup", methods=["GET", "POST"])
def signup():
    message = ""

    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]

        if password != confirm_password:
            message = "Passwords do not match"
            return render_template("signup.html", message=message)

        hashed_password = generate_password_hash(password)

        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            cursor.execute(
                "INSERT INTO users (name, email, password) VALUES (?, ?, ?)",
                (name, email, hashed_password)
            )

            conn.commit()
            conn.close()

            message = "Account created successfully! Please login."

        except sqlite3.IntegrityError:
            message = "Email already exists."

    return render_template("signup.html", message=message)

# ---------------- LOGIN ----------------
@app.route("/login", methods=["GET", "POST"])
def login():
    message = ""

    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
        user = cursor.fetchone()
        conn.close()

        if user and check_password_hash(user["password"], password):
            session["user_id"] = user["id"]
            session["user_name"] = user["name"]
            return redirect(url_for("home"))
        else:
            message = "Invalid email or password"

    return render_template("login.html", message=message)

# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# ---------------- CART ----------------
@app.route("/add-to-cart", methods=["POST"])
def add_to_cart():
    product = request.form["product"]

    if "cart" not in session:
        session["cart"] = {}

    session["cart"][product] = session["cart"].get(product, 0) + 1
    session.modified = True

    return redirect(url_for("home") + "#products")

@app.route("/update-cart", methods=["POST"])
def update_cart():
    product = request.form["product"]
    action = request.form["action"]

    if "cart" in session and product in session["cart"]:
        if action == "plus":
            session["cart"][product] += 1
        elif action == "minus":
            session["cart"][product] -= 1
            if session["cart"][product] <= 0:
                del session["cart"][product]

    session.modified = True
    return redirect(url_for("cart") + "#cart")

@app.route("/cart")
def cart():
    if "user_id" not in session:
        return redirect(url_for("login"))

    cart = session.get("cart", {})
    subtotal = 0

    for product, qty in cart.items():
        subtotal += PRODUCT_PRICES.get(product, 0) * qty

    gst = round(subtotal * 0.18, 2)
    discount = session.get("discount", 0)
    total = subtotal + gst - discount

    return render_template(
        "cart.html",
        cart_items=cart,
        prices=PRODUCT_PRICES,
        names=PRODUCT_NAMES,
        subtotal=subtotal,
        gst=gst,
        discount=discount,
        total=total
    )

@app.route("/apply-coupon", methods=["POST"])
def apply_coupon():
    code = request.form["coupon"]

    if code == "SAVE100":
        session["discount"] = 100
    elif code == "SAVE200":
        session["discount"] = 200
    else:
        session["discount"] = 0

    session.modified = True
    return redirect(url_for("cart"))

# ---------------- CHECKOUT ----------------
@app.route("/checkout", methods=["GET", "POST"])
def checkout():
    if "user_id" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        session.pop("cart", None)
        session.pop("discount", None)
        return render_template("success.html")

    return render_template("checkout.html")

# ---------------- MAIN ----------------
if __name__ == "__main__":
    create_users_table()

import os

if __name__ == "__main__":
    create_users_table()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

