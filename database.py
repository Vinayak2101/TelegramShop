from pymongo import MongoClient
from dotenv import load_dotenv
import os

load_dotenv()

client = MongoClient(os.getenv("MONGODB_URI"))
db = client["keyshop"]
keys_collection = db["keys"]
users_collection = db["users"]
transactions_collection = db["transactions"]

def add_key(product, key):
    keys_collection.insert_one({"product": product, "key": key, "sold": False})

def get_available_key(product):
    return keys_collection.find_one({"product": product, "sold": False})

def mark_key_sold(key_id):
    keys_collection.update_one({"_id": key_id}, {"$set": {"sold": True}})

def save_transaction(user_id, product, address, currency, amount, status="pending"):
    transactions_collection.insert_one({
        "user_id": user_id,
        "product": product,
        "address": address,
        "currency": currency,
        "amount": amount,
        "status": status
    })

def update_transaction_status(address, status):
    transactions_collection.update_one({"address": address}, {"$set": {"status": status}})
