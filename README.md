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

Strategy: Dual EMA
------------------
- File: `strategies/strategy_dual_ema.py`
- Listens to bid/ask quotes, maintains two EMAs (e.g. 9/25), and sends trade signals to the trading daemon via ZMQ.
- Edit the `SYMBOL`, `EMA_FAST`, and `EMA_SLOW` parameters at the top of the script as needed.

How it Works:
  - Receives bid/ask/symbol binary quotes on `tcp://127.0.0.1:5000`.
  - Computes two EMAs (fast and slow) to detect crossovers.
  - When the fast EMA crosses above the slow EMA, sends a BUY order to the trading daemon; when it crosses below, sends a SELL order.
  - Sends JSON order messages via ZMQ PUSH to `tcp://127.0.0.1:5001`.

To run:
  ```
  python3 strategies/strategy_dual_ema.py
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

