"""
Gestor de portfolio.

Tracking de posiciones abiertas con logica de salida:
  - Take-profit: cuando hemos capturado >= TAKE_PROFIT_RATIO del edge
  - Stop-loss:   cuando la posicion cae >= STOP_LOSS_RATIO del capital apostado
  - Time-exit:   cuando quedan < MIN_HOURS_TO_EXPIRY horas para expirar

Sizing proporcional con Kelly conservador × confianza MTF.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Literal, Optional

from config import cfg
from src.analysis.hedge import HedgeOpportunity
from src.logger import setup_logger

log = setup_logger("portfolio")

ExitReason = Literal["take_profit", "stop_loss", "time_exit"]


@dataclass
class Position:
    position_id: str
    market_question: str
    token_id: str
    outcome_label: str
    crypto_symbol: str
    entry_price: float        # probabilidad al entrar (0-1)
    shares: float             # shares del token que tenemos
    size_usdc: float          # USDC apostados = shares × entry_price
    fair_price_at_entry: float
    edge_at_entry: float      # fair_price - entry_price al entrar
    confidence: float
    hours_to_expiry_at_entry: float
    order_id: Optional[str]
    opened_at: datetime = field(default_factory=datetime.utcnow)
    closed: bool = False
    exit_price: Optional[float] = None
    exit_reason: Optional[ExitReason] = None
    pnl: Optional[float] = None

    # ── umbrales de salida pre-calculados ──────────────────────────────
    @property
    def take_profit_price(self) -> float:
        """Precio al que queremos salir para capturar TAKE_PROFIT_RATIO del edge."""
        return self.entry_price + self.edge_at_entry * cfg.TAKE_PROFIT_RATIO

    @property
    def stop_loss_price(self) -> float:
        """Precio por debajo del cual ejecutamos stop-loss."""
        return self.entry_price * (1.0 - cfg.STOP_LOSS_RATIO)

    # ── valor actual ───────────────────────────────────────────────────
    def current_value_usdc(self, current_price: float) -> float:
        """Valor de mercado de nuestra posicion en USDC."""
        return self.shares * current_price

    def unrealized_pnl(self, current_price: float) -> float:
        return self.current_value_usdc(current_price) - self.size_usdc

    def unrealized_pnl_pct(self, current_price: float) -> float:
        if self.size_usdc == 0:
            return 0.0
        return self.unrealized_pnl(current_price) / self.size_usdc

    # ── señal de salida ────────────────────────────────────────────────
    def check_exit_signal(
        self, current_price: float, hours_to_expiry: float
    ) -> Optional[ExitReason]:
        """
        Evalua si hay que salir de esta posicion.

        Orden de prioridad:
          1. Time-exit (evitar riesgo de resolucion desconocida)
          2. Take-profit (asegurar ganancias cuando Polymarket corrige)
          3. Stop-loss (limitar perdidas)
        """
        if hours_to_expiry <= cfg.MIN_HOURS_TO_EXPIRY:
            return "time_exit"

        if current_price >= self.take_profit_price:
            return "take_profit"

        if current_price <= self.stop_loss_price:
            return "stop_loss"

        return None

    def __str__(self) -> str:
        status = (
            "ABIERTA"
            if not self.closed
            else f"CERRADA [{self.exit_reason}] PnL={self.pnl:+.2f} USDC"
        )
        return (
            f"[{self.crypto_symbol}] {self.outcome_label} "
            f"{self.shares:.2f}sh @ {self.entry_price:.3f} "
            f"(tp={self.take_profit_price:.3f} sl={self.stop_loss_price:.3f}) | {status}"
        )


class PortfolioManager:
    """
    Gestiona posiciones y calcula tamaño optimo de cada operacion.
    """

    def __init__(self, initial_balance: float = 0.0):
        self.balance = initial_balance
        self.positions: Dict[str, Position] = {}
        self._position_counter = 0

    def update_balance(self, balance: float) -> None:
        self.balance = balance

    @property
    def open_positions(self) -> List[Position]:
        return [p for p in self.positions.values() if not p.closed]

    @property
    def capital_at_risk(self) -> float:
        return sum(p.size_usdc for p in self.open_positions)

    @property
    def available_capital(self) -> float:
        return max(0.0, self.balance - self.capital_at_risk)

    def can_open_position(self, opportunity: HedgeOpportunity) -> bool:
        if len(self.open_positions) >= cfg.MAX_OPEN_POSITIONS:
            log.warning(f"Max posiciones abiertas ({cfg.MAX_OPEN_POSITIONS}) alcanzado")
            return False
        for pos in self.open_positions:
            if pos.token_id == opportunity.token_id:
                log.debug(f"Ya tenemos posicion en token {opportunity.token_id[:10]}")
                return False
        if self.available_capital < cfg.MIN_ORDER_SIZE:
            log.warning(
                f"Capital insuficiente: {self.available_capital:.2f} USDC "
                f"< min {cfg.MIN_ORDER_SIZE}"
            )
            return False
        return True

    def calculate_position_size(self, opportunity: HedgeOpportunity) -> float:
        """
        Kelly conservador escalado por confianza MTF.
        Retorna USDC a apostar.
        """
        p = opportunity.fair_price
        market_price = opportunity.market_price
        b = (1.0 / market_price) - 1.0  # ganancia neta por USDC si ganamos

        if b <= 0 or p <= 0:
            return 0.0

        q = 1.0 - p
        kelly_full = (p * b - q) / b
        kelly_adj = kelly_full * cfg.KELLY_FRACTION * opportunity.confidence

        fraction = max(0.0, min(kelly_adj, cfg.MAX_POSITION_PCT))
        raw_size = self.available_capital * fraction
        size = max(cfg.MIN_ORDER_SIZE, min(raw_size, cfg.MAX_ORDER_SIZE))
        size = min(size, self.available_capital)

        log.info(
            f"Kelly sizing: full={kelly_full:.3f} adj={kelly_adj:.3f} "
            f"→ {size:.2f} USDC (disponible={self.available_capital:.2f})"
        )
        return round(size, 2)

    def open_position(
        self,
        opportunity: HedgeOpportunity,
        order_id: Optional[str],
        size_usdc: float,
    ) -> Position:
        self._position_counter += 1
        pos_id = f"pos_{self._position_counter:04d}"
        entry_price = opportunity.market_price
        shares = size_usdc / entry_price if entry_price > 0 else 0.0

        position = Position(
            position_id=pos_id,
            market_question=opportunity.market.question,
            token_id=opportunity.token_id,
            outcome_label=opportunity.outcome_label,
            crypto_symbol=opportunity.signal.symbol,
            entry_price=entry_price,
            shares=round(shares, 4),
            size_usdc=size_usdc,
            fair_price_at_entry=opportunity.fair_price,
            edge_at_entry=opportunity.edge,
            confidence=opportunity.confidence,
            hours_to_expiry_at_entry=opportunity.hours_to_expiry,
            order_id=order_id,
        )

        self.positions[pos_id] = position
        log.info(
            f"POSICION ABIERTA {pos_id}: {position} | "
            f"TP={position.take_profit_price:.4f} SL={position.stop_loss_price:.4f}"
        )
        return position

    def close_position(
        self,
        pos_id: str,
        exit_price: float,
        reason: ExitReason,
    ) -> Optional[Position]:
        position = self.positions.get(pos_id)
        if not position or position.closed:
            return None

        position.closed = True
        position.exit_price = exit_price
        position.exit_reason = reason
        # PnL = (exit_price - entry_price) × shares
        position.pnl = (exit_price - position.entry_price) * position.shares
        self.balance += position.pnl

        pnl_pct = (position.pnl / position.size_usdc * 100) if position.size_usdc else 0
        log.info(
            f"POSICION CERRADA {pos_id} [{reason.upper()}]: "
            f"PnL={position.pnl:+.2f} USDC ({pnl_pct:+.1f}%) | "
            f"entry={position.entry_price:.4f} exit={exit_price:.4f}"
        )
        return position

    def print_summary(self) -> None:
        closed = [p for p in self.positions.values() if p.closed]
        total_pnl = sum(p.pnl or 0 for p in closed)
        wins = sum(1 for p in closed if (p.pnl or 0) > 0)
        losses = len(closed) - wins

        log.info("=" * 65)
        log.info(f"PORTFOLIO SUMMARY | Balance: {self.balance:.2f} USDC")
        log.info(f"  Abiertas:   {len(self.open_positions)} | En riesgo: {self.capital_at_risk:.2f} USDC")
        log.info(f"  Disponible: {self.available_capital:.2f} USDC")
        for pos in self.open_positions:
            log.info(f"  → {pos}")
        if closed:
            win_rate = wins / len(closed) * 100
            log.info(
                f"  Cerradas:   {len(closed)} | PnL total: {total_pnl:+.2f} USDC | "
                f"Win rate: {win_rate:.0f}% ({wins}W/{losses}L)"
            )
        log.info("=" * 65)
