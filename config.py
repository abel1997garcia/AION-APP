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

    # Indicadores tecnicos
    EMA_FAST: int = 9
    EMA_SLOW: int = 21
    RSI_PERIOD: int = 14
    MOMENTUM_WINDOW: int = 10        # velas para calcular momentum
    PRICE_HISTORY_LIMIT: int = 200   # velas en memoria por simbolo
    CANDLE_INTERVAL: str = "1m"      # intervalo de velas

    # Deteccion de divergencia Binance→Polymarket
    PRICE_MOVE_THRESHOLD: float = 0.005   # 0.5% movimiento minimo para signal
    LEAD_LAG_WINDOW: int = 5              # minutos de ventana de lead/lag

    # Kelly fraction conservador
    KELLY_FRACTION: float = 0.25

    def validate(self) -> None:
        if not self.PRIVATE_KEY or self.PRIVATE_KEY == "0xTU_PRIVATE_KEY_AQUI":
            raise ValueError(
                "PRIVATE_KEY no configurado. Copia .env.example a .env y configura tu wallet."
            )


cfg = Config()
