Trading Bot Utilities
=====================

This workspace contains small tools for quoting Binance spot prices via `pynng`.

Setup
-----
- Install dependencies in a virtualenv (Python 3.12):
  ```
  python3 -m venv venv
  source venv/bin/activate
  pip install -r requirements.txt
  ```

Trading Daemon
---------
- File: `trading/trade.py`
- Sample order test to binance test vision api.
- Before running:

Go to https://testnet.binance.vision/
Login
Copy API keys to /trading/.env

- Run:
  ```
  python3 quoting/quote.py
  ```

Quoting Daemon
---------
- File: `quoting/quote.py`
- Broadcasts BTC/USDT bid/ask/last over `tcp://127.0.0.1:5000`.
- Run:
  ```
  python3 quoting/quote.py
  ```

Subscriber
----------
- File: `tools/subscriber.py`
- Connects to the publisher and prints formatted quotes.
- Run in a second terminal while the publisher is active:
  ```
  python3 quoting/subscriber.py
  ```

Notes
-----
- Multicast UDP is *not* enabled in the default pynng builds; this setup relies on local TCP pub/sub.
- Adjust symbol, host, or port by editing the constants at the top of each script.

