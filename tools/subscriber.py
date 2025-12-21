import struct
import time

import zmq

# Configuration should match the publisher
HOST = 'localhost'
PORT = 5557
URL = f"tcp://{HOST}:{PORT}"

if __name__ == '__main__':
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
