# Strategy: Dual EMA
# This strategy uses two EMAs to determine the trend and entry points.
import zmq
import struct
import time
import json
from collections import deque

# === CONFIG ===
SYMBOL = 'XRP/USDT'
HOST = '127.0.0.1'
QUOTE_PORT = 5000  # Port for receiving price quotes
TRADE_PORT = 5001  # Port for sending trade orders
QUOTE_URL = f"tcp://{HOST}:{QUOTE_PORT}"
TRADE_URL = f"tcp://{HOST}:{TRADE_PORT}"

EMA_FAST = 9
EMA_SLOW = 25
TIME_PERIOD = 60  # Update EMAs every N seconds (300 = 5 minutes)
MAX_PRICES_SIZE = 100  # Maximum number of prices to keep in memory
STRATEGY_NAME = "dual_ema"  # Name of this strategy

# === ZMQ SUB setup (receives price quotes) ===
context = zmq.Context()
quote_sock = context.socket(zmq.SUB)
quote_sock.connect(QUOTE_URL)
quote_sock.setsockopt_string(zmq.SUBSCRIBE, "")  # subscribe to everything

# === ZMQ PUSH setup (sends trade orders) ===
trade_sock = context.socket(zmq.PUSH)
trade_sock.connect(TRADE_URL)

# For EMA calculation
prices = deque()
ema9 = None
ema25 = None
position = 0  # 0 = flat, 1 = long, -1 = short
last_update_time = None  # Track when we last updated EMAs

def update_ema(price, prev_ema, period):
    if prev_ema is None:
        return price
    k = 2 / (period + 1)
    return price * k + prev_ema * (1 - k)

def send_order(order_type, symbol, price, strategy_name):
    """Send order signal to trade daemon via ZMQ PUSH"""
    order = {
        'order_type': order_type,  # 'BUY' or 'SELL'
        'symbol': symbol,
        'price': price,
        'strategy_name': strategy_name,
        'timestamp': time.time()
    }
    try:
        trade_sock.send_string(json.dumps(order), zmq.NOBLOCK)
        return True
    except zmq.Again:
        print(f"  Warning: Could not send {order_type} order (queue full)")
        return False
    except Exception as e:
        print(f"  Error sending order: {e}")
        return False

print(f"EMA 9/25 Strategy listening for {SYMBOL}...")
print(f"Update period: {TIME_PERIOD} seconds ({TIME_PERIOD/60:.1f} minutes)")
print("Waiting for data...\n")

while True:
    try:
        # Receive your exact binary message format
        msg = quote_sock.recv()  # blocks until message arrives
        bid, ask, symbol_bytes = struct.unpack('!dd16s', msg)
        symbol = symbol_bytes.split(b'\0', 1)[0].decode().strip()

        if symbol != SYMBOL:  # your quote.py sends "XRPUSDT"
            print("Skipping non-matching symbol:", symbol)
            continue

        price = (bid + ask) / 2  # mid price
        # Store bid/ask for order execution
        current_bid = bid
        current_ask = ask
        current_time = time.time()

        # Add price and keep only max size
        prices.append(price)
        if len(prices) > MAX_PRICES_SIZE:
            prices.popleft()

        # Check if it's time to update EMAs (every TIME_PERIOD seconds)
        should_update = False
        if last_update_time is None:
            # First update - wait until we have minimum data
            if len(prices) >= EMA_SLOW:
                should_update = True
                last_update_time = current_time
            else:
                print(f"\rWarming up... {len(prices)}/{EMA_SLOW}", end="")
                continue
        elif current_time - last_update_time >= TIME_PERIOD:
            should_update = True
            last_update_time = current_time

        # Only update EMAs and check signals at the configured time interval
        if should_update:
            print("\rStrategy LIVE!                ", end="")

            # Update EMAs
            ema9 = update_ema(price, ema9, EMA_FAST)
            ema25 = update_ema(price, ema25, EMA_SLOW)

            # === SIMPLE CROSSOVER LOGIC ===
            if ema9 > ema25 and position <= 0:
                print(f"\nBUY SIGNAL @ {price:.6f} | EMA9={ema9:.6f} > EMA25={ema25:.6f}")
                position = 1
                # Send BUY order to trade daemon
                if send_order('BUY', SYMBOL, current_ask, STRATEGY_NAME):
                    print(f"  → BUY order sent to trade daemon")

            elif ema9 < ema25 and position >= 0:
                print(f"\nSELL SIGNAL @ {price:.6f} | EMA9={ema9:.6f} < EMA25={ema25:.6f}")
                position = -1
                # Send SELL order to trade daemon
                if send_order('SELL', SYMBOL, current_bid, STRATEGY_NAME):
                    print(f"  → SELL order sent to trade daemon")

        # Optional: print current state every 5 seconds (only if EMAs are initialized)
        if ema9 is not None and ema25 is not None and int(current_time) % 5 == 0:
            status = "LONG " if position == 1 else "SHORT" if position == -1 else "FLAT "
            print(f"\r[{time.strftime('%H:%M:%S')}] {status} | Price {price:.6f} | EMA9 {ema9:.6f} | EMA25 {ema25:.6f}", end="")

    except KeyboardInterrupt:
        print("\nStrategy stopped.")
        quote_sock.close()
        trade_sock.close()
        context.term()
        break
    except Exception as e:
        print("Error:", e)
        time.sleep(1)