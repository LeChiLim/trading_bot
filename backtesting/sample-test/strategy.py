import zmq
import json
import pandas as pd
import pandas_ta_classic as ta
import signal
import sys

# Data in from :5556
# Signals out to :5558


def signal_handler(sig, frame):
    print("\nShutting down strategy...")
    sub_socket.close()
    pub_socket.close()
    context.term()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

context = zmq.Context()
sub_socket = context.socket(zmq.SUB)
sub_socket.connect("tcp://localhost:5556")  # Data IN
sub_socket.setsockopt_string(zmq.SUBSCRIBE, "")

pub_socket = context.socket(zmq.PUB)
pub_socket.connect("tcp://localhost:5558")  # Signals OUT

print("Strategy ready. Waiting for data chunks...")

all_signals = []
try:
    while True:
        message = sub_socket.recv_string()
        data = json.loads(message)
        if data["type"] == "data_chunk":
            df_chunk = pd.DataFrame(data["data"])
            df_chunk["timestamp"] = pd.to_datetime(df_chunk["timestamp"])
            df_chunk.set_index("timestamp", inplace=True)
            
            # EMA strategy
            df_chunk.ta.ema(9, append=True)
            df_chunk.ta.ema(25, append=True)
            df_chunk["signal"] = 0
            df_chunk.loc[df_chunk["EMA_9"] > df_chunk["EMA_25"], "signal"] = 1
            df_chunk.loc[df_chunk["EMA_9"] < df_chunk["EMA_25"], "signal"] = -1
            
            signals = df_chunk[["signal", "bid", "ask", "mid"]].reset_index().to_dict('records')
            pub_socket.send_string(json.dumps({
                "type": "signals",
                "chunk_id": data["chunk_id"],
                "signals": signals
            }))
            print(f"Processed chunk {data['chunk_id']}")
            
except KeyboardInterrupt:
    pass
finally:
    sub_socket.close()
    pub_socket.close()
    context.term()
