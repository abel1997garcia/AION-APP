"""
Orquestador principal del trading bot.

Flujo:
  1. Binance WebSocket → precios en tiempo real
  2. Cada N segundos: analizar señales tecnicas
  3. Obtener mercados activos de Polymarket (cache 5 min)
  4. Detectar oportunidades de hedge
  5. Calcular tamaño proporcional
  6. Ejecutar orden en Polymarket
  7. Monitorear posiciones abiertas
"""
import asyncio
import time
from datetime import datetime
from typing import Dict, List, Optional

from config import cfg
from src.analysis.hedge import HedgeDetector, HedgeOpportunity
from src.analysis.predictor import TechnicalPredictor
from src.logger import setup_logger
from src.polymarket.client import Market, PolymarketClient
from src.portfolio import PortfolioManager
from src.price_feed import PriceFeed, TickerData

log = setup_logger("bot")


class TradingBot:
    """
    Bot de trading Binance → Polymarket hedge.
    """

    MARKET_REFRESH_INTERVAL = 300   # segundos entre actualizacion de mercados
    ANALYSIS_INTERVAL = 30          # segundos entre ciclos de analisis
    BALANCE_REFRESH_INTERVAL = 60   # segundos entre actualizacion de balance

    def __init__(self):
        self.feed = PriceFeed(cfg.TRACKED_SYMBOLS)
        self.poly_client = PolymarketClient()
        self.predictor = TechnicalPredictor(self.feed)
        self.hedge_detector = HedgeDetector(min_liquidity=500.0)
        self.portfolio = PortfolioManager()

        self._markets: List[Market] = []
        self._last_market_refresh: float = 0
        self._last_analysis: float = 0
        self._last_balance_refresh: float = 0
        self._running = False

    async def start(self) -> None:
        log.info("=" * 60)
        log.info("  AION CRYPTO TRADING BOT - INICIANDO")
        log.info(f"  Simbolos: {cfg.TRACKED_SYMBOLS}")
        log.info(f"  Max posicion: {cfg.MAX_POSITION_PCT*100:.0f}%")
        log.info(f"  Edge minimo: {cfg.MIN_EDGE_THRESHOLD*100:.0f}%")
        log.info(f"  Confianza minima: {cfg.MIN_CONFIDENCE*100:.0f}%")
        log.info("=" * 60)

        # Inicializar Polymarket client
        await self.poly_client.initialize()

        # Obtener balance inicial
        balance = await self.poly_client.get_usdc_balance()
        self.portfolio.update_balance(balance)
        log.info(f"Balance USDC: {balance:.2f}")

        if balance < cfg.MIN_ORDER_SIZE:
            log.warning(
                f"Balance ({balance:.2f} USDC) menor al minimo por operacion "
                f"({cfg.MIN_ORDER_SIZE} USDC). El bot monitoreara pero no operara."
            )

        # Cargar mercados iniciales
        await self._refresh_markets()

        # Registrar callback de precio
        self.feed.add_callback(self._on_ticker)

        # Lanzar tareas
        self._running = True
        await asyncio.gather(
            self.feed.start(),
            self._analysis_loop(),
            self._balance_loop(),
            return_exceptions=True,
        )

    async def stop(self) -> None:
        self._running = False
        await self.feed.stop()
        await self.poly_client.close()
        self.portfolio.print_summary()
        log.info("Bot detenido correctamente.")

    # ------------------------------------------------------------------ #
    # Callbacks y loops                                                    #
    # ------------------------------------------------------------------ #

    async def _on_ticker(self, ticker: TickerData) -> None:
        """Callback llamado en cada tick de precio."""
        # Por ahora solo logueamos a DEBUG; el analisis va en el loop separado
        log.debug(f"[{ticker.symbol}] ${ticker.price:,.2f}")

    async def _analysis_loop(self) -> None:
        """Loop principal de analisis y trading."""
        # Esperar a que el feed tenga suficientes datos
        log.info("Esperando datos del WebSocket (60s)...")
        await asyncio.sleep(60)

        while self._running:
            try:
                await self._run_analysis_cycle()
            except Exception as e:
                log.error(f"Error en ciclo de analisis: {e}", exc_info=True)

            await asyncio.sleep(self.ANALYSIS_INTERVAL)

    async def _balance_loop(self) -> None:
        """Actualiza el balance periodicamente."""
        while self._running:
            await asyncio.sleep(self.BALANCE_REFRESH_INTERVAL)
            try:
                balance = await self.poly_client.get_usdc_balance()
                self.portfolio.update_balance(balance)
                log.info(f"Balance actualizado: {balance:.2f} USDC")
            except Exception as e:
                log.warning(f"Error actualizando balance: {e}")

    # ------------------------------------------------------------------ #
    # Ciclo de analisis                                                    #
    # ------------------------------------------------------------------ #

    async def _run_analysis_cycle(self) -> None:
        """
        Un ciclo completo: analizar → detectar → operar.
        """
        now = time.time()

        # Refrescar mercados si toca
        if now - self._last_market_refresh > self.MARKET_REFRESH_INTERVAL:
            await self._refresh_markets()

        if not self._markets:
            log.warning("No hay mercados disponibles de Polymarket. Reintentando en el proximo ciclo.")
            return

        log.debug(f"Ciclo de analisis | {len(self._markets)} mercados disponibles")

        all_opportunities: List[HedgeOpportunity] = []

        for symbol in cfg.TRACKED_SYMBOLS:
            signal = self.predictor.analyze(symbol)
            if signal is None:
                continue

            price = self.feed.get_price(symbol)
            if price:
                log.info(
                    f"[{symbol}] ${price:,.2f} | dir={signal.direction} "
                    f"conf={signal.confidence:.2f} mom={signal.momentum:+.4f} "
                    f"rsi={signal.rsi:.1f if signal.rsi else 'N/A'}"
                )

            if not signal.is_actionable():
                log.debug(f"[{symbol}] Señal no accionable (conf={signal.confidence:.2f})")
                continue

            opps = self.hedge_detector.find_opportunities(signal, self._markets)
            all_opportunities.extend(opps)

        if not all_opportunities:
            log.debug("Sin oportunidades de hedge en este ciclo.")
            return

        log.info(f"Oportunidades detectadas: {len(all_opportunities)}")

        # Ejecutar las mejores oportunidades
        for opp in all_opportunities[:3]:  # max 3 por ciclo
            if not self.portfolio.can_open_position(opp):
                continue

            size = self.portfolio.calculate_position_size(opp)
            if size < cfg.MIN_ORDER_SIZE:
                log.warning(f"Tamaño calculado ({size:.2f}) menor al minimo. Saltando.")
                continue

            await self._execute_opportunity(opp, size)

    async def _execute_opportunity(
        self, opp: HedgeOpportunity, size: float
    ) -> None:
        """Ejecuta una oportunidad de hedge en Polymarket."""
        log.info(
            f"EJECUTANDO: {opp.market.crypto_symbol} {opp.outcome_label} "
            f"{size:.2f} USDC @ {opp.market_price:.4f} "
            f"(fair={opp.fair_price:.4f} edge={opp.edge:+.4f})"
        )

        result = await self.poly_client.place_order(
            token_id=opp.token_id,
            side="BUY",
            size=size,
            price=opp.market_price,
        )

        if result.success:
            position = self.portfolio.open_position(
                opportunity=opp,
                order_id=result.order_id,
                actual_size=size,
            )
            log.info(f"Posicion abierta exitosamente: {position.position_id}")
        else:
            log.error(f"Fallo al ejecutar orden: {result.error}")

    async def _refresh_markets(self) -> None:
        """Actualiza la lista de mercados activos de Polymarket."""
        log.info("Actualizando mercados de Polymarket...")
        try:
            markets = await self.poly_client.fetch_crypto_markets(cfg.TRACKED_SYMBOLS)
            self._markets = markets
            self._last_market_refresh = time.time()

            # Resumen de mercados
            by_symbol: Dict[str, int] = {}
            for m in markets:
                sym = m.crypto_symbol or "?"
                by_symbol[sym] = by_symbol.get(sym, 0) + 1
            summary = ", ".join(f"{k}:{v}" for k, v in sorted(by_symbol.items()))
            log.info(f"Mercados cargados: {len(markets)} | {summary}")

        except Exception as e:
            log.error(f"Error actualizando mercados: {e}")
