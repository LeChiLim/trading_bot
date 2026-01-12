# Add a function to add trades to a PostgreSQL database
import psycopg2
import datetime
from typing import Dict, Any

def insert_trade(conn, trade_record: Dict[str, Any]):
    cur = conn.cursor()
    timestamp_dt = datetime.datetime.fromtimestamp(
            trade_record['timestamp']
        )
    try:
        cur.execute("""
            INSERT INTO trades (
                timestamp, order_id, order_type, symbol, price, 
                    order_size, side, fee, exchange, status, strategy_name
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            timestamp_dt,
            trade_record['order_id'],
            trade_record['order_type'],
            trade_record['symbol'],
            trade_record['price'],
            trade_record['order_size'],
            trade_record['side'],
            trade_record['fee'],
            trade_record['exchange'],
            trade_record['status'],
            trade_record['strategy_name']
        ))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error inserting trade: {e}")
        conn.rollback()
        return False

DB_NAME="postgres"
DB_USER="postgres"
DB_PASS="password"
DB_HOST="100.127.11.87"
DB_PORT=5433

conn = psycopg2.connect(database=DB_NAME,
                            user=DB_USER,
                            password=DB_PASS,
                            host=DB_HOST,
                            port=DB_PORT)

print("Database connected successfully")

#example usage
trade_record = {
    'timestamp': 1625247600,
    'order_id': '12345',
    'order_type': 'BUY',
    'symbol': 'XRP/USDT',
    'price': 0.75,
    'order_size': 100,
    'side': 'LONG',
    'fee': 0.001,
    'exchange': 'Binance',
    'status': 'COMPLETED',
    'strategy_name': 'MeanReversion'
}

insert_trade(conn, trade_record)

    