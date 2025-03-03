from flask import Flask, render_template, redirect, url_for, request, flash
from flask_login import (
    LoginManager,
    UserMixin,
    login_user,
    login_required,
    logout_user,
    current_user,
)
from models import (
    User,
    insert_product,
    get_user_products,
    insert_bill,
    get_user_bills,
    get_next_bill_no,
    get_all_bills,
    get_all_products,
    get_all_users,
    get_total_sales,
)
from bson import ObjectId

app = Flask(__name__)
app.secret_key = "your_secret_key"

# Flask-Login setup
login_manager = LoginManager(app)
login_manager.login_view = "login"


@login_manager.user_loader
def load_user(username):
    user = User.find_user(username)
    if user:
        return User(username=user["username"])
    return None


@app.context_processor
def inject_functions():
    return dict(get_next_bill_no=get_next_bill_no)


@app.route("/")
@login_required
def home():
    user_bills = get_user_bills(
        current_user.username
    )  # Fetch bills for the current user
    total_sales = get_total_sales(
        current_user.username
    )  # Calculate total sales for the user
    return render_template(
        "index.html",
        username=current_user.username,
        bills=user_bills,
        total_sales=total_sales,
    )


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        remember = request.form.get("remember")

        user = User.find_user(username)
        if user and User.verify_password(user, password):
            user_obj = User(username=user["username"])
            login_user(user_obj, remember=remember)
            return redirect(url_for("home"))
        flash("Invalid username or password", "error")
    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if User.find_user(username):
            flash("Username already exists", "error")
        else:
            User.create_user(username, password)
            flash("Registration successful! Please login.", "success")
            return redirect(url_for("login"))
    return render_template("register.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))


@app.route("/products", methods=["GET", "POST"])
@login_required
def products():
    if request.method == "POST":
        product_no = request.form["product_no"]
        product_name = request.form["product_name"]
        product_price = request.form["product_price"]
        insert_product(current_user.username, product_no, product_name, product_price)
        flash("Product added successfully!", "success")
    user_products = get_user_products(current_user.username)
    return render_template("products.html", products=user_products)


@app.route("/edit_product/<product_id>", methods=["GET", "POST"])
@login_required
def edit_product(product_id):
    product = products.find_one({"_id": ObjectId(product_id)})
    if not product:
        flash("Product not found!", "error")
        return redirect(url_for("products"))

    if request.method == "POST":
        product_no = request.form.get("product_no")
        product_name = request.form.get("product_name")
        product_price = request.form.get("product_price")

        products.update_one(
            {"_id": ObjectId(product_id)},
            {
                "$set": {
                    "product_no": product_no,
                    "product_name": product_name,
                    "product_price": float(product_price),
                }
            },
        )
        flash("Product updated successfully!", "success")
        return redirect(url_for("products"))

    return render_template("edit_product.html", product=product)


@app.route("/delete_product/<product_id>")
@login_required
def delete_product(product_id):
    products.delete_one({"_id": ObjectId(product_id)})
    flash("Product deleted successfully!", "success")
    return redirect(url_for("products"))


@app.route("/bills", methods=["GET", "POST"])
@login_required
def bills():
    user_products = get_user_products(current_user.username)
    if request.method == "POST":
        payment_method = request.form["payment_method"]
        overall_total = float(request.form["overall_total"].replace("$", ""))
        bill_no = get_next_bill_no(current_user.username)

        for product in user_products:
            quantity = int(request.form.get(f"quantity_{product['product_no']}", 0))
            if quantity > 0:
                insert_bill(
                    current_user.username,
                    bill_no,
                    "",  # Empty name
                    "",  # Empty class
                    payment_method,
                    product["product_no"],
                    product["product_name"],
                    product["product_price"],
                    quantity,
                    float(product["product_price"]) * quantity,
                )

        flash("Bill created successfully!", "success")
        return redirect(url_for("bills"))

    return render_template("bills.html", products=user_products)


@app.route("/admin")
@login_required
def admin():
    if current_user.username != "admin":  # Ensure only the admin can access this page
        flash("Access denied!", "error")
        return redirect(url_for("home"))

    all_users = get_all_users()
    all_bills = get_all_bills()
    all_products = get_all_products()

    # Calculate total sales for each user
    user_sales = {
        user["username"]: get_total_sales(user["username"]) for user in all_users
    }

    return render_template(
        "admin.html",
        users=all_users,
        bills=all_bills,
        products=all_products,
        user_sales=user_sales,
        username=current_user.username,
    )


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
