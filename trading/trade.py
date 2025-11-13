# trade_daemon/trade.py
import ccxt
import pynng
import struct
import time
import os
from dotenv import load_dotenv
load_dotenv()

# === CONFIG ===
API_KEY = os.getenv('BINANCE_TESTNET_KEY')
print(API_KEY)
API_SECRET = os.getenv('BINANCE_TESTNET_SECRET')
print(API_SECRET)
SYMBOL = "XRP/USDT"
TEST_TRADE_SIZE_USD = 10 
PUB_MULTICAST_URL = "tcp://127.0.0.1:5000"
# ==================

# Binance with API keys
exchange = ccxt.binance({
    'apiKey': API_KEY,
    'secret': API_SECRET,
    'enableRateLimit': True,
    'options': {'defaultType': 'spot'}
})

exchange.set_sandbox_mode(True)
print("Using Binance TESTNET endpoints")


# nng subscriber
sock = pynng.Sub0()
sock.dial(PUB_MULTICAST_URL)
sock.subscribe(b'')  # All messages

print(f"Trade Daemon listening on {PUB_MULTICAST_URL}")
print(f"Will place ${TEST_TRADE_SIZE_USD} {SYMBOL} orders")

while True:
    try:
        msg = sock.recv()
        bid, ask, symbol_bytes = struct.unpack('!dd16s', msg)
        symbol = symbol_bytes.decode().rstrip('\0')
        print(f"Signal → Bid: ${bid:.4f} | Ask: ${ask:.4f}")

        # === SIMPLE STRATEGY: Buy on any signal ===
        amount = TEST_TRADE_SIZE_USD / ask
        order = exchange.create_market_buy_order(symbol, amount)
        print(f"ORDER PLACED: {amount:.6f} BTC/USDT @ ${ask:.4f}")
        print(f"Order ID: {order['id']}")

        break  # Remove this line to keep trading

    except Exception as e:
        print("Error:", e)
    
    time.sleep(1)