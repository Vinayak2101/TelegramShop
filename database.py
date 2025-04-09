from pymongo import MongoClient
from dotenv import load_dotenv
import os

load_dotenv()

client = MongoClient(os.getenv("MONGODB_URI"))
db = client["keyshop"]
transactions_collection = db["transactions"]

def save_transaction(user_id, product, txid, currency, status="pending"):
    transactions_collection.insert_one({
        "user_id": user_id,
        "product": product,
        "txid": txid,
        "currency": currency,
        "status": status
    })

def update_transaction_status(txid, status):
    transactions_collection.update_one({"txid": txid}, {"$set": {"status": status}})

def get_transaction(txid):
    return transactions_collection.find_one({"txid": txid})
