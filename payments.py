from blockcypher import create_unsigned_tx, make_tx_signatures, broadcast_signed_tx, get_address_overview
from binance.spot import Spot
from dotenv import load_dotenv
import os

load_dotenv()

# BlockCypher for BTC and LTC
BTC_API_KEY = os.getenv("BTC_API_KEY")
LTC_API_KEY = os.getenv("LTC_API_KEY")
BNB_API_KEY = os.getenv("BNB_API_KEY")
BNB_API_SECRET = os.getenv("BNB_API_SECRET")

# Binance client for USDT (BEP-20)
binance_client = Spot(BNB_API_KEY, BNB_API_SECRET)

# Your master wallet addresses (replace with real ones)
BTC_WALLET = "your_btc_address"
LTC_WALLET = "your_ltc_address"
BNB_WALLET = "your_bnb_address"  # BEP-20 compatible

def generate_address(currency):
    if currency == "BTC":
        # Generate new BTC address
        response = requests.post(
            f"https://api.blockcypher.com/v1/btc/main/addrs?token={BTC_API_KEY}"
        )
        return response.json()["address"]
    elif currency == "LTC":
        response = requests.post(
            f"https://api.blockcypher.com/v1/ltc/main/addrs?token={LTC_API_KEY}"
        )
        return response.json()["address"]
    elif currency == "USDT_BEP20":
        # Generate deposit address for BEP-20 (Binance API)
        response = binance_client.new_deposit_address(coin="USDT", network="BSC")
        return response["address"]
    return None

def check_payment(address, currency, amount):
    if currency == "BTC":
        overview = get_address_overview(address, api_key=BTC_API_KEY, coin_symbol="btc")
        return overview["final_balance"] >= amount * 10**8  # Convert to satoshis
    elif currency == "LTC":
        overview = get_address_overview(address, api_key=LTC_API_KEY, coin_symbol="ltc")
        return overview["final_balance"] >= amount * 10**8
    elif currency == "USDT_BEP20":
        # Check Binance deposit history
        deposits = binance_client.get_deposit_history(coin="USDT", status=1)  # Confirmed deposits
        for deposit in deposits:
            if deposit["address"] == address and float(deposit["amount"]) >= amount:
                return True
        return False
    return False
