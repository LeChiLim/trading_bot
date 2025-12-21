import zmq
import json
import numpy as np
import pandas as pd
import os
import time
import struct

#just data out to 5557

#config ports
context = zmq.Context()
pub_socket = context.socket(zmq.PUB)
pub_socket.bind("tcp://*:5557")  # Signals back to backtester


#import data
PROJ_PATH = "/home/asus_laptop/projects/trading_bot/"
DATAFILE_PATH = os.path.join(
    PROJ_PATH,
    "data", "btcusd",
    "btcusd-m1-bid-2025-03-19-2025-12-18T08-48.csv",
)

# load data
print("Loading data from:", DATAFILE_PATH)
df = pd.read_csv(DATAFILE_PATH)

# timestamp to datetime and index
df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
df = df.set_index("timestamp")

# simulate bid/ask from mid
avg_spread_pct = 0.00005     # 0.005%
std_spread_pct = 0.00025     # 0.025%

df["mid"] = (df["open"] + df["close"]) / 2

spread_pct = np.clip(
    np.random.normal(avg_spread_pct, std_spread_pct, size=len(df)),
    0,
    None,
)

mid = df["mid"].to_numpy()
half_spread = mid * spread_pct / 2

df["bid"] = (mid - half_spread).round(2)
df["ask"] = (mid + half_spread).round(2)

# time to send data
SYMBOL = "BTC/USD"  # or whatever you want, padded to 16 bytes like ccxt script

print(f"Replaying {len(df)} rows over tcp://*:5557 as bid/ask stream...")

try:
    for idx, row in df.iterrows():
        bid = float(row["bid"])
        ask = float(row["ask"])
        ts  = idx.timestamp()  # float UNIX timestamp

        # pack: bid (double), ask (double), timestamp (double), symbol (16-byte string)
        msg = struct.pack(
            "!ddd16s",
            bid,
            ask,
            ts,
            SYMBOL.encode().ljust(16, b"\0")
        )
        pub_socket.send(msg)
        # Optional: slow down so it looks like a live feed
        time.sleep(1)

        # Optional: print occasionally
        # print(f"{idx}  bid={bid:.2f} ask={ask:.2f}")

except KeyboardInterrupt:
    print("\nReplay stopped by user.")

# 

pub_socket.close()
context.term()
