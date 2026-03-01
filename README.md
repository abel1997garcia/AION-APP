# AION - Crypto Trading Bot (Binance → Polymarket Hedge)

Bot automatico que detecta divergencias entre el precio real de Binance y las probabilidades
de Polymarket, y opera en el lado correcto para capturar el spread.

## Arquitectura

```
Binance WebSocket (BTC/ETH/SOL tick-by-tick)
          │
          ▼
  TechnicalPredictor
  (EMA, RSI, Momentum, Velocity)
          │
          ▼  PriceSignal { direction, confidence }
          │
          ▼
  HedgeDetector
  ┌────────────────────────────────────────────────────┐
  │  Polymarket CLOB API                               │
  │  "Will BTC be above $X on date Y?" → YES @ 0.42   │
  │                                                    │
  │  Black-Scholes prob(BTC > X) = 0.63               │
  │  Edge = 0.63 - 0.42 = 0.21 → OPORTUNIDAD         │
  └────────────────────────────────────────────────────┘
          │
          ▼
  PortfolioManager (Kelly conservador)
  → Calcula tamaño proporcional: 5-15% del portfolio
          │
          ▼
  Polymarket CLOB → Ejecuta orden BUY YES
```

## Estrategia de Trading

1. **Feed de precios**: Binance WebSocket en tiempo real para BTC, ETH, SOL (y más)
2. **Predictor tecnico**: Combina EMA crossover, RSI, momentum y velocidad de precio
3. **Deteccion de hedge**:
   - Busca mercados de Polymarket tipo "Will BTC be above $X on [date]?"
   - Calcula probabilidad justa con modelo Black-Scholes + drift de la señal tecnica
   - Si Polymarket muestra precio significativamente diferente → oportunidad
4. **Sizing proporcional (Kelly conservador)**:
   - `kelly = (p*b - q) / b` donde b = odds de Polymarket
   - Se aplica factor 0.25 + escala por confianza de la señal
   - Maximo configurable por operacion (default 10% del portfolio)

## Instalacion (VPS Linux)

```bash
git clone <repo> AION-APP && cd AION-APP

# Instalacion automatica
chmod +x install.sh && ./install.sh

# Configurar credenciales
nano .env   # Pegar tu PRIVATE_KEY de wallet EVM con USDC en Polygon
```

## Configuracion (.env)

```env
PRIVATE_KEY=0x...tu_private_key_de_wallet_polygon...

# Ajustes de estrategia
MAX_POSITION_PCT=0.10      # Max 10% del portfolio por operacion
MIN_EDGE_THRESHOLD=0.08    # Solo operar si edge > 8%
MIN_CONFIDENCE=0.65        # Confianza minima del predictor (65%)
MAX_OPEN_POSITIONS=5       # Max 5 operaciones simultaneas

# Cryptos
TRACKED_SYMBOLS=BTC,ETH,SOL
```

## Uso

```bash
source venv/bin/activate

# Modo prueba (no ejecuta ordenes reales)
python main.py --dry-run

# Modo real
python main.py

# Solo BTC y ETH
python main.py --symbols BTC,ETH
```

## Ejecutar como servicio (systemd)

```bash
sudo cp aion-bot.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable aion-bot
sudo systemctl start aion-bot

# Ver logs
journalctl -u aion-bot -f
```

## Requisitos de la wallet

- Wallet EVM (MetaMask, etc.) con **USDC en Polygon Mainnet** (chain ID 137)
- La misma wallet debe estar registrada en [Polymarket](https://polymarket.com)
- El private key se usa para firmar ordenes CLOB (nunca sale del servidor)

## Archivos del proyecto

```
AION-APP/
├── main.py                    # Punto de entrada
├── config.py                  # Configuracion centralizada
├── requirements.txt           # Dependencias Python
├── .env.example               # Template de variables de entorno
├── install.sh                 # Script de instalacion para VPS
├── aion-bot.service           # Servicio systemd
└── src/
    ├── price_feed.py          # Binance WebSocket (OHLCV + tickers)
    ├── bot.py                 # Orquestador principal
    ├── portfolio.py           # Gestion de posiciones y sizing
    ├── logger.py              # Logger con colores
    ├── polymarket/
    │   └── client.py          # Cliente CLOB + Gamma API
    └── analysis/
        ├── predictor.py       # Indicadores tecnicos (EMA, RSI, momentum)
        └── hedge.py           # Deteccion de oportunidades de hedge
```

## Riesgos

- Las predicciones tecnicas no garantizan exactitud
- Los mercados de Polymarket tienen liquidez variable
- Usar siempre `--dry-run` primero para validar la logica
- Nunca invertir mas de lo que puedes permitirte perder
