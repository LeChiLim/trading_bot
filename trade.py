import ccxt
import os
import time
from decimal import Decimal

# Configuration
SYMBOL = 'BTC/USDT'
TESTNET = True  # Use Binance testnet

# API credentials from environment variables
API_KEY = os.getenv('BINANCE_API_KEY', '')
API_SECRET = os.getenv('BINANCE_API_SECRET', '')

def get_exchange():
    """Initialize and return Binance exchange (testnet or mainnet)"""
    options = {
        'enableRateLimit': True,
        'adjustForTimeDifference': True,
    }
    
    if TESTNET:
        # Binance testnet configuration
        exchange = ccxt.binance({
            'apiKey': API_KEY,
            'secret': API_SECRET,
            'options': {
                'defaultType': 'spot',  # spot, future, delivery
            },
            'sandbox': True,  # Enable testnet
            **options
        })
        print("Using Binance TESTNET")
    else:
        exchange = ccxt.binance({
            'apiKey': API_KEY,
            'secret': API_SECRET,
            'options': {
                'defaultType': 'spot',
            },
            **options
        })
        print("Using Binance MAINNET")
    
    return exchange

def get_balance(exchange, currency='USDT'):
    """Get balance for a specific currency"""
    try:
        balance = exchange.fetch_balance()
        free = balance.get(currency, {}).get('free', 0)
        used = balance.get(currency, {}).get('used', 0)
        total = balance.get(currency, {}).get('total', 0)
        print(f"{currency} Balance: Free={free}, Used={used}, Total={total}")
        return free
    except Exception as e:
        print(f"Error fetching balance: {e}")
        return None

def place_market_buy_order(exchange, symbol, amount):
    """Place a market buy order"""
    try:
        print(f"\nPlacing MARKET BUY order: {amount} {symbol}")
        order = exchange.create_market_buy_order(symbol, amount)
        print(f"Order placed successfully!")
        print(f"Order ID: {order['id']}")
        print(f"Status: {order['status']}")
        print(f"Filled: {order.get('filled', 'N/A')}")
        return order
    except Exception as e:
        print(f"Error placing market buy order: {e}")
        return None

def place_market_sell_order(exchange, symbol, amount):
    """Place a market sell order"""
    try:
        print(f"\nPlacing MARKET SELL order: {amount} {symbol}")
        order = exchange.create_market_sell_order(symbol, amount)
        print(f"Order placed successfully!")
        print(f"Order ID: {order['id']}")
        print(f"Status: {order['status']}")
        print(f"Filled: {order.get('filled', 'N/A')}")
        return order
    except Exception as e:
        print(f"Error placing market sell order: {e}")
        return None

def place_limit_buy_order(exchange, symbol, amount, price):
    """Place a limit buy order"""
    try:
        print(f"\nPlacing LIMIT BUY order: {amount} {symbol} @ {price}")
        order = exchange.create_limit_buy_order(symbol, amount, price)
        print(f"Order placed successfully!")
        print(f"Order ID: {order['id']}")
        print(f"Status: {order['status']}")
        return order
    except Exception as e:
        print(f"Error placing limit buy order: {e}")
        return None

def place_limit_sell_order(exchange, symbol, amount, price):
    """Place a limit sell order"""
    try:
        print(f"\nPlacing LIMIT SELL order: {amount} {symbol} @ {price}")
        order = exchange.create_limit_sell_order(symbol, amount, price)
        print(f"Order placed successfully!")
        print(f"Order ID: {order['id']}")
        print(f"Status: {order['status']}")
        return order
    except Exception as e:
        print(f"Error placing limit sell order: {e}")
        return None

def get_ticker(exchange, symbol):
    """Get current ticker price"""
    try:
        ticker = exchange.fetch_ticker(symbol)
        return ticker
    except Exception as e:
        print(f"Error fetching ticker: {e}")
        return None

def cancel_order(exchange, symbol, order_id):
    """Cancel an order"""
    try:
        result = exchange.cancel_order(order_id, symbol)
        print(f"Order {order_id} cancelled: {result['status']}")
        return result
    except Exception as e:
        print(f"Error cancelling order: {e}")
        return None

def get_open_orders(exchange, symbol):
    """Get all open orders for a symbol"""
    try:
        orders = exchange.fetch_open_orders(symbol)
        print(f"\nOpen orders for {symbol}: {len(orders)}")
        for order in orders:
            print(f"  ID: {order['id']}, Side: {order['side']}, Amount: {order['amount']}, "
                  f"Price: {order.get('price', 'Market')}, Status: {order['status']}")
        return orders
    except Exception as e:
        print(f"Error fetching open orders: {e}")
        return []

if __name__ == '__main__':
    # Check if API keys are set
    if not API_KEY or not API_SECRET:
        print("ERROR: API keys not found!")
        print("Please set environment variables:")
        print("  export BINANCE_API_KEY='your_testnet_api_key'")
        print("  export BINANCE_API_SECRET='your_testnet_api_secret'")
        print("\nGet testnet API keys from: https://testnet.binance.vision/")
        exit(1)
    
    # Initialize exchange
    exchange = get_exchange()
    
    print(f"\n{'='*60}")
    print(f"Binance Trading Bot - {SYMBOL}")
    print(f"{'='*60}\n")
    
    # Test connection and get balance
    print("1. Checking connection and balance...")
    usdt_balance = get_balance(exchange, 'USDT')
    btc_balance = get_balance(exchange, 'BTC')
    
    # Get current price
    print("\n2. Fetching current market price...")
    ticker = get_ticker(exchange, SYMBOL)
    if ticker:
        print(f"Current {SYMBOL} price:")
        print(f"  Bid: {ticker['bid']}")
        print(f"  Ask: {ticker['ask']}")
        print(f"  Last: {ticker['last']}")
    
    # Example: Place a small test order (uncomment to test)
    # WARNING: This will place a real order on testnet!
    print("\n3. Example order placement (commented out for safety)")
    print("   Uncomment the code below to place test orders")
    
    # Example 1: Place a small market buy order (0.001 BTC)
    # if usdt_balance and usdt_balance > 10:
    #     amount = 0.001  # Buy 0.001 BTC
    #     place_market_buy_order(exchange, SYMBOL, amount)
    #     time.sleep(2)
    #     get_balance(exchange, 'USDT')
    #     get_balance(exchange, 'BTC')
    
    # Example 2: Place a limit buy order below market price
    # if ticker and usdt_balance and usdt_balance > 10:
    #     limit_price = ticker['bid'] * 0.99  # 1% below current bid
    #     amount = 0.001
    #     place_limit_buy_order(exchange, SYMBOL, amount, limit_price)
    #     time.sleep(2)
    #     get_open_orders(exchange, SYMBOL)
    
    # Example 3: Place a limit sell order above market price
    # if ticker and btc_balance and btc_balance > 0.001:
    #     limit_price = ticker['ask'] * 1.01  # 1% above current ask
    #     amount = 0.001
    #     place_limit_sell_order(exchange, SYMBOL, amount, limit_price)
    #     time.sleep(2)
    #     get_open_orders(exchange, SYMBOL)
    
    print("\n" + "="*60)
    print("Script completed. Check your testnet account for results.")
    print("="*60)

