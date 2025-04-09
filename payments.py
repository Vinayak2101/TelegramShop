from dotenv import load_dotenv
import os
import requests

load_dotenv()

SELLAUTH_SHOP_ID = os.getenv("SELLAUTH_SHOP_ID")
SELLAUTH_API_KEY = os.getenv("SELLAUTH_API_KEY")

def generate_sellauth_checkout(product_id, variant_id, quantity, gateway):
    url = f"https://api.sellauth.com/v1/shops/{SELLAUTH_SHOP_ID}/checkout"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {SELLAUTH_API_KEY}"
    }
    payload = {
        "cart": [{
            "productId": product_id,
            "variantId": variant_id,
            "quantity": quantity
        }],
        "gateway": gateway
    }
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code == 200:
        data = response.json()
        return data.get("txid") or data.get("transaction_id") or data.get("id")
    else:
        raise Exception(f"Sellauth checkout error: {response.text}")

def check_sellauth_transaction_status(txid):
    url = f"https://api.sellauth.com/v1/shops/{SELLAUTH_SHOP_ID}/payouts/transactions"
    headers = {
        "Authorization": f"Bearer {SELLAUTH_API_KEY}"
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        transactions = response.json().get("data", [])
        for tx in transactions:
            if tx.get("txid") == txid and tx.get("confirmations", 0) >= 1:
                return True
        return False
    else:
        raise Exception(f"Transaction status check failed: {response.text}")
