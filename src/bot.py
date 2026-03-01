"""
Orquestador principal del trading bot (multi-timeframe 5m/15m).

Flujo de entrada:
  1. Binance WS cierra vela de 5m → evento en candle_close_queue
  2. Bot despierta y ejecuta analisis MTF (5m timing + 15m tendencia)
  3. HedgeDetector compara precio Binance vs probabilidad Polymarket
  4. Si edge >= threshold: place_order en CLOB (shares calculados correctamente)

Flujo de salida (loop paralelo cada 30s):
  5. Para cada posicion abierta: consultar precio actual en CLOB
  6. check_exit_signal → take_profit / stop_loss / time_exit
  7. Si señal de salida: sell_shares en CLOB → close_position en portfolio
"""
import asyncio
import time
from typing import Dict, List, Optional

from config import cfg
from src.analysis.hedge import HedgeDetector, HedgeOpportunity
from src.analysis.predictor import MTFSignal, TechnicalPredictor
from src.logger import setup_logger
from src.polymarket.client import Market, PolymarketClient
from src.portfolio import ExitReason, PortfolioManager, Position
from src.price_feed import PriceFeed, TickerData

log = setup_logger("bot")


class TradingBot:
    """Bot de trading Binance → Polymarket hedge (MTF 5m/15m)."""

    MARKET_REFRESH_INTERVAL = 300   # 5 min entre refrescos de mercados Polymarket
    WARMUP_SECONDS = 120            # espera inicial mientras se acumulan velas

    def __init__(self):
        self.feed = PriceFeed(cfg.TRACKED_SYMBOLS)
        self.poly_client = PolymarketClient()
        self.predictor = TechnicalPredictor(self.feed)
        self.hedge_detector = HedgeDetector(min_liquidity=500.0)
        self.portfolio = PortfolioManager()

        self._markets: List[Market] = []
        self._last_market_refresh: float = 0
        self._running = False

    # ------------------------------------------------------------------ #
    # Lifecycle                                                            #
    # ------------------------------------------------------------------ #

    async def start(self) -> None:
        log.info("=" * 65)
        log.info("  AION CRYPTO TRADING BOT  [MTF 5m/15m | Polymarket Hedge]")
        log.info(f"  Simbolos:       {cfg.TRACKED_SYMBOLS}")
        log.info(f"  Timeframes:     {cfg.TF_ENTRY} entrada + {cfg.TF_TREND} tendencia")
        log.info(f"  Max posicion:   {cfg.MAX_POSITION_PCT*100:.0f}%  "
                 f"Edge min: {cfg.MIN_EDGE_THRESHOLD*100:.0f}%  "
                 f"Conf min: {cfg.MIN_CONFIDENCE*100:.0f}%")
        log.info(f"  Take-profit:    +{cfg.TAKE_PROFIT_RATIO*100:.0f}% del edge   "
                 f"Stop-loss: -{cfg.STOP_LOSS_RATIO*100:.0f}% capital")
        log.info(f"  Time-exit:      <{cfg.MIN_HOURS_TO_EXPIRY:.0f}h para expirar")
        log.info("=" * 65)

        await self.poly_client.initialize()

        balance = await self.poly_client.get_usdc_balance()
        self.portfolio.update_balance(balance)
        log.info(f"Balance USDC: {balance:.2f}")

        if balance < cfg.MIN_ORDER_SIZE:
            log.warning(
                f"Balance ({balance:.2f} USDC) < minimo por operacion "
                f"({cfg.MIN_ORDER_SIZE} USDC). Monitoreando sin operar."
            )

        await self._refresh_markets()
        self.feed.add_callback(self._on_ticker)
        self._running = True

        await asyncio.gather(
            self.feed.start(),
            self._analysis_loop(),
            self._position_monitor_loop(),
            self._balance_loop(),
            return_exceptions=True,
        )

    async def stop(self) -> None:
        self._running = False
        await self.feed.stop()
        await self.poly_client.close()
        self.portfolio.print_summary()
        log.info("Bot detenido.")

    # ------------------------------------------------------------------ #
    # Loop de analisis — EVENT-DRIVEN al cierre de cada vela de 5m        #
    # ------------------------------------------------------------------ #

    async def _analysis_loop(self) -> None:
        """
        Analisis disparado POR EVENTO al cierre de cada vela de 5m.
        Fallback por timeout cada 90s si no llegan eventos.
        """
        log.info(f"Warmup {self.WARMUP_SECONDS}s (acumulando velas 5m/15m)...")
        await asyncio.sleep(self.WARMUP_SECONDS)

        while self._running:
            try:
                # Esperar evento de cierre de vela de 5m (timeout = fallback)
                symbol, tf = await asyncio.wait_for(
                    self.feed.candle_close_queue.get(),
                    timeout=90.0,
                )
                log.debug(f"Vela {tf} cerrada para {symbol} → analizando")
                await self._analyze_symbol(symbol)
            except asyncio.TimeoutError:
                # Fallback: analizar todos los simbolos
                log.debug("Timeout de evento → analisis de fallback")
                for sym in cfg.TRACKED_SYMBOLS:
                    if self._running:
                        await self._analyze_symbol(sym)
            except Exception as e:
                log.error(f"Error en analysis_loop: {e}", exc_info=True)

    async def _analyze_symbol(self, symbol: str) -> None:
        """Analiza un simbolo y ejecuta oportunidades si las hay."""
        now = time.time()
        if now - self._last_market_refresh > self.MARKET_REFRESH_INTERVAL:
            await self._refresh_markets()
        if not self._markets:
            return

        signal: Optional[MTFSignal] = self.predictor.analyze_mtf(symbol)
        if signal is None:
            counts = self.feed.candle_counts(symbol)
            log.debug(
                f"[{symbol}] Acumulando | "
                f"5m={counts.get('5m', 0)}/{cfg.EMA_SLOW_5M+5} "
                f"15m={counts.get('15m', 0)}/{cfg.EMA_SLOW_15M+5}"
            )
            return

        log.info(signal.log_summary())

        if not signal.is_actionable():
            if not signal.tfs_agree and signal.signal_15m and signal.signal_15m.direction != "neutral":
                log.debug(f"[{symbol}] TFs discrepan → abstenerse")
            return

        opps = self.hedge_detector.find_opportunities(signal, self._markets)
        for opp in opps[:2]:  # max 2 operaciones por simbolo por ciclo
            if self.portfolio.can_open_position(opp):
                await self._execute_entry(opp)

    # ------------------------------------------------------------------ #
    # Loop de monitoreo de posiciones — SALIDA                            #
    # ------------------------------------------------------------------ #

    async def _position_monitor_loop(self) -> None:
        """
        Revisa posiciones abiertas cada POSITION_CHECK_INTERVAL segundos.
        Para cada una consulta el precio actual en CLOB y evalua si salir.
        """
        await asyncio.sleep(self.WARMUP_SECONDS + 30)  # esperar tras el warmup

        while self._running:
            await asyncio.sleep(cfg.POSITION_CHECK_INTERVAL)
            try:
                await self._check_all_positions()
            except Exception as e:
                log.error(f"Error en position_monitor_loop: {e}", exc_info=True)

    async def _check_all_positions(self) -> None:
        open_pos = self.portfolio.open_positions
        if not open_pos:
            return

        log.debug(f"Revisando {len(open_pos)} posicion(es) abierta(s)...")

        for pos in open_pos:
            try:
                await self._check_position(pos)
            except Exception as e:
                log.warning(f"Error revisando posicion {pos.position_id}: {e}")

    async def _check_position(self, pos: Position) -> None:
        """Consulta el precio actual del token y decide si salir."""
        # Precio al que podemos vender (mejor BID del CLOB)
        current_price = await self.poly_client.get_token_best_bid(pos.token_id)

        if current_price is None:
            log.debug(f"[{pos.position_id}] Sin bid disponible, saltando")
            return

        # Horas hasta expirar (estimado desde la apertura)
        from datetime import datetime, timezone
        elapsed_h = (datetime.utcnow() - pos.opened_at).total_seconds() / 3600
        remaining_h = max(0.0, pos.hours_to_expiry_at_entry - elapsed_h)

        upnl = pos.unrealized_pnl(current_price)
        upnl_pct = pos.unrealized_pnl_pct(current_price) * 100
        log.debug(
            f"[{pos.position_id}] {pos.crypto_symbol} {pos.outcome_label} "
            f"price={current_price:.4f} upnl={upnl:+.2f}({upnl_pct:+.1f}%) "
            f"exp={remaining_h:.1f}h TP={pos.take_profit_price:.4f} SL={pos.stop_loss_price:.4f}"
        )

        reason: Optional[ExitReason] = pos.check_exit_signal(current_price, remaining_h)
        if reason:
            await self._execute_exit(pos, current_price, reason)

    # ------------------------------------------------------------------ #
    # Ejecucion de ordenes                                                 #
    # ------------------------------------------------------------------ #

    async def _execute_entry(self, opp: HedgeOpportunity) -> None:
        """Calcula tamaño, coloca orden de compra y registra posicion."""
        size_usdc = self.portfolio.calculate_position_size(opp)
        if size_usdc < cfg.MIN_ORDER_SIZE:
            log.warning(f"Tamaño calculado {size_usdc:.2f} USDC < minimo. Saltando.")
            return

        log.info(
            f"ENTRADA: {opp.market.crypto_symbol} {opp.outcome_label} "
            f"{size_usdc:.2f} USDC @ {opp.market_price:.4f} | "
            f"fair={opp.fair_price:.4f} edge={opp.edge:+.4f} ev={opp.expected_value:.3f}"
        )

        result = await self.poly_client.buy_usdc(
            token_id=opp.token_id,
            usdc_amount=size_usdc,
            price=opp.market_price,
        )

        if result.success:
            pos = self.portfolio.open_position(
                opportunity=opp,
                order_id=result.order_id,
                size_usdc=size_usdc,
            )
            log.info(f"Posicion registrada: {pos.position_id}")
        else:
            log.error(f"Orden de entrada fallida: {result.error}")

    async def _execute_exit(
        self, pos: Position, current_price: float, reason: ExitReason
    ) -> None:
        """Vende todos los shares de una posicion y la cierra."""
        emoji_map = {
            "take_profit": "TAKE-PROFIT",
            "stop_loss":   "STOP-LOSS",
            "time_exit":   "TIME-EXIT",
        }
        log.info(
            f"{emoji_map[reason]} [{pos.position_id}] "
            f"{pos.crypto_symbol} {pos.outcome_label} | "
            f"Vendiendo {pos.shares:.4f} shares @ {current_price:.4f} "
            f"(entry={pos.entry_price:.4f})"
        )

        # Usar un precio ligeramente inferior al bid para asegurar ejecucion
        sell_price = round(current_price * 0.995, 4)

        result = await self.poly_client.sell_shares(
            token_id=pos.token_id,
            shares=pos.shares,
            min_price=sell_price,
        )

        if result.success:
            self.portfolio.close_position(pos.position_id, current_price, reason)
        else:
            log.error(
                f"Fallo al vender {pos.position_id}: {result.error}. "
                f"Se reintentara en el proximo ciclo."
            )

    # ------------------------------------------------------------------ #
    # Loops auxiliares                                                     #
    # ------------------------------------------------------------------ #

    async def _on_ticker(self, ticker: TickerData) -> None:
        log.debug(f"[{ticker.symbol}] ${ticker.price:,.2f}")

    async def _balance_loop(self) -> None:
        while self._running:
            await asyncio.sleep(60)
            try:
                balance = await self.poly_client.get_usdc_balance()
                self.portfolio.update_balance(balance)
                log.info(
                    f"Balance: {balance:.2f} USDC | "
                    f"En riesgo: {self.portfolio.capital_at_risk:.2f} | "
                    f"Disponible: {self.portfolio.available_capital:.2f}"
                )
            except Exception as e:
                log.warning(f"Error actualizando balance: {e}")

    async def _refresh_markets(self) -> None:
        log.info("Actualizando mercados Polymarket...")
        try:
            markets = await self.poly_client.fetch_crypto_markets(cfg.TRACKED_SYMBOLS)
            self._markets = markets
            self._last_market_refresh = time.time()
            by_sym: Dict[str, int] = {}
            for m in markets:
                s = m.crypto_symbol or "?"
                by_sym[s] = by_sym.get(s, 0) + 1
            summary = " | ".join(f"{k}:{v}" for k, v in sorted(by_sym.items()))
            log.info(f"Mercados: {len(markets)} total | {summary}")
        except Exception as e:
            log.error(f"Error actualizando mercados: {e}")
