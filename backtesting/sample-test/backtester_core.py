import zmq
import json
import time
import os
import threading
from queue import Queue
from collections import deque
import pandas as pd
import numpy as np
from dotenv import load_dotenv
load_dotenv()

# === CONFIG ===
SYMBOL = "BTC/USD"
TEST_TRADE_SIZE_USD = 10 
TRADE_PORT = 5558
TRADE_URL = f"tcp://127.0.0.1:{TRADE_PORT}"
MAX_QUEUE_SIZE = 1000

# === Backtest Mode - No real exchange ===
print("BACKTEST MODE - No real trades executed")
print(f"Listening on {TRADE_URL} for strategy orders")
print(f"Trade size: ${TEST_TRADE_SIZE_USD} {SYMBOL}")
print("-" * 60)

# === Trade Records (for metrics) ===
trades_df = pd.DataFrame(columns=[
    'timestamp', 'strategy_name', 'symbol', 'order_type', 
    'entry_price', 'amount', 'exit_price', 'exit_time', 
    'pnl_pct', 'pnl_usd'
])
total_trades_count = 0
current_positions = {}  # Track open positions: {symbol: {'entry_price': x, 'amount': y, 'strategy': z}}

# === ZMQ PULL socket ===
context = zmq.Context()
pull_sock = context.socket(zmq.PULL)
pull_sock.bind(TRADE_URL)
pull_sock.setsockopt(zmq.RCVTIMEO, 1000)

order_queue = Queue(maxsize=MAX_QUEUE_SIZE)

def simulate_execution(order_data):
    """Simulate trade execution and track position"""
    global total_trades_count
    
    try:
        order_type = order_data['order_type']
        symbol = order_data['symbol']
        price = order_data['price']
        strategy_name = order_data.get('strategy_name', 'unknown')
        
        amount = TEST_TRADE_SIZE_USD / price
        
        timestamp = time.time()
        
        if order_type == 'BUY':
            # Open long position
            current_positions[symbol] = {
                'entry_price': price,
                'amount': amount,
                'strategy': strategy_name,
                'entry_time': timestamp
            }
            print(f"[{time.strftime('%H:%M:%S')}] 📈 LONG {symbol} @ ${price:.6f} | Pos: {amount:.6f}")
            
        elif order_type == 'SELL':
            # Close long position (or open short - simplified)
            if symbol in current_positions:
                pos = current_positions[symbol]
                entry_price = pos['entry_price']
                entry_amount = pos['amount']
                
                # Calculate P&L
                pnl_pct = (price - entry_price) / entry_price * 100
                pnl_usd = (price - entry_price) * entry_amount
                
                # Record completed trade
                trade_record = {
                    'timestamp': timestamp,
                    'strategy_name': strategy_name,
                    'symbol': symbol,
                    'order_type': 'CLOSE_LONG',
                    'entry_price': entry_price,
                    'amount': entry_amount,
                    'exit_price': price,
                    'exit_time': timestamp,
                    'pnl_pct': pnl_pct,
                    'pnl_usd': pnl_usd
                }
                trades_df.loc[len(trades_df)] = trade_record
                total_trades_count += 1
                
                del current_positions[symbol]
                print(f"[{time.strftime('%H:%M:%S')}] ✅ CLOSED {symbol} | P&L: {pnl_pct:+.2f}% (${pnl_usd:+.2f}) | Total: {total_trades_count}")
            else:
                print(f"[{time.strftime('%H:%M:%S')}] ⚠️  No position to close: {symbol}")
                
        print("-" * 60)
        
    except Exception as e:
        print(f"ERROR simulating trade: {e}")

def process_order_queue():
    """Process orders from queue"""
    while True:
        try:
            order_data = order_queue.get(timeout=1)
            simulate_execution(order_data)
            order_queue.task_done()
        except:
            continue

# Start processing thread
processing_thread = threading.Thread(target=process_order_queue, daemon=True)
processing_thread.start()

print("Backtest processor started...")
print("Waiting for strategy orders...\n")

# Main receive loop
while True:
    try:
        msg = pull_sock.recv_string()
        order_data = json.loads(msg)
        
        try:
            order_queue.put(order_data, timeout=1)
            queue_size = order_queue.qsize()
            print(f"[{time.strftime('%H:%M:%S')}] 📨 Order queued: {order_data['order_type']} {order_data['symbol']} | Q: {queue_size}")
        except:
            print(f"[{time.strftime('%H:%M:%S')}] ⚠️ Queue full - dropping order")
            
    except zmq.Again:
        continue
    except KeyboardInterrupt:
        break
    except Exception as e:
        print(f"Receive error: {e}")
        time.sleep(0.1)

# === COMPUTE METRICS on shutdown ===
print("\n" + "="*70)
print("BACKTEST RESULTS")
print("="*70)

if len(trades_df) > 0:
    completed_trades = trades_df['pnl_pct']
    winning_trades = completed_trades > 0
    total_trades = len(completed_trades)
    
    # Basic metrics
    win_rate = len(winning_trades[winning_trades]) / total_trades * 100
    avg_profit_per_trade = completed_trades.mean()
    avg_winner = completed_trades[winning_trades].mean() if len(winning_trades[winning_trades]) > 0 else 0
    avg_loser = completed_trades[~winning_trades].mean() if len(completed_trades[~winning_trades]) > 0 else 0
    
    # Sharpe (simplified - assumes 1-min bars)
    returns = completed_trades / 100  # Convert to decimal
    sharpe_ratio = (returns.mean() / returns.std() * np.sqrt(525600)) if returns.std() > 0 else 0
    
    total_pnl_usd = trades_df['pnl_usd'].sum()
    
    print(f"Total trades:      {total_trades}")
    print(f"Win rate:          {win_rate:.1f}%")
    print(f"Avg P&L/trade:     {avg_profit_per_trade:.2f}%")
    print(f"Avg winner:        {avg_winner:.2f}%")
    print(f"Avg loser:         {avg_loser:.2f}%")
    print(f"Profit factor:     {abs(avg_winner/avg_loser):.2f}" if avg_winner != 0 and avg_loser != 0 else "N/A")
    print(f"Sharpe ratio:      {sharpe_ratio:.2f}")
    print(f"Total P&L:         ${total_pnl_usd:.2f}")
else:
    print("No trades completed")

print(f"Open positions: {len(current_positions)}")
print("="*70)

# Cleanup
pull_sock.close()
context.term()
