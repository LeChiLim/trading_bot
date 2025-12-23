import struct
import time
import argparse
import zmq

# Configuration should match the publisher
HOST = 'localhost'
PORT = 5001

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
                    prog='Subscriber Tool',
                    description='Subscribe to any zmq host and port.')

    parser.add_argument('--host', type=str, default=HOST, help='Host to connect to')     
    parser.add_argument('--port', type=int, default=PORT, help='Port to connect to')   
    parser.add_argument('--backtest', type=bool, default=False,
                    help='Set to True if connecting to backtester data feed.')

    args = parser.parse_args()

    if args.backtest == True:
        PORT = 5557  # Backtester data feed port

    URL = f"tcp://{HOST}:{PORT}"

    context = zmq.Context()
    sub = context.socket(zmq.SUB)
    sub.connect(URL)
    sub.setsockopt(zmq.SUBSCRIBE, b'')  # subscribe to everything

    print("Listening for quotes...")
    print("-" * 40)

    while True:
        try:
            msg = sub.recv()
            bid, ask, ts, symbol_bytes = struct.unpack('!ddd16s', msg)
            symbol = symbol_bytes.decode().rstrip('\0')
            ts = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
            print(f"[{ts}] {symbol}: bid={bid:.2f} ask={ask:.2f}")
        except KeyboardInterrupt:
            print("\nStopped.")
            break
        except Exception as exc:
            print("Error receiving data:", exc)
            time.sleep(0.5)
