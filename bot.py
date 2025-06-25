from flask import Flask, request, jsonify
import requests
import time
import hmac
import hashlib
import os
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)

API_KEY = os.getenv("BINANCE_API_KEY")
SECRET_KEY = os.getenv("BINANCE_SECRET_KEY").encode()
SYMBOL = os.getenv("SYMBOL")
QTY = os.getenv("ORDER_QTY")
BASE_URL = "https://testnet.binance.vision"

def place_order(side):
    endpoint = "/api/v3/order"
    url = BASE_URL + endpoint
    timestamp = int(time.time() * 1000)
    params = f"symbol={SYMBOL}&side={side.upper()}&type=MARKET&quantity={QTY}&timestamp={timestamp}"
    signature = hmac.new(SECRET_KEY, params.encode(), hashlib.sha256).hexdigest()
    headers = {"X-MBX-APIKEY": API_KEY}
    full_url = f"{url}?{params}&signature={signature}"

    print(f"[DEBUG] Sending {side.upper()} order for {QTY} {SYMBOL}")
    response = requests.post(full_url, headers=headers)
    print(f"[DEBUG] Binance Response: {response.status_code} - {response.text}")

    # 🧾 Log Balance
    log_balance()

    return response


def log_balance():
    timestamp = int(time.time() * 1000)
    params = f"timestamp={timestamp}"
    signature = hmac.new(SECRET_KEY, params.encode(), hashlib.sha256).hexdigest()
    url = f"{BASE_URL}/api/v3/account?{params}&signature={signature}"
    headers = {"X-MBX-APIKEY": API_KEY}
    response = requests.get(url, headers=headers).json()

    print("=== Binance Testnet Balance ===")
    for asset in response["balances"]:
        free = float(asset["free"])
        locked = float(asset["locked"])
        if free > 0 or locked > 0:
            print(f"{asset['asset']}: Free={free} | Locked={locked}")



@app.route("/", methods=["POST"])
def webhook():
    data = request.get_json()
    signal = data.get("signal", "").lower()

    print(f"[DEBUG] Webhook received: {data}")

    if signal not in ["long", "short"]:
        print("[ERROR] Invalid signal received")
        return jsonify({"error": "Invalid signal"}), 400

    side = "BUY" if signal == "long" else "SELL"
    response = place_order(side)

    if response.status_code == 200:
        return jsonify({"message": f"{side} order placed"})
    else:
        return jsonify({"error": response.json()}), 500

if __name__ == "__main__":
    app.run(port=5000)
