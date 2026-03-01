"""
Configuracion centralizada del bot.
Lee variables de entorno desde .env
"""
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # Wallet
    PRIVATE_KEY: str = os.getenv("PRIVATE_KEY", "")
    POLYMARKET_FUNDER: str = os.getenv("POLYMARKET_FUNDER", "")

    # Polymarket
    POLYMARKET_HOST: str = os.getenv("POLYMARKET_HOST", "https://clob.polymarket.com")
    POLYMARKET_CHAIN_ID: int = int(os.getenv("POLYMARKET_CHAIN_ID", "137"))
    GAMMA_API: str = "https://gamma-api.polymarket.com"

    # Binance WebSocket
    BINANCE_WS_BASE: str = "wss://stream.binance.com:9443/ws"
    BINANCE_API_KEY: str = os.getenv("BINANCE_API_KEY", "")
    BINANCE_API_SECRET: str = os.getenv("BINANCE_API_SECRET", "")

    # Estrategia
    MAX_POSITION_PCT: float = float(os.getenv("MAX_POSITION_PCT", "0.10"))
    MIN_EDGE_THRESHOLD: float = float(os.getenv("MIN_EDGE_THRESHOLD", "0.08"))
    MIN_CONFIDENCE: float = float(os.getenv("MIN_CONFIDENCE", "0.65"))
    MAX_OPEN_POSITIONS: int = int(os.getenv("MAX_OPEN_POSITIONS", "5"))
    MIN_ORDER_SIZE: float = float(os.getenv("MIN_ORDER_SIZE", "10"))
    MAX_ORDER_SIZE: float = float(os.getenv("MAX_ORDER_SIZE", "500"))

    # Cryptos
    TRACKED_SYMBOLS: list[str] = [
        s.strip().upper()
        for s in os.getenv("TRACKED_SYMBOLS", "BTC,ETH,SOL").split(",")
    ]

    # Logs
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: str = os.getenv("LOG_FILE", "logs/bot.log")

    # Timeframes operativos
    TF_ENTRY: str = "5m"    # timeframe de entrada/timing (rapido)
    TF_TREND: str = "15m"   # timeframe de tendencia (lento, contexto)

    # Indicadores tecnicos — 5m (entrada)
    EMA_FAST_5M: int = 8    # ~40 min
    EMA_SLOW_5M: int = 21   # ~105 min
    RSI_PERIOD_5M: int = 14
    MOMENTUM_WINDOW_5M: int = 6   # 6 velas × 5m = 30 min de momentum

    # Indicadores tecnicos — 15m (tendencia)
    EMA_FAST_15M: int = 5   # ~75 min
    EMA_SLOW_15M: int = 10  # ~150 min
    RSI_PERIOD_15M: int = 14
    MOMENTUM_WINDOW_15M: int = 4  # 4 velas × 15m = 60 min de momentum

    # Compatibilidad (aliases al TF de entrada)
    EMA_FAST: int = 8
    EMA_SLOW: int = 21
    RSI_PERIOD: int = 14
    MOMENTUM_WINDOW: int = 6

    PRICE_HISTORY_LIMIT: int = 200  # velas en memoria por simbolo y TF

    # Multi-timeframe: bonificacion/penalizacion de confianza
    MTF_AGREEMENT_BOOST: float = 0.15      # bonus cuando 5m y 15m coinciden
    MTF_DISAGREEMENT_PENALTY: float = 0.30 # penalizacion cuando divergen

    # Deteccion de divergencia Binance→Polymarket
    PRICE_MOVE_THRESHOLD: float = 0.003   # 0.3% movimiento minimo (5m mueve menos)
    LEAD_LAG_WINDOW: int = 3              # ventana de lead/lag en velas de 5m

    # Kelly fraction conservador
    KELLY_FRACTION: float = 0.25

    # Gestion de salida de posiciones
    # Salir cuando hayamos capturado este % del edge estimado
    TAKE_PROFIT_RATIO: float = 0.55
    # Salir si la posicion cae este % sobre el capital apostado (stop-loss)
    STOP_LOSS_RATIO: float = 0.20
    # Siempre salir cuando queden menos de estas horas para expirar
    MIN_HOURS_TO_EXPIRY: float = 2.0
    # Segundos entre cada revision de posiciones abiertas
    POSITION_CHECK_INTERVAL: int = 30

    def validate(self) -> None:
        if not self.PRIVATE_KEY or self.PRIVATE_KEY == "0xTU_PRIVATE_KEY_AQUI":
            raise ValueError(
                "PRIVATE_KEY no configurado. Copia .env.example a .env y configura tu wallet."
            )


cfg = Config()
