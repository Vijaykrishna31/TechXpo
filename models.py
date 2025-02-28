from pymongo import MongoClient
from pymongo.server_api import ServerApi
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
import urllib.parse

# Connect to MongoDB
# client = MongoClient(
#     "mongodb+srv://sacs:sacs@gacslm@demo.zcw4w.mongodb.net/?retryWrites=true&w=majority&appName=demo"
# )
username = urllib.parse.quote_plus('sacs')
password = urllib.parse.quote_plus('sacs@gacslm')
uri = ""
client = MongoClient('mongodb+srv://%s:%s@demo.zcw4w.mongodb.net/?retryWrites=true&w=majority&appName=demo' % (username, password))

db = client["Trade_fair"]
users = db["users"]
products = db["products"]
bills = db["bills"]


class User(UserMixin):
    def __init__(self, username):
        self.username = username

    def get_id(self):
        return self.username

    @staticmethod
    def create_user(username, password):
        hashed_password = generate_password_hash(password)
        users.insert_one({"username": username, "password": hashed_password})

    @staticmethod
    def find_user(username):
        return users.find_one({"username": username})

    @staticmethod
    def verify_password(user, password):
        return check_password_hash(user["password"], password)


# Product-related methods
def insert_product(user_id, product_no, product_name, product_price):
    products.insert_one(
        {
            "user_id": user_id,
            "product_no": product_no,
            "product_name": product_name,
            "product_price": product_price,
        }
    )


def get_user_products(user_id):
    products_list = list(products.find({"user_id": user_id}))
    for product in products_list:
        product["_id"] = str(product["_id"])  # Convert ObjectId to string
    return products_list


# Bill-related methods
def insert_bill(
    user_id,
    bill_no,
    name,
    bill_class,
    bill_type,
    product_code,
    product_name,
    product_price,
    quantity,
    total,
):
    bills.insert_one(
        {
            "user_id": user_id,
            "bill_no": bill_no,
            "name": name,
            "class": bill_class,
            "type": bill_type,
            "product_code": product_code,
            "product_name": product_name,
            "product_price": product_price,
            "quantity": quantity,
            "total": total,
        }
    )


def get_user_bills(user_id):
    bills_list = list(bills.find({"user_id": user_id}))
    for bill in bills_list:
        bill["_id"] = str(bill["_id"])  # Convert ObjectId to string
    return bills_list


def get_next_bill_no(user_id):
    last_bill = bills.find_one({"user_id": user_id}, sort=[("bill_no", -1)])
    return 1 if last_bill is None else int(last_bill["bill_no"]) + 1


def get_all_users():
    return list(users.find({}, {"_id": 0, "password": 0}))  # Exclude sensitive data


def get_all_bills():
    return list(bills.find({}))


def get_all_products():
    return list(products.find({}))


def get_total_sales(user_id):
    user_bills = bills.find({"user_id": user_id})
    total_sales = sum(float(bill["total"]) for bill in user_bills)
    return total_sales
