import struct
import time

import pynng

# Configuration should match the publisher
HOST = '127.0.0.1'
PORT = 5000
URL = f"tcp://{HOST}:{PORT}"

if __name__ == '__main__':
    sub = pynng.Sub0()
    sub.dial(URL)
    sub.subscribe(b'')  # subscribe to everything

    print("Listening for quotes...")
    print("-" * 40)

    while True:
        try:
            msg = sub.recv()
            bid, ask, symbol_bytes = struct.unpack('!dd16s', msg)
            symbol = symbol_bytes.decode().rstrip('\0')
            ts = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
            print(f"[{ts}] {symbol}: bid={bid:.2f} ask={ask:.2f}")
        except KeyboardInterrupt:
            print("\nStopped.")
            break
        except Exception as exc:
            print("Error receiving data:", exc)
            time.sleep(0.5)
