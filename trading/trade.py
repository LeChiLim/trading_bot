# trade_daemon/trade.py
import ccxt
import zmq
import json
import time
import os
import threading
from queue import Queue
from collections import deque
from dotenv import load_dotenv
load_dotenv()

# === CONFIG ===
API_KEY = os.getenv('BINANCE_TESTNET_KEY')
API_SECRET = os.getenv('BINANCE_TESTNET_SECRET')
SYMBOL = "XRP/USDT"
TEST_TRADE_SIZE_USD = 10 
TRADE_PORT = 5001  # Port for receiving trade orders from strategies
TRADE_URL = f"tcp://127.0.0.1:{TRADE_PORT}"
MAX_QUEUE_SIZE = 1000  # Maximum orders in queue
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

# === Order Queue ===
order_queue = Queue(maxsize=MAX_QUEUE_SIZE)

# === Trade Records ===
trade_records = deque(maxlen=10000)  # Keep last 10,000 trades in memory
total_trades_count = 0  # Total number of trades executed

# === ZMQ PULL socket (receives orders from strategies) ===
context = zmq.Context()
pull_sock = context.socket(zmq.PULL)
pull_sock.bind(TRADE_URL)
pull_sock.setsockopt(zmq.RCVTIMEO, 1000)  # 1 second timeout for non-blocking

print(f"Trade Daemon listening on {TRADE_URL}")
print(f"Will place ${TEST_TRADE_SIZE_USD} {SYMBOL} orders")
print(f"Max queue size: {MAX_QUEUE_SIZE}")
print("-" * 60)

def execute_order(order_data):
    """Execute a trade order on the exchange"""
    global total_trades_count
    
    try:
        order_type = order_data['order_type']
        symbol = order_data['symbol']
        price = order_data['price']
        strategy_name = order_data.get('strategy_name', 'unknown')
        
        # Calculate order amount based on USD size
        if order_type == 'BUY':
            amount = TEST_TRADE_SIZE_USD / price
            order = exchange.create_market_buy_order(symbol, amount)
            print(f"[{time.strftime('%H:%M:%S')}] BUY ORDER EXECUTED")
        elif order_type == 'SELL':
            # For SELL, we need to know how much we have, or use a fixed amount
            # This is simplified - you may want to track your position
            amount = TEST_TRADE_SIZE_USD / price
            order = exchange.create_market_sell_order(symbol, amount)
            print(f"[{time.strftime('%H:%M:%S')}] SELL ORDER EXECUTED")
        else:
            print(f"Unknown order type: {order_type}")
            return
        
        # Record the trade
        trade_record = {
            'timestamp': time.time(),
            'order_id': order['id'],
            'order_type': order_type,
            'symbol': symbol,
            'price': price,
            'amount': amount,
            'strategy_name': strategy_name,
            'status': order.get('status', 'unknown')
        }
        
        trade_records.append(trade_record)
        total_trades_count += 1
        
        print(f"  Order ID: {order['id']}")
        print(f"  Strategy: {strategy_name}")
        print(f"  Symbol: {symbol}")
        print(f"  Type: {order_type}")
        print(f"  Amount: {amount:.6f}")
        print(f"  Price: ${price:.6f}")
        print(f"  Total Trades: {total_trades_count}")
        print("-" * 60)
        
        return trade_record
        
    except Exception as e:
        print(f"[{time.strftime('%H:%M:%S')}] ERROR executing order: {e}")
        print(f"  Order data: {order_data}")
        return None

def process_order_queue():
    """Process orders from the queue"""
    while True:
        try:
            # Get order from queue (blocks until available)
            order_data = order_queue.get(timeout=1)
            execute_order(order_data)
            order_queue.task_done()
        except:
            # Timeout - continue loop
            continue

# Start order processing thread
processing_thread = threading.Thread(target=process_order_queue, daemon=True)
processing_thread.start()

print("Order processing thread started...")
print("Waiting for orders from strategies...\n")

# Main loop: receive orders and add to queue
while True:
    try:
        # Receive order from strategy (non-blocking with timeout)
        msg = pull_sock.recv_string()
        order_data = json.loads(msg)
        
        # Add to queue (will block if queue is full)
        try:
            order_queue.put(order_data, timeout=1)
            queue_size = order_queue.qsize()
            strategy_name = order_data.get('strategy_name', 'unknown')
            print(f"[{time.strftime('%H:%M:%S')}] Order received from {strategy_name}: {order_data['order_type']} {order_data['symbol']} @ ${order_data['price']:.6f} | Queue: {queue_size}/{MAX_QUEUE_SIZE}")
        except Exception as queue_error:
            strategy_name = order_data.get('strategy_name', 'unknown') if 'order_data' in locals() else 'unknown'
            print(f"[{time.strftime('%H:%M:%S')}] WARNING: Order queue full! Dropping order from {strategy_name}")
            
    except zmq.Again:
        # Timeout - no message received, continue loop
        continue
    except KeyboardInterrupt:
        print("\n\nTrade Daemon stopped.")
        print(f"Total trades executed: {total_trades_count}")
        print(f"Recent trades in memory: {len(trade_records)}")
        pull_sock.close()
        context.term()
        break
    except Exception as e:
        print(f"[{time.strftime('%H:%M:%S')}] Error receiving order: {e}")
        time.sleep(1)