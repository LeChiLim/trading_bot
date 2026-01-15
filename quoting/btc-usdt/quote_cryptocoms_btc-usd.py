import ccxt
import zmq
import time
import json
import struct

# Config
SYMBOL = 'BTC/USDT'
HOST = '127.0.0.1'
PORT = 5002
URL = f"tcp://{HOST}:{PORT}"

# Initialize cryptocom (public data only)
exchange = ccxt.cryptocom({
    'enableRateLimit': True,  # Be nice to the API
})

# zmq pub socket
context = zmq.Context()
sock = context.socket(zmq.PUB)
sock.bind(URL)
sock.setsockopt(zmq.SNDTIMEO, 100)

print(f"Crypto.com {SYMBOL} Live Price Tracker")
print("-" * 50)
print(f"Publishing {SYMBOL} to {HOST}:{PORT}")

while True:
    try:
        ticker = exchange.fetch_ticker(SYMBOL)
        data = {
            'symbol': SYMBOL,
            'bid': ticker['bid'],
            'ask': ticker['ask'],
            'last': ticker['last'],
            'timestamp': time.time()
        }
        # Send as compact binary (faster than JSON)
        msg = struct.pack('!dd16s', data['bid'], data['ask'], data['symbol'].encode().ljust(16, b'\0'))
        sock.send(msg, zmq.NOBLOCK)
        print(f"Sent: bid={data['bid']:.6f} ask={data['ask']:.6f} symbol={data['symbol']}")
    except Exception as e:
        print("Error:", e)
    
    time.sleep(0.1) 
