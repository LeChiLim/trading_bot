# Strategy: Statistical Arbitrage (Stat Arb) for BTC/ETH Pair
# This strategy uses cointegration and mean reversion on the BTC/ETH spread.
import zmq
import struct
import time
import json
from collections import deque
import argparse
import numpy as np  # For regression and stats

# === CONFIG ===
SYMBOL1 = 'BTCUSDT'  # Primary symbol (e.g., BTC)
SYMBOL2 = 'ETHUSDT'  # Secondary symbol (e.g., ETH)
HOST = '127.0.0.1'
QUOTE_PORT = 5000  # Port for receiving price quotes
TRADE_PORT = 5001  # Port for sending trade orders
QUOTE_URL = f"tcp://{HOST}:{QUOTE_PORT}"
TRADE_URL = f"tcp://{HOST}:{TRADE_PORT}"

LOOKBACK = 100  # Number of periods for rolling stats and beta
ENTRY_Z = 2.0   # Z-score threshold for entry
EXIT_Z = 0.5    # Z-score threshold for exit (closer to mean)
TIME_PERIOD = 60  # Update stats every N seconds (60 = 1 minute)
MAX_PRICES_SIZE = 200  # Maximum number of prices to keep in memory (larger for lookback)
STRATEGY_NAME = "stat_arb_btc_eth"  # Name of this strategy

def run_strategy():
    """Stat Arb strategy: sends paired trade signals via ZMQ PUSH"""
    # === ZMQ SUB setup (receives price quotes) ===
    context = zmq.Context()
    quote_sock = context.socket(zmq.SUB)
    quote_sock.connect(QUOTE_URL)
    quote_sock.setsockopt_string(zmq.SUBSCRIBE, "")  # subscribe to everything

    # === ZMQ PUSH setup (sends trade orders) ===
    trade_sock = context.socket(zmq.PUSH)
    trade_sock.connect(TRADE_URL)

    # For price storage
    prices1 = deque(maxlen=MAX_PRICES_SIZE)  # For SYMBOL1 (BTC)
    prices2 = deque(maxlen=MAX_PRICES_SIZE)  # For SYMBOL2 (ETH)
    current_data = {
        SYMBOL1: {'bid': 0, 'ask': 0, 'mid': 0},
        SYMBOL2: {'bid': 0, 'ask': 0, 'mid': 0}
    }
    position = 0  # 0 = flat, 1 = long spread (long BTC, short ETH), -1 = short spread (short BTC, long ETH)
    last_update_time = None  # Track when we last updated stats

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
            print(f"  Warning: Could not send {order_type} for {symbol} (queue full)")
            return False
        except Exception as e:
            print(f"  Error sending order for {symbol}: {e}")
            return False

    def send_pair_orders(action1, symbol1, price1, action2, symbol2, price2):
        """Send two orders for the pair"""
        success1 = send_order(action1, symbol1, price1, STRATEGY_NAME)
        success2 = send_order(action2, symbol2, price2, STRATEGY_NAME)
        if success1 and success2:
            print(f"  → Pair orders sent: {action1} {symbol1}, {action2} {symbol2}")
        return success1 and success2

    print(f"Stat Arb Strategy for {SYMBOL1}/{SYMBOL2} listening on {QUOTE_URL} and trade pub on {TRADE_URL}...")
    print(f"Lookback: {LOOKBACK} | Entry Z: {ENTRY_Z} | Exit Z: {EXIT_Z}")
    print(f"Update period: {TIME_PERIOD} seconds ({TIME_PERIOD/60:.1f} minutes)")
    print("Waiting for data...\n")

    while True:
        try:
            # Receive quote message
            msg = quote_sock.recv()  # blocks until message arrives
            bid, ask, ts, symbol_bytes = struct.unpack('!ddd16s', msg)
            symbol = symbol_bytes.split(b'\0', 1)[0].decode().strip()

            if symbol not in [SYMBOL1, SYMBOL2]:
                continue

            price = (bid + ask) / 2  # mid price
            current_data[symbol]['bid'] = bid
            current_data[symbol]['ask'] = ask
            current_data[symbol]['mid'] = price
            current_time = ts

            # Append price to the appropriate deque
            if symbol == SYMBOL1:
                prices1.append(price)
            elif symbol == SYMBOL2:
                prices2.append(price)

            # Check if it's time to update stats (every TIME_PERIOD seconds)
            should_update = False
            if last_update_time is None:
                # First update - wait until we have minimum data for both
                if len(prices1) >= LOOKBACK and len(prices2) >= LOOKBACK:
                    should_update = True
                    last_update_time = current_time
                else:
                    print(f"\rWarming up... BTC: {len(prices1)}/{LOOKBACK} | ETH: {len(prices2)}/{LOOKBACK}", end="")
                    continue
            elif current_time - last_update_time >= TIME_PERIOD:
                should_update = True
                last_update_time = current_time

            # Only update stats and check signals at the configured time interval
            if should_update:
                print("\rStrategy LIVE!                ", end="")

                # Get recent prices (assume roughly synced since quotes are frequent)
                p1 = np.array(list(prices1)[-LOOKBACK:])
                p2 = np.array(list(prices2)[-LOOKBACK:])

                # Compute beta (hedge ratio): regress p1 on p2
                beta = np.polyfit(p2, p1, 1)[0]

                # Compute historical spreads
                spreads = p1 - beta * p2
                mean_spread = np.mean(spreads)
                std_spread = np.std(spreads)

                # Current spread and Z-score
                current_p1 = current_data[SYMBOL1]['mid']
                current_p2 = current_data[SYMBOL2]['mid']
                current_spread = current_p1 - beta * current_p2
                zscore = (current_spread - mean_spread) / std_spread if std_spread != 0 else 0

                # === STAT ARB LOGIC ===
                # Long spread: BUY BTC (at ask), SELL ETH (at bid)
                # Short spread: SELL BTC (at bid), BUY ETH (at ask)
                if zscore > ENTRY_Z and position != -1:
                    print(f"\nSHORT SPREAD SIGNAL @ Z={zscore:.2f} | Spread={current_spread:.6f}")
                    send_pair_orders(
                        'SELL', SYMBOL1, current_data[SYMBOL1]['bid'],
                        'BUY', SYMBOL2, current_data[SYMBOL2]['ask']
                    )
                    position = -1

                elif zscore < -ENTRY_Z and position != 1:
                    print(f"\nLONG SPREAD SIGNAL @ Z={zscore:.2f} | Spread={current_spread:.6f}")
                    send_pair_orders(
                        'BUY', SYMBOL1, current_data[SYMBOL1]['ask'],
                        'SELL', SYMBOL2, current_data[SYMBOL2]['bid']
                    )
                    position = 1

                elif abs(zscore) < EXIT_Z and position != 0:
                    print(f"\nEXIT SIGNAL @ Z={zscore:.2f} | Spread={current_spread:.6f}")
                    if position == 1:  # Close long spread
                        send_pair_orders(
                            'SELL', SYMBOL1, current_data[SYMBOL1]['bid'],
                            'BUY', SYMBOL2, current_data[SYMBOL2]['ask']
                        )
                    elif position == -1:  # Close short spread
                        send_pair_orders(
                            'BUY', SYMBOL1, current_data[SYMBOL1]['ask'],
                            'SELL', SYMBOL2, current_data[SYMBOL2]['bid']
                        )
                    position = 0

            # Optional: print current state every 5 seconds (if warmed up)
            if len(prices1) >= LOOKBACK and len(prices2) >= LOOKBACK and int(current_time) % 5 == 0:
                status = "LONG SPREAD " if position == 1 else "SHORT SPREAD" if position == -1 else "FLAT "
                print(f"\r[{time.strftime('%H:%M:%S')}] {status} | BTC {current_data[SYMBOL1]['mid']:.2f} | ETH {current_data[SYMBOL2]['mid']:.2f} | Z ? ", end="")

        except KeyboardInterrupt:
            print("\nStrategy stopped.")
            quote_sock.close()
            trade_sock.close()
            context.term()
            break
        except Exception as e:
            print("Error:", e)
            time.sleep(1)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
                    prog='Subscriber Tool',
                    description='Subscribe to any zmq host and port.')

    parser.add_argument('--host', type=str, default=HOST, help='Host to connect to')     
    parser.add_argument('--quote_port', type=int, default=QUOTE_PORT, help='Quote Port to connect to') 
    parser.add_argument('--trade_port', type=int, default=TRADE_PORT, help='Trade Port to connect to')   
    parser.add_argument('--backtest', action='store_true',
                    help='Set to True if connecting to backtester data feed.')

    args = parser.parse_args()

    if args.backtest == True:
        QUOTE_PORT = 5557  # Backtester data feed port
        QUOTE_URL = f"tcp://{HOST}:{QUOTE_PORT}"

        TRADE_PORT = 5558  # Backtester trade order port
        TRADE_URL = f"tcp://{HOST}:{TRADE_PORT}"

    run_strategy()
```