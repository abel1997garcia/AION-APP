#!/usr/bin/env python3
"""
AION Crypto Trading Bot
=======================
Punto de entrada principal.

Uso:
  python main.py              # Modo trading real
  python main.py --dry-run    # Modo simulacion (no ejecuta ordenes)
  python main.py --status     # Ver estado del portfolio

Requisitos previos:
  1. cp .env.example .env && nano .env  (configurar PRIVATE_KEY)
  2. pip install -r requirements.txt
"""
import argparse
import asyncio
import os
import signal
import sys

# Agregar el directorio raiz al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import cfg
from src.bot import TradingBot
from src.logger import setup_logger

log = setup_logger("main")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="AION - Crypto Trading Bot (Binance → Polymarket Hedge)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simular operaciones sin ejecutarlas realmente",
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Mostrar estado del portfolio y salir",
    )
    parser.add_argument(
        "--symbols",
        type=str,
        help="Sobrescribir simbolos del .env (ej: BTC,ETH)",
    )
    return parser.parse_args()


async def run_bot(dry_run: bool = False) -> None:
    bot = TradingBot()

    if dry_run:
        log.warning("MODO DRY-RUN activado: las ordenes NO se ejecutaran en Polymarket")
        # Monkey-patch para simular ordenes
        from src.polymarket.client import OrderResult
        async def fake_place_order(token_id, side, size, price, order_type="GTC"):
            log.info(f"[DRY-RUN] Orden simulada: {side} {size:.2f} USDC @ {price:.4f}")
            return OrderResult(success=True, order_id="dry-run-001", error=None,
                               size=size, price=price, side=side)
        bot.poly_client.place_order = fake_place_order

    # Manejar señales del sistema para shutdown limpio
    loop = asyncio.get_running_loop()

    def shutdown_handler():
        log.info("Señal de shutdown recibida. Deteniendo bot...")
        asyncio.create_task(bot.stop())

    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, shutdown_handler)
        except NotImplementedError:
            pass  # Windows no soporta add_signal_handler

    try:
        await bot.start()
    except KeyboardInterrupt:
        log.info("Interrupcion de teclado.")
    finally:
        await bot.stop()


def main() -> None:
    args = parse_args()

    # Sobrescribir simbolos si se pasan por CLI
    if args.symbols:
        cfg.TRACKED_SYMBOLS = [s.strip().upper() for s in args.symbols.split(",")]

    # Validar configuracion (excepto en dry-run que no necesita private key real)
    if not args.dry_run and not args.status:
        try:
            cfg.validate()
        except ValueError as e:
            log.error(str(e))
            sys.exit(1)
    elif args.dry_run:
        log.info("Dry-run: saltando validacion de PRIVATE_KEY")

    if args.status:
        log.info("Modo --status: consultando portfolio actual...")
        # En una implementacion futura: leer estado guardado en disco
        log.info("(Funcionalidad de status en desarrollo)")
        return

    log.info(f"Iniciando bot | simbolos={cfg.TRACKED_SYMBOLS} | dry_run={args.dry_run}")
    asyncio.run(run_bot(dry_run=args.dry_run))


if __name__ == "__main__":
    main()
