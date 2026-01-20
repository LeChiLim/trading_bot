# 🤖 Crypto Trading Bot

> A study on production-grade cryptocurrency trading system with live trading, backtesting, and strategy optimization capabilities for multiple crypto exchanges.

[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 📋 Table of Contents

- [Overview](#-overview)
- [Features](#-features)
- [Architecture](#-architecture)
- [Prerequisites](#-prerequisites)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Usage](#-usage)
  - [Live Trading](#live-trading)
  - [Backtesting](#backtesting)
- [Components](#-components)
- [Strategies](#-strategies)
- [Tools](#-tools)
- [Database](#-database)
- [Contributing](#-contributing)
- [Disclaimer](#-disclaimer)
- [License](#-license)

## 🎯 Overview

This trading bot is designed to replicate production-level trading infrastructure with a focus on learning and experimentation. It integrates with ccxt's API to execute automated trading strategies while providing comprehensive backtesting capabilities to validate strategies before deploying them live.

The system is built with a microservices architecture, separating concerns between market data streaming, strategy execution, and order management.

## ✨ Features

### Live Trading
- **Real-time Market Data**: Subscribe to live BTC/USDT bid/ask quotes via ZMQ
- **Automated Order Execution**: Place market and limit orders on different exchanges with ccxt
- **Strategy Engine**: Modular strategy framework supporting multiple concurrent strategies
- **Risk Management**: Position tracking and trade history storage

### Backtesting
- **Historical Data Support**: Test strategies against historical market data
- **Strategy Validation**: Validate strategy performance before live deployment
- **Performance Metrics**: Analyze trade statistics and profitability

### Infrastructure
- **ZMQ Messaging**: High-performance inter-process communication
- **PostgreSQL + TimescaleDB**: Time-series optimized trade data storage
- **Binance Integration**: Full API connectivity for testnet and production environments

## 🏗️ Architecture

```



┌──────────────────┐
│       ccxt       │
│  binance, kraken |
|  cryptocoms      │
└──────────────────┘
        │                            
        │ Market Data               
        │                            
        ▼ 
┌─────────────────┐         ┌──────────────────┐
│  Quoting Service│────────▶│  Strategy Engine │
│   (quote.py)    │  ZMQ    │ (strategy_*.py)  │
└─────────────────┘         └──────────────────┘
        │                            │
        │ Market Data                │ Signals
        │                            │
        ▼                            ▼
┌─────────────────┐         ┌──────────────────┐
│  Subscriber     │         │ Trading Service  │
│ (subscriber.py) │         │   (trade.py)     │
└─────────────────┘         └──────────────────┘
                                     │
                                     ▼
                            ┌──────────────────┐
                            │  Binance API     │
                            │  + PostgreSQL    │
                            └──────────────────┘
```

**Communication Flows:**
- **Quoting Service** → Broadcasts market data on `tcp://127.0.0.1:5001`
- **Strategy Engine** → Sends trade signals to `tcp://127.0.0.1:6001`
- **Trading Service** → Executes orders via Binance API and stores in database

## 🔧 Prerequisites

- **Python**: 3.12 or higher
- **PostgreSQL**: 18+ with TimescaleDB extension
- **Binance Account**: For API access (testnet recommended for development)
- **Git**: For cloning the repository

## 📦 Installation

### 1. Clone the Repository

```bash
git clone https://github.com/LeChiLim/trading_bot.git
cd trading_bot
```

### 2. Set Up Python Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Set Up PostgreSQL with TimescaleDB

Follow the [TimescaleDB installation guide](https://www.tigerdata.com/docs/self-hosted/latest/install/installation-docker) for Docker deployment.

### 4. Configure Binance API For Testing

1. Go to [Binance Testnet](https://testnet.binance.vision/)
2. Create an account and generate API keys
3. Create a `.env` file in the `trading/` directory:

```bash
cd trading
touch .env
```

Add your credentials to `.env`:

```env
BINANCE_API_KEY=your_api_key_here
BINANCE_API_SECRET=your_api_secret_here
BINANCE_TESTNET=true
```

## ⚙️ Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `BINANCE_API_KEY` | Your Binance API key | Yes |
| `BINANCE_API_SECRET` | Your Binance API secret | Yes |
| `BINANCE_TESTNET` | Use testnet (true/false) | Yes |
| `DATABASE_URL` | PostgreSQL connection string | Yes |

### Strategy Parameters

Edit strategy files in `strategies/` to configure:
- Trading symbol (e.g., `BTCUSDT`)
- Technical indicator parameters (EMA periods, RSI thresholds, etc.)
- Position sizing
- Risk limits

## 🚀 Usage

### Live Trading

#### 1. Start the Quoting Service

The quoting service broadcasts real-time market data.

```bash
python3 quoting/quote.py
```

**Output**: Streams BTC/USDT bid/ask/last prices on `tcp://127.0.0.1:5001`

#### 2. Start the Trading Service

The trading service listens for signals and executes orders.

```bash
python3 trading/trade.py
```

**Features**:
- Connects to Binance API
- Listens for trade signals on `tcp://127.0.0.1:5001`
- Executes orders and logs to database

#### 3. Launch a Strategy

Start your chosen strategy to generate trading signals.

```bash
python3 strategies/strategy_dual_ema.py
```

**Strategy: Dual EMA Crossover**
- **Fast EMA**: 9 periods (default)
- **Slow EMA**: 25 periods (default)
- **Buy Signal**: When fast EMA crosses above slow EMA
- **Sell Signal**: When fast EMA crosses below slow EMA

#### 4. Monitor Activity (Optional)

Use the subscriber tool to view live market data.

```bash
python3 tools/subscriber.py
```

### Backtesting

Backtesting allows you to test strategies against historical data without risking capital.

#### 1. Prepare Historical Data

Use the [Backtest Manager VS Code extension](https://marketplace.visualstudio.com/items?itemName=woung717.backtest-manager) to download historical OHLCV data from various exchanges.

Store data in: `data/btcusd/` or appropriate symbol directory

#### 2. Run Data Preparation

```bash
python3 backtesting/data_prep.py
```

Simulates quoting service using historical data.

#### 3. Execute Strategy in Backtest Mode

```bash
python3 strategies/strategy_dual_ema.py --backtest
```

The `--backtest` flag modifies ports to avoid conflicts with live services.

#### 4. Analyze Results

Results are collected by `backtesting/backtester_core.py` and can be analyzed for:
- Win/loss ratio
- Total profit/loss
- Maximum drawdown
- Trade frequency

## 🧩 Components

### Quoting Service (`quoting/quote.py`)

**Purpose**: Real-time market data distribution

**Features**:
- Connects to Binance WebSocket API
- Publishes bid/ask/last prices via ZMQ PUB socket
- Supports multiple trading pairs

**Port**: `tcp://127.0.0.1:5000`

### Trading Service (`trading/trade.py`)

**Purpose**: Order execution and management

**Features**:
- Receives trade signals via ZMQ PULL socket
- Executes market/limit orders on Binance
- Stores trade history in PostgreSQL
- Error handling and retry logic

**Port**: Listens on `tcp://127.0.0.1:5001`

### Strategy Engine (`strategies/`)

**Purpose**: Generate trading signals based on technical analysis

**Current Strategies**:
- **Dual EMA Crossover** (`strategy_dual_ema.py`): Moving average crossover strategy
- _(Add more strategies as developed)_

**Customization**:
- Adjust indicator parameters in strategy files
- Implement custom strategies by extending base strategy class
- Combine multiple indicators for complex signals

## 📊 Strategies

### Dual EMA Strategy

**File**: `strategies/strategy_dual_ema.py`

**Logic**:
1. Calculate fast EMA (default: 9 periods)
2. Calculate slow EMA (default: 25 periods)
3. Generate signals:
   - **BUY**: Fast EMA crosses above slow EMA
   - **SELL**: Fast EMA crosses below slow EMA

**Configuration**:
```python
SYMBOL = "BTCUSDT"
EMA_FAST = 9
EMA_SLOW = 25
```

**How to Customize**:
```python
# Edit at the top of strategy_dual_ema.py
EMA_FAST = 12  # Change to preferred period
EMA_SLOW = 26  # Change to preferred period
```

### Creating Custom Strategies

1. Create a new file in `strategies/` directory
2. Subscribe to market data from quoting service
3. Implement your signal logic
4. Send signals to trading service via ZMQ PUSH

**Example Signal Format**:
```json
{
  "action": "BUY",
  "symbol": "BTCUSDT",
  "quantity": 0.001,
  "price": null
}
```

## 🛠️ Tools

### Subscriber (`tools/subscriber.py`)

**Purpose**: Monitor live market data for debugging

**Usage**:
```bash
python3 tools/subscriber.py
```

**Output**: Formatted real-time quotes from quoting service

### Data Preparation (`backtesting/data_prep.py`)

**Purpose**: Replay historical data for backtesting

**Features**:
- Reads CSV/OHLCV data files
- Simulates real-time quote streaming
- Adjustable playback speed

## 💾 Database

### PostgreSQL + TimescaleDB

**Purpose**: Store and analyze trade execution history

**Schema** (example):
```sql
CREATE TABLE trades (
  id SERIAL PRIMARY KEY,
  timestamp TIMESTAMPTZ NOT NULL,
  symbol VARCHAR(20) NOT NULL,
  side VARCHAR(4) NOT NULL,
  price DECIMAL(18, 8),
  quantity DECIMAL(18, 8),
  order_id VARCHAR(50),
  status VARCHAR(20)
);

-- Convert to hypertable for time-series optimization
SELECT create_hypertable('trades', 'timestamp');
```

**Installation**:
Follow the [TimescaleDB Docker installation guide](https://www.tigerdata.com/docs/self-hosted/latest/install/installation-docker)

**Benefits**:
- Optimized for time-series queries
- Efficient data retention policies
- Fast aggregation queries

## 🤝 Contributing

Contributions are welcome! This project is a learning platform for understanding trading infrastructure.

**Areas for Contribution**:
- Additional trading strategies
- Improved risk management
- Performance optimizations
- Documentation improvements
- Bug fixes

**How to Contribute**:
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## ⚠️ Disclaimer

**EDUCATIONAL PURPOSES ONLY**

This software is for educational and research purposes only. Cryptocurrency trading carries significant financial risk. 

**Important Warnings**:
- ❌ **DO NOT** use this bot with real money without thorough testing
- ❌ **DO NOT** run untested strategies on mainnet
- ✅ **DO** use Binance testnet for development and testing
- ✅ **DO** understand the risks before trading with real capital
- ✅ **DO** start with paper trading and small amounts

**No Warranty**: This software is provided "as is" without warranty of any kind. The authors assume no responsibility for financial losses incurred through the use of this software.

**Regulatory Compliance**: Ensure compliance with local regulations regarding automated trading and cryptocurrency transactions.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 📚 Resources

- [Binance API Documentation](https://binance-docs.github.io/apidocs/)
- [ZMQ Guide](https://zeromq.org/get-started/)
- [TimescaleDB Documentation](https://docs.timescale.com/)
- [Backtest Manager Extension](https://marketplace.visualstudio.com/items?itemName=woung717.backtest-manager)

## 💡 Future Enhancements

- [ ] Web-based dashboard for monitoring
- [ ] Additional technical indicators (RSI, MACD, Bollinger Bands)
- [ ] Multi-exchange support
- [ ] Advanced risk management features
- [ ] Machine learning based strategies
- [ ] Telegram bot integration for alerts
- [ ] Automated parameter optimization

---

**Built with ❤️ for learning trading infrastructure**

*For questions or support, please open an issue on GitHub.*