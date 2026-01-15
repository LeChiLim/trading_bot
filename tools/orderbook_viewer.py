#!/usr/bin/env python3
"""
Binance BTC/USDT Order Book Sample - CCXT
Real-time + REST snapshots for market making
"""

import ccxt
import time
from pprint import pprint

# Initialize Binance (use sandbox for testing)
exchange = ccxt.binance({
    'sandbox': True,  # Testnet - change to False for live
    'enableRateLimit': True,
})

symbol = 'BTC/USDT'

def print_rest_orderbook():
    """REST snapshot - perfect for backtesting"""
    print("\n" + "="*60)
    print("REST ORDER BOOK SNAPSHOT (Top 5000 levels)")
    print("="*60)
    
    orderbook = exchange.fetch_order_book(symbol, limit=5000)
    
    print(f"💰 SYMBOL: {symbol}")
    print(f"📊 SPREAD: ${orderbook['asks'][0][0] - orderbook['bids'][0][0]:.2f}")
    print(f"🎯 MID PRICE: ${((orderbook['bids'][0][0] + orderbook['asks'][0][0])/2):.2f}")
    
    print("\nBIDS (Buyers - Green)")
    print("Price\t\tSize")
    for i, bid in enumerate(orderbook['bids'][:10]):
        price, size = bid
        print(f"🟢 ${price:>8.2f}\t{size:>8.4f} BTC")
    
    print("\nASKS (Sellers - Red)") 
    print("Price\t\tSize")
    for i, ask in enumerate(orderbook['asks'][:10]):
        price, size = ask
        print(f"🔴 ${price:>8.2f}\t{size:>8.4f} BTC")

def print_websocket_orderbook():
    """Live WebSocket stream - perfect for market making"""
    print("\n" + "="*60)
    print("LIVE WEBSOCKET ORDER BOOK (Press Ctrl+C to stop)")
    print("="*60)
    
    while True:
        try:
            orderbook = exchange.watch_order_book(symbol, limit=10)
            best_bid = orderbook['bids'][0]
            best_ask = orderbook['asks'][0]
            
            print(f"\r🟢 Bid: ${best_bid[0]:>8.2f} x {best_bid[1]:>6.4f} | 🔴 Ask: ${best_ask[0]:>8.2f} x {best_ask[1]:>6.4f} | 📊 Spread: ${best_ask[0]-best_bid[0]:>5.2f}", end='', flush=True)
            
        except KeyboardInterrupt:
            print("\nStopped.")
            break
        except Exception as e:
            print(f"\nError: {e}")
            time.sleep(1)

if __name__ == "__main__":
    print("🚀 Binance BTC/USDT Order Book Demo")
    print("1. REST Snapshot (Backtesting)")
    print("2. Live WebSocket (Market Making)")
    
    choice = input("\nChoose (1/2): ")
    
    if choice == "1":
        print_rest_orderbook()
    else:
        print_websocket_orderbook()
    
    #exchange.close()  # Clean shutdown
