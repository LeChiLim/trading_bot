# Strategy: Dual EMA
# This strategy uses two EMAs to determine the trend and entry points.
# strategy_ema9_25_xrpusdt.py
import zmq
import struct
import time
from collections import deque

# === CONFIG ===
SYMBOL = 'XRP/USDT'
HOST = '127.0.0.1'
PORT = 5000
URL = f"tcp://{HOST}:{PORT}"

EMA_FAST = 9
EMA_SLOW = 25

# === ZMQ SUB setup (matches your quote.py binary format) ===
context = zmq.Context()
sock = context.socket(zmq.SUB)
sock.connect(URL)
sock.setsockopt_string(zmq.SUBSCRIBE, "")  # subscribe to everything

# For EMA calculation
prices = deque()
ema9 = None
ema25 = None
position = 0  # 0 = flat, 1 = long, -1 = short

def update_ema(price, prev_ema, period):
    if prev_ema is None:
        return price
    k = 2 / (period + 1)
    return price * k + prev_ema * (1 - k)

print(f"EMA 9/25 Strategy listening for {SYMBOL}...")
print("Waiting for data...\n")

while True:
    try:
        # Receive your exact binary message format
        msg = sock.recv()  # blocks until message arrives
        bid, ask, symbol_bytes = struct.unpack('!dd16s', msg)
        symbol = symbol_bytes.split(b'\0', 1)[0].decode().strip()

        if symbol != SYMBOL:  # your quote.py sends "XRPUSDT"
            print("Skipping non-matching symbol:", symbol)
            continue

        price = (bid + ask) / 2  # mid price

        # Add price and keep only what we need
        prices.append(price)
        if len(prices) > EMA_SLOW:
            prices.popleft()

        # Wait until we have enough data
        if len(prices) < EMA_SLOW:
            print(f"\rWarming up... {len(prices)}/{EMA_SLOW}", end="")
            continue
        else:
            print("\rStrategy LIVE!                ", end="")

        # Update EMAs
        ema9 = update_ema(price, ema9, EMA_FAST)
        ema25 = update_ema(price, ema25, EMA_SLOW)

        # === SIMPLE CROSSOVER LOGIC ===
        if ema9 > ema25 and position <= 0:
            print(f"\nBUY SIGNAL @ {price:.6f} | EMA9={ema9:.6f} > EMA25={ema25:.6f}")
            position = 1
            # PLACE YOUR BUY ORDER HERE LATER:
            # exchange.create_market_buy_order(SYMBOL, amount)

        elif ema9 < ema25 and position >= 0:
            print(f"\nSELL/SHORT SIGNAL @ {price:.6f} | EMA9={ema9:.6f} < EMA25={ema25:.6f}")
            position = -1
            # PLACE YOUR SELL ORDER HERE LATER:
            # exchange.create_market_sell_order(SYMBOL, amount)

        # Optional: print current state every 5 seconds
        if int(time.time()) % 5 == 0:
            status = "LONG " if position == 1 else "SHORT" if position == -1 else "FLAT "
            print(f"\r[{time.strftime('%H:%M:%S')}] {status} | Price {price:.6f} | EMA9 {ema9:.6f} | EMA25 {ema25:.6f}", end="")

    except KeyboardInterrupt:
        print("\nStrategy stopped.")
        break
    except Exception as e:
        print("Error:", e)
        time.sleep(1)