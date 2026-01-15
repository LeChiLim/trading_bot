#Strategy: Arbitrage between multiple exchanges

import zmq
import struct
import time
import json
from collections import deque
import argparse

# === CONFIG ===
SYMBOL = 'BTC/USD'
HOST = '127.0.0.1'

TRADE_PORT = 5001  # Port for sending trade orders
QUOTE_BINANCE_URL = f"tcp://{HOST}:5001"
QUOTE_CRYPTOCOMS_URL = f"tcp://{HOST}:5002"
QUOTE_KRAKEN_URL = f"tcp://{HOST}:5003"
QUOTE_KUCOIN_URL = f"tcp://{HOST}:5004"

TRADE_URL = f"tcp://{HOST}:{TRADE_PORT}"
STRATEGY_NAME = "Strategy Arb"  # Name of this strategy

def send_order(trade_sock, order_type, symbol, price, strategy_name):
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


def run_strategy():
    # === ZMQ SUB setup (receives price quotes) ===
    binance_context = zmq.Context()
    quote_sock_binance = binance_context.socket(zmq.SUB)
    quote_sock_binance.connect(QUOTE_BINANCE_URL)
    quote_sock_binance.setsockopt_string(zmq.SUBSCRIBE, "")  
    print("Subscribed to Binance quotes.")
    cryptocoms_context = zmq.Context()
    quote_sock_cryptocoms = cryptocoms_context.socket(zmq.SUB)
    quote_sock_cryptocoms.connect(QUOTE_CRYPTOCOMS_URL)
    quote_sock_cryptocoms.setsockopt_string(zmq.SUBSCRIBE, "")
    print("Subscribed to Cryptocoms quotes.")
    kraken_context = zmq.Context()
    quote_sock_kraken = kraken_context.socket(zmq.SUB)
    quote_sock_kraken.connect(QUOTE_KRAKEN_URL)
    quote_sock_kraken.setsockopt_string(zmq.SUBSCRIBE, "")
    print("Subscribed to Kraken quotes.")
    kucoin_context = zmq.Context()
    quote_sock_kucoin = kucoin_context.socket(zmq.SUB)
    quote_sock_kucoin.connect(QUOTE_KUCOIN_URL)
    quote_sock_kucoin.setsockopt_string(zmq.SUBSCRIBE, "")
    print("Subscribed to Kucoin quotes.")
    # === ZMQ PUSH setup (sends trade orders) ===
    context = zmq.Context()
    trade_sock = context.socket(zmq.PUSH)
    trade_sock.connect(TRADE_URL)

    print(f"Arbitrage Strategy listening for {SYMBOL} on multiple quote URLs and trade pub on {TRADE_URL}...")
    print("All setup!")

    while True:
        try:
            # Receive quotes from all exchanges
            msg_binance = quote_sock_binance.recv()
            bid_binance, ask_binance, symbol_binance_bytes = struct.unpack('!dd16s', msg_binance)
            symbol_binance = symbol_binance_bytes.split(b'\0', 1)[0].decode().strip()

            msg_cryptocoms = quote_sock_cryptocoms.recv()
            bid_cryptocoms, ask_cryptocoms, symbol_cryptocoms_bytes = struct.unpack('!dd16s', msg_cryptocoms)
            symbol_cryptocoms = symbol_cryptocoms_bytes.split(b'\0', 1)[0].decode().strip()
            
            msg_kraken = quote_sock_kraken.recv()
            bid_kraken, ask_kraken, symbol_kraken_bytes = struct.unpack('!dd16s', msg_kraken)
            symbol_kraken = symbol_kraken_bytes.split(b'\0', 1)[0].decode().strip()
          
            msg_kucoin = quote_sock_kucoin.recv()
            bid_kucoin, ask_kucoin, symbol_kucoin_bytes = struct.unpack('!dd16s', msg_kucoin)
            symbol_kucoin = symbol_kucoin_bytes.split(b'\0', 1)[0].decode().strip()
            
            print("Received Prices:")
            print(f"  Binance: Bid {bid_binance}, Ask {ask_binance}")
            print(f"  Cryptocoms: Bid {bid_cryptocoms}, Ask {ask_cryptocoms}")
            print(f"  Kraken: Bid {bid_kraken}, Ask {ask_kraken}")
            print(f"  Kucoin: Bid {bid_kucoin}, Ask {ask_kucoin}")

            # Simple arbitrage logic
            # Buy from the exchange with the lowest ask and sell to the one with the highest bid
            asks = {
                'binance': ask_binance,
                'cryptocoms': ask_cryptocoms,
                'kraken': ask_kraken,
                'kucoin': ask_kucoin
            }
            bids = {
                'binance': bid_binance,
                'cryptocoms': bid_cryptocoms,
                'kraken': bid_kraken,
                'kucoin': bid_kucoin
            }

            best_ask_exchange = min(asks, key=asks.get)
            best_bid_exchange = max(bids, key=bids.get)
            #print(f"Best Ask: {best_ask_exchange} at {asks[best_ask_exchange]:.2f}, Best Bid: {best_bid_exchange} at {bids[best_bid_exchange]:.2f}")

            if bids[best_bid_exchange] > asks[best_ask_exchange]:
                # Arbitrage opportunity detected
                print(f"Arbitrage Opportunity: Buy on {best_ask_exchange} at {asks[best_ask_exchange]} and Sell on {best_bid_exchange} at {bids[best_bid_exchange]}")
                # Send BUY order to best ask exchange
                #send_order(trade_sock, 'BUY', SYMBOL, asks[best_ask_exchange], STRATEGY_NAME)
                # Send SELL order to best bid exchange
                #send_order(trade_sock, 'SELL', SYMBOL, bids[best_bid_exchange], STRATEGY_NAME)
            else:
                print("No arbitrage opportunity detected.")        
        except Exception as e:
            print("Error:", e)

        time.sleep(0.1)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
                    prog='Strategy Arbitrage',
                    description='Arbitrage between multiple exchanges')

    parser.add_argument('--host', type=str, default=HOST, help='Host to connect to') 
    parser.add_argument('--backtest', action='store_true',
                    help='Set to True if connecting to backtester data feed.')

    args = parser.parse_args()

    if args.backtest == True:
        QUOTE_PORT = 5557  # Backtester data feed port
        QUOTE_URL = f"tcp://{HOST}:{QUOTE_PORT}"

        TRADE_PORT = 5558  # Backtester trade order port
        TRADE_URL = f"tcp://{HOST}:{TRADE_PORT}"

    run_strategy()