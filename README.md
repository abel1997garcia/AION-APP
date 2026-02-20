# AION – Binance/Polymarket Arbitrage Bot

Statistical arbitrage bot that monitors live BTC prices on Binance and exploits
mispricings in Bitcoin binary prediction markets on Polymarket.

## How it works

```
Binance WebSocket  ──► BTC spot price (real-time)
                              │
                              ▼
                    Lognormal pricing model
                    P(BTC > $K at expiry T)
                              │
                              ▼
                  Polymarket CLOB market prices
                  (YES token implied probability)
                              │
                         edge = model - market
                              │
                    ┌─────────┴─────────┐
                edge > 1.5%         edge < -1.5%
                BUY YES             BUY NO
                    │                   │
                    └────── Risk Manager ──────┘
                         Kelly sizing, $200 cap
                              │
                    Polymarket CLOB order (FOK)
```

## Project structure

```
AION-APP/
├── trading_bot/
│   ├── main.py              # Entry point / async orchestrator
│   ├── config.py            # .env configuration loader
│   ├── logger.py            # Loguru setup (console + rotating file)
│   ├── binance_feed.py      # Binance WebSocket real-time feed
│   ├── pricing_model.py     # Lognormal probability model
│   ├── polymarket_client.py # Polymarket CLOB API wrapper
│   ├── risk_manager.py      # Kelly sizing + exposure limits
│   └── arbitrage_engine.py  # Core strategy logic
├── requirements.txt
├── setup.py
├── setup.sh                 # VPS one-shot setup script
└── .env.example             # Configuration template
```

## VPS Setup (Lithuania)

```bash
# 1. Clone / upload the repo
git clone <your-repo-url> /opt/aion-bot
cd /opt/aion-bot

# 2. Run setup (requires sudo)
sudo bash setup.sh

# 3. Fill in your credentials
nano .env          # set POLYMARKET_PRIVATE_KEY

# 4. Start the bot
sudo systemctl start aion-bot
sudo journalctl -u aion-bot -f
```

## Manual run (without systemd)

```bash
cd /opt/aion-bot
source .venv/bin/activate
python -m trading_bot.main
```

## Configuration

Copy `.env.example` to `.env` and edit:

| Variable | Description | Default |
|---|---|---|
| `POLYMARKET_PRIVATE_KEY` | Your Polygon wallet private key | **required** |
| `MAX_POSITION_USDC` | Max USDC per trade | `200` |
| `MIN_EDGE_THRESHOLD` | Min edge to trade (e.g. `0.015` = 1.5%) | `0.015` |
| `MAX_TOTAL_EXPOSURE_USDC` | Max total open positions | `1000` |
| `KELLY_FRACTION` | Kelly multiplier (0.5 = half-Kelly) | `0.5` |
| `BTC_ANNUAL_VOL_OVERRIDE` | Override volatility (e.g. `0.80`). Empty = auto | `` |
| `MARKET_SCAN_INTERVAL_SECONDS` | How often to refresh market list | `300` |

## Wallet requirements

Your Polymarket wallet needs:
- **USDC** on Polygon (for buying positions)
- A small amount of **MATIC** for gas (~0.1 MATIC is enough for months)

## Pricing model

The bot prices `P(BTC_T > K)` using geometric Brownian motion:

```
d2 = [ln(S/K) + (drift - σ²/2)·T] / (σ·√T)
P(S_T > K) = N(d2)
```

- `S` = Binance live price
- `K` = market strike price (parsed from question)
- `T` = time to expiry in years
- `σ` = 30-day realized volatility (auto-fetched, or overridden via .env)
- `drift = 0` (risk-neutral)

## Risk management

- **Half-Kelly** position sizing capped at `MAX_POSITION_USDC`
- Only one position per market condition at a time
- Total exposure capped at `MAX_TOTAL_EXPOSURE_USDC`
- FOK orders – if not filled at the limit price, no trade occurs

## Disclaimer

This software is for educational and personal use. Trading prediction markets
carries significant financial risk. Past performance of any model does not
guarantee future results.
