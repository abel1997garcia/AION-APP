"""
Gestor de portfolio y tamaño de posicion.

Logica de sizing proporcional basada en Kelly conservador:
  - Kelly fraction = edge / odds
  - Aplicamos un factor de descuento (0.25) para ser conservadores
  - Limite maximo configurable por operacion (MAX_POSITION_PCT)
  - El tamaño se escala proporcionalmente con la confianza de la señal
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional

from config import cfg
from src.analysis.hedge import HedgeOpportunity
from src.logger import setup_logger

log = setup_logger("portfolio")


@dataclass
class Position:
    position_id: str
    market_question: str
    token_id: str
    outcome_label: str
    crypto_symbol: str
    entry_price: float        # probabilidad al entrar
    size_usdc: float          # USDC apostados
    fair_price_at_entry: float
    confidence: float
    order_id: Optional[str]
    opened_at: datetime = field(default_factory=datetime.utcnow)
    closed: bool = False
    exit_price: Optional[float] = None
    pnl: Optional[float] = None

    @property
    def max_win(self) -> float:
        """Maximo ganado si resolucion correcta."""
        return self.size_usdc * (1.0 / self.entry_price - 1.0)

    @property
    def max_loss(self) -> float:
        """Maximo perdido si resolucion incorrecta."""
        return self.size_usdc

    def __str__(self) -> str:
        status = "ABIERTA" if not self.closed else f"CERRADA (PnL={self.pnl:+.2f})"
        return (
            f"[{self.crypto_symbol}] {self.outcome_label} "
            f"size={self.size_usdc:.2f} USDC @ {self.entry_price:.3f} | {status}"
        )


class PortfolioManager:
    """
    Gestiona posiciones abiertas y calcula tamaño optimo de cada operacion.
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
        """USDC actualmente en posiciones abiertas."""
        return sum(p.size_usdc for p in self.open_positions)

    @property
    def available_capital(self) -> float:
        return max(0.0, self.balance - self.capital_at_risk)

    def can_open_position(self, opportunity: HedgeOpportunity) -> bool:
        """Verifica si se puede abrir una nueva posicion."""
        if len(self.open_positions) >= cfg.MAX_OPEN_POSITIONS:
            log.warning(
                f"Maximo de posiciones abiertas ({cfg.MAX_OPEN_POSITIONS}) alcanzado"
            )
            return False

        # Verificar que no estamos ya en este mercado
        for pos in self.open_positions:
            if pos.token_id == opportunity.token_id:
                log.debug(f"Ya tenemos posicion en token {opportunity.token_id[:8]}")
                return False

        if self.available_capital < cfg.MIN_ORDER_SIZE:
            log.warning(
                f"Capital disponible insuficiente: {self.available_capital:.2f} USDC "
                f"< minimo {cfg.MIN_ORDER_SIZE}"
            )
            return False

        return True

    def calculate_position_size(self, opportunity: HedgeOpportunity) -> float:
        """
        Calcula el tamaño optimo de la posicion usando Kelly conservador.

        Kelly formula para apuestas binarias:
          f* = (p * b - q) / b
          donde: p = prob de ganar, q = 1-p, b = odds (ganancia por USDC arriesgado)

        Aplicamos descuento y limite maximo.
        """
        p = opportunity.fair_price          # prob estimada de ganar
        market_price = opportunity.market_price
        b = (1.0 / market_price) - 1.0     # ganancia neta por USDC si ganamos

        if b <= 0 or p <= 0:
            return 0.0

        q = 1.0 - p
        kelly_full = (p * b - q) / b

        # Kelly conservador
        kelly_conservative = kelly_full * cfg.KELLY_FRACTION

        # Escalar por confianza de la señal
        kelly_adjusted = kelly_conservative * opportunity.confidence

        # Limit por MAX_POSITION_PCT del portfolio total
        max_fraction = cfg.MAX_POSITION_PCT
        fraction = min(kelly_adjusted, max_fraction)
        fraction = max(0.0, fraction)

        # Calcular USDC
        raw_size = self.available_capital * fraction

        # Clamp entre min y max
        size = max(cfg.MIN_ORDER_SIZE, min(raw_size, cfg.MAX_ORDER_SIZE))

        # No apostar más de lo disponible
        size = min(size, self.available_capital)

        log.info(
            f"Sizing: kelly={kelly_full:.3f} conserv={kelly_conservative:.3f} "
            f"adj={kelly_adjusted:.3f} → {size:.2f} USDC "
            f"(balance={self.balance:.2f}, disponible={self.available_capital:.2f})"
        )
        return round(size, 2)

    def open_position(
        self,
        opportunity: HedgeOpportunity,
        order_id: Optional[str],
        actual_size: float,
    ) -> Position:
        self._position_counter += 1
        pos_id = f"pos_{self._position_counter:04d}"

        position = Position(
            position_id=pos_id,
            market_question=opportunity.market.question,
            token_id=opportunity.token_id,
            outcome_label=opportunity.outcome_label,
            crypto_symbol=opportunity.signal.symbol,
            entry_price=opportunity.market_price,
            size_usdc=actual_size,
            fair_price_at_entry=opportunity.fair_price,
            confidence=opportunity.confidence,
            order_id=order_id,
        )

        self.positions[pos_id] = position
        log.info(f"Posicion abierta: {position}")
        return position

    def close_position(self, pos_id: str, exit_price: float) -> Optional[Position]:
        position = self.positions.get(pos_id)
        if not position or position.closed:
            return None

        position.closed = True
        position.exit_price = exit_price

        # PnL aproximado: si ganamos (exit=1.0), si perdemos (exit=0.0)
        if exit_price >= 0.99:
            position.pnl = position.max_win
        elif exit_price <= 0.01:
            position.pnl = -position.max_loss
        else:
            position.pnl = position.size_usdc * (exit_price / position.entry_price - 1.0)

        self.balance += position.pnl if position.pnl else 0.0
        log.info(f"Posicion cerrada: {position}")
        return position

    def print_summary(self) -> None:
        log.info("=" * 60)
        log.info(f"PORTFOLIO SUMMARY | Balance: {self.balance:.2f} USDC")
        log.info(f"  Posiciones abiertas: {len(self.open_positions)}")
        log.info(f"  Capital en riesgo:   {self.capital_at_risk:.2f} USDC")
        log.info(f"  Capital disponible:  {self.available_capital:.2f} USDC")
        for pos in self.open_positions:
            log.info(f"  → {pos}")
        closed = [p for p in self.positions.values() if p.closed]
        if closed:
            total_pnl = sum(p.pnl or 0 for p in closed)
            log.info(f"  Posiciones cerradas: {len(closed)} | PnL total: {total_pnl:+.2f} USDC")
        log.info("=" * 60)
