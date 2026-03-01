"""
Cliente para Polymarket CLOB API.
Maneja autenticacion, consulta de mercados y ejecucion de ordenes.

Convencion de tallas en Polymarket CLOB:
  - BUY:  size = shares a comprar.  Coste = shares × price USDC
  - SELL: size = shares a vender.  Ingreso = shares × price USDC
  - Para convertir USDC → shares en BUY: shares = usdc / price
"""
import asyncio
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import aiohttp

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
    crypto_symbol: Optional[str] = None
    strike_price: Optional[float] = None
    direction: Optional[str] = None  # "above" | "below"


@dataclass
class OrderResult:
    success: bool
    order_id: Optional[str]
    error: Optional[str]
    size_usdc: float
    shares: float
    price: float
    side: str


class PolymarketClient:
    """
    Wrapper sobre py-clob-client con helpers para el bot.
    """

    GAMMA_MARKETS = f"{cfg.GAMMA_API}/markets"

    CRYPTO_KEYWORDS = {
        "BTC": ["bitcoin", "btc"],
        "ETH": ["ethereum", "eth"],
        "SOL": ["solana", "sol"],
        "BNB": ["bnb", "binance coin"],
        "AVAX": ["avalanche", "avax"],
    }

    DIRECTION_ABOVE = ["above", "higher", "over", "exceed", "reach", "surpass"]
    DIRECTION_BELOW = ["below", "lower", "under", "beneath", "drop"]

    def __init__(self):
        self._clob_client = None
        self._api_creds = None
        self._session: Optional[aiohttp.ClientSession] = None
        self._initialized = False

    async def initialize(self) -> None:
        if self._initialized:
            return
        try:
            from py_clob_client.client import ClobClient

            self._clob_client = ClobClient(
                host=cfg.POLYMARKET_HOST,
                key=cfg.PRIVATE_KEY,
                chain_id=cfg.POLYMARKET_CHAIN_ID,
                funder=cfg.POLYMARKET_FUNDER or None,
            )
            try:
                self._api_creds = self._clob_client.derive_api_key()
                log.info(f"API key derivada: {self._api_creds.api_key[:8]}...")
            except Exception as e:
                log.warning(f"Derivando API key fallida, creando nueva: {e}")
                self._api_creds = self._clob_client.create_api_key()

            self._clob_client.set_api_creds(self._api_creds)
            log.info("Polymarket CLOB client inicializado")

        except ImportError:
            log.error("py-clob-client no instalado. pip install py-clob-client")
            raise
        except Exception as e:
            log.error(f"Error inicializando client: {e}")
            raise

        self._session = aiohttp.ClientSession()
        self._initialized = True

    async def close(self) -> None:
        if self._session:
            await self._session.close()

    async def get_usdc_balance(self) -> float:
        try:
            return float(self._clob_client.get_balance())
        except Exception as e:
            log.error(f"Error obteniendo balance: {e}")
            return 0.0

    # ------------------------------------------------------------------ #
    # Consulta de mercados                                                 #
    # ------------------------------------------------------------------ #

    async def fetch_crypto_markets(self, symbols: List[str]) -> List[Market]:
        markets: List[Market] = []
        params = {"active": "true", "closed": "false", "limit": 200, "offset": 0}
        try:
            async with self._session.get(
                self.GAMMA_MARKETS, params=params,
                timeout=aiohttp.ClientTimeout(total=15)
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
            log.error(f"Error consultando mercados: {e}")
            return []

    def _parse_market(self, raw: Dict[str, Any], filter_symbols: List[str]) -> Optional[Market]:
        question = raw.get("question", "").lower()
        text = question + " " + raw.get("description", "").lower()

        crypto_symbol = None
        for sym, keywords in self.CRYPTO_KEYWORDS.items():
            if sym in filter_symbols and any(kw in text for kw in keywords):
                crypto_symbol = sym
                break
        if not crypto_symbol:
            return None

        strike_price = None
        price_match = re.search(r"\$?([\d,]+(?:\.\d+)?)\s*[kK]?", raw.get("question", ""))
        if price_match:
            try:
                num_str = price_match.group(1).replace(",", "")
                strike_price = float(num_str)
                if "k" in raw.get("question", "").lower():
                    strike_price *= 1000
            except ValueError:
                pass

        direction = None
        if any(kw in text for kw in self.DIRECTION_ABOVE):
            direction = "above"
        elif any(kw in text for kw in self.DIRECTION_BELOW):
            direction = "below"

        tokens = [
            {"token_id": t.get("token_id", ""), "outcome": t.get("outcome", ""),
             "price": float(t.get("price", 0.5))}
            for t in raw.get("tokens", [])
        ]
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

    # ------------------------------------------------------------------ #
    # Precios de mercado                                                   #
    # ------------------------------------------------------------------ #

    async def get_token_best_bid(self, token_id: str) -> Optional[float]:
        """
        Retorna el mejor precio BID para un token (lo que obtendremos al vender).
        Si no hay bids, retorna None.
        """
        try:
            book = self._clob_client.get_order_book(token_id)
            bids = getattr(book, "bids", [])
            if not bids:
                return None
            # bids ordenados de mayor a menor precio
            best = max(bids, key=lambda b: float(b.get("price", 0)))
            return float(best.get("price", 0))
        except Exception as e:
            log.warning(f"Error obteniendo bid para {token_id[:8]}: {e}")
            return None

    async def get_token_best_ask(self, token_id: str) -> Optional[float]:
        """
        Retorna el mejor ASK (precio al que podemos comprar).
        """
        try:
            book = self._clob_client.get_order_book(token_id)
            asks = getattr(book, "asks", [])
            if not asks:
                return None
            best = min(asks, key=lambda a: float(a.get("price", 1)))
            return float(best.get("price", 1))
        except Exception as e:
            log.warning(f"Error obteniendo ask para {token_id[:8]}: {e}")
            return None

    # ------------------------------------------------------------------ #
    # Ejecucion de ordenes                                                 #
    # ------------------------------------------------------------------ #

    async def buy_usdc(
        self,
        token_id: str,
        usdc_amount: float,
        price: float,
    ) -> OrderResult:
        """
        Compra `usdc_amount` USDC del token al precio `price`.
        Internamente convierte a shares = usdc_amount / price.
        """
        if price <= 0:
            return OrderResult(success=False, order_id=None,
                               error="Precio invalido", size_usdc=usdc_amount,
                               shares=0, price=price, side="BUY")

        shares = round(usdc_amount / price, 2)
        log.info(
            f"BUY {usdc_amount:.2f} USDC → {shares:.2f} shares @ {price:.4f} | "
            f"token={token_id[:10]}..."
        )
        return await self._place_order(token_id, "BUY", shares, price)

    async def sell_shares(
        self,
        token_id: str,
        shares: float,
        min_price: float,
    ) -> OrderResult:
        """
        Vende `shares` tokens al precio minimo `min_price`.
        Usa GTC para que se ejecute al mejor precio disponible.
        """
        usdc_value = round(shares * min_price, 2)
        log.info(
            f"SELL {shares:.2f} shares @ min {min_price:.4f} "
            f"(≈{usdc_value:.2f} USDC) | token={token_id[:10]}..."
        )
        return await self._place_order(token_id, "SELL", shares, min_price)

    async def _place_order(
        self,
        token_id: str,
        side: str,
        shares: float,
        price: float,
        order_type: str = "GTC",
    ) -> OrderResult:
        """
        Coloca orden en CLOB. `shares` es en unidades de token (outcome shares).
        """
        usdc_value = round(shares * price, 2)
        try:
            from py_clob_client.clob_types import OrderArgs, OrderType, Side

            side_enum = Side.BUY if side == "BUY" else Side.SELL
            type_enum = OrderType.GTC if order_type == "GTC" else OrderType.FOK

            order_args = OrderArgs(
                token_id=token_id,
                price=round(price, 4),
                size=round(shares, 2),   # CLOB espera shares, no USDC
                side=side_enum,
                type=type_enum,
            )

            response = self._clob_client.post_order(order_args, type_enum)

            if response and response.get("success"):
                order_id = response.get("orderID", response.get("order_id", "unknown"))
                log.info(f"Orden {side} ejecutada: {order_id} | {shares:.2f}sh @ {price:.4f}")
                return OrderResult(
                    success=True, order_id=order_id, error=None,
                    size_usdc=usdc_value, shares=shares, price=price, side=side,
                )
            else:
                err = str(response)
                log.error(f"Orden rechazada: {err}")
                return OrderResult(success=False, order_id=None, error=err,
                                   size_usdc=usdc_value, shares=shares, price=price, side=side)

        except Exception as e:
            log.error(f"Excepcion en orden {side}: {e}")
            return OrderResult(success=False, order_id=None, error=str(e),
                               size_usdc=usdc_value, shares=shares, price=price, side=side)

    async def cancel_order(self, order_id: str) -> bool:
        try:
            self._clob_client.cancel_order(order_id)
            log.info(f"Orden cancelada: {order_id}")
            return True
        except Exception as e:
            log.error(f"Error cancelando {order_id}: {e}")
            return False

    async def get_open_orders(self) -> List[Dict]:
        try:
            return self._clob_client.get_orders() or []
        except Exception as e:
            log.error(f"Error obteniendo ordenes abiertas: {e}")
            return []
