"""
Cliente para Polymarket CLOB API.
Maneja autenticacion, consulta de mercados y ejecucion de ordenes.
"""
import asyncio
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import aiohttp
import requests

from config import cfg
from src.logger import setup_logger

log = setup_logger("polymarket.client")


@dataclass
class Market:
    condition_id: str
    question: str
    description: str
    end_date_iso: str
    active: bool
    closed: bool
    tokens: List[Dict]  # [{token_id, outcome, price}]
    volume: float
    liquidity: float
    # Mapeado del simbolo crypto asociado (BTC/ETH/SOL)
    crypto_symbol: Optional[str] = None
    # Strike price extraido de la pregunta
    strike_price: Optional[float] = None
    # Direccion: "above" o "below"
    direction: Optional[str] = None


@dataclass
class OrderResult:
    success: bool
    order_id: Optional[str]
    error: Optional[str]
    size: float
    price: float
    side: str


class PolymarketClient:
    """
    Wrapper sobre py-clob-client con helpers para el bot.
    Soporte para consulta de mercados y ejecucion de ordenes.
    """

    GAMMA_MARKETS = f"{cfg.GAMMA_API}/markets"
    GAMMA_EVENTS = f"{cfg.GAMMA_API}/events"

    # Keywords para detectar mercados de precio crypto
    CRYPTO_KEYWORDS = {
        "BTC": ["bitcoin", "btc"],
        "ETH": ["ethereum", "eth"],
        "SOL": ["solana", "sol"],
        "BNB": ["bnb", "binance coin"],
        "AVAX": ["avalanche", "avax"],
    }

    DIRECTION_KEYWORDS_ABOVE = ["above", "higher", "over", "exceed", "reach", "surpass", "mas de", "superar"]
    DIRECTION_KEYWORDS_BELOW = ["below", "lower", "under", "beneath", "drop", "menos de", "caer"]

    def __init__(self):
        self._clob_client = None
        self._api_creds = None
        self._session: Optional[aiohttp.ClientSession] = None
        self._initialized = False

    async def initialize(self) -> None:
        """Inicializa cliente CLOB y credenciales API."""
        if self._initialized:
            return

        # Importar aqui para evitar errores si no esta instalado en modo test
        try:
            from py_clob_client.client import ClobClient
            from py_clob_client.clob_types import ApiCreds

            self._clob_client = ClobClient(
                host=cfg.POLYMARKET_HOST,
                key=cfg.PRIVATE_KEY,
                chain_id=cfg.POLYMARKET_CHAIN_ID,
                funder=cfg.POLYMARKET_FUNDER or None,
            )

            # Obtener/crear credenciales API
            try:
                self._api_creds = self._clob_client.derive_api_key()
                log.info(f"API key derivada: {self._api_creds.api_key[:8]}...")
            except Exception as e:
                log.warning(f"No se pudo derivar API key, creando nueva: {e}")
                self._api_creds = self._clob_client.create_api_key()

            self._clob_client.set_api_creds(self._api_creds)
            log.info("Polymarket CLOB client inicializado correctamente")

        except ImportError:
            log.error("py-clob-client no instalado. Ejecuta: pip install py-clob-client")
            raise
        except Exception as e:
            log.error(f"Error inicializando Polymarket client: {e}")
            raise

        self._session = aiohttp.ClientSession()
        self._initialized = True

    async def close(self) -> None:
        if self._session:
            await self._session.close()

    async def get_usdc_balance(self) -> float:
        """Retorna balance USDC disponible en Polymarket."""
        try:
            balance = self._clob_client.get_balance()
            return float(balance)
        except Exception as e:
            log.error(f"Error obteniendo balance: {e}")
            return 0.0

    async def fetch_crypto_markets(self, symbols: List[str]) -> List[Market]:
        """
        Consulta Gamma API y filtra mercados relevantes de precio crypto.
        """
        markets: List[Market] = []

        params = {
            "active": "true",
            "closed": "false",
            "limit": 200,
            "offset": 0,
        }

        try:
            async with self._session.get(
                self.GAMMA_MARKETS, params=params, timeout=aiohttp.ClientTimeout(total=15)
            ) as resp:
                data = await resp.json()

            raw_markets = data if isinstance(data, list) else data.get("markets", [])
            log.info(f"Gamma API: {len(raw_markets)} mercados activos")

            for raw in raw_markets:
                market = self._parse_market(raw, symbols)
                if market:
                    markets.append(market)

            log.info(f"Mercados crypto detectados: {len(markets)}")
            return markets

        except Exception as e:
            log.error(f"Error consultando mercados Gamma: {e}")
            return []

    def _parse_market(self, raw: Dict[str, Any], filter_symbols: List[str]) -> Optional[Market]:
        """Intenta parsear un mercado como mercado de precio crypto."""
        question = raw.get("question", "").lower()
        description = raw.get("description", "").lower()
        text = question + " " + description

        # Detectar crypto symbol
        crypto_symbol = None
        for sym, keywords in self.CRYPTO_KEYWORDS.items():
            if sym in filter_symbols and any(kw in text for kw in keywords):
                crypto_symbol = sym
                break

        if not crypto_symbol:
            return None

        # Detectar strike price (numero en la pregunta, ej: $100,000)
        import re
        price_match = re.search(r"\$?([\d,]+(?:\.\d+)?)\s*[kK]?", raw.get("question", ""))
        strike_price = None
        if price_match:
            num_str = price_match.group(1).replace(",", "")
            try:
                strike_price = float(num_str)
                # Manejar "k" (miles)
                if "k" in raw.get("question", "").lower():
                    strike_price *= 1000
            except ValueError:
                pass

        # Detectar direccion
        direction = None
        if any(kw in text for kw in self.DIRECTION_KEYWORDS_ABOVE):
            direction = "above"
        elif any(kw in text for kw in self.DIRECTION_KEYWORDS_BELOW):
            direction = "below"

        # Obtener tokens (YES/NO outcomes)
        tokens = []
        for t in raw.get("tokens", []):
            tokens.append({
                "token_id": t.get("token_id", ""),
                "outcome": t.get("outcome", ""),
                "price": float(t.get("price", 0.5)),
            })

        if not tokens:
            return None

        return Market(
            condition_id=raw.get("condition_id", raw.get("id", "")),
            question=raw.get("question", ""),
            description=raw.get("description", ""),
            end_date_iso=raw.get("end_date_iso", raw.get("endDateIso", "")),
            active=raw.get("active", True),
            closed=raw.get("closed", False),
            tokens=tokens,
            volume=float(raw.get("volume", 0)),
            liquidity=float(raw.get("liquidity", 0)),
            crypto_symbol=crypto_symbol,
            strike_price=strike_price,
            direction=direction,
        )

    async def get_market_prices(self, condition_id: str) -> Dict[str, float]:
        """
        Obtiene precios actuales YES/NO de un mercado via CLOB.
        Retorna {token_id: precio}
        """
        try:
            orderbook = self._clob_client.get_order_book(condition_id)
            prices = {}
            for side in ["bids", "asks"]:
                for order in getattr(orderbook, side, []):
                    # Mejor precio disponible
                    prices[order.get("token_id", "")] = float(order.get("price", 0))
            return prices
        except Exception as e:
            log.warning(f"Error obteniendo orderbook {condition_id[:8]}: {e}")
            return {}

    async def place_order(
        self,
        token_id: str,
        side: str,  # "BUY" o "SELL"
        size: float,  # en USDC
        price: float,  # probabilidad 0-1
        order_type: str = "GTC",
    ) -> OrderResult:
        """
        Coloca una orden en Polymarket CLOB.

        token_id: ID del token YES o NO
        side: BUY o SELL
        size: cantidad en USDC
        price: precio como probabilidad (0.0-1.0)
        """
        try:
            from py_clob_client.clob_types import OrderArgs, OrderType, Side

            side_enum = Side.BUY if side.upper() == "BUY" else Side.SELL
            type_enum = OrderType.GTC if order_type == "GTC" else OrderType.FOK

            order_args = OrderArgs(
                token_id=token_id,
                price=round(price, 4),
                size=round(size, 2),
                side=side_enum,
                type=type_enum,
            )

            log.info(
                f"Colocando orden: {side} {size:.2f} USDC @ {price:.4f} | token={token_id[:8]}..."
            )

            response = self._clob_client.post_order(order_args, type_enum)

            if response and response.get("success"):
                order_id = response.get("orderID", response.get("order_id", ""))
                log.info(f"Orden ejecutada: {order_id}")
                return OrderResult(
                    success=True,
                    order_id=order_id,
                    error=None,
                    size=size,
                    price=price,
                    side=side,
                )
            else:
                error_msg = str(response)
                log.error(f"Orden rechazada: {error_msg}")
                return OrderResult(success=False, order_id=None, error=error_msg,
                                   size=size, price=price, side=side)

        except Exception as e:
            log.error(f"Excepcion al colocar orden: {e}")
            return OrderResult(success=False, order_id=None, error=str(e),
                               size=size, price=price, side=side)

    async def cancel_order(self, order_id: str) -> bool:
        try:
            self._clob_client.cancel_order(order_id)
            log.info(f"Orden cancelada: {order_id}")
            return True
        except Exception as e:
            log.error(f"Error cancelando orden {order_id}: {e}")
            return False

    async def get_open_orders(self) -> List[Dict]:
        try:
            return self._clob_client.get_orders() or []
        except Exception as e:
            log.error(f"Error obteniendo ordenes abiertas: {e}")
            return []
