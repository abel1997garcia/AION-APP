#!/usr/bin/env bash
# =============================================================================
# AION Bot – VPS Setup Script (Ubuntu/Debian)
# Run once on the Lithuania VPS:  bash setup.sh
# =============================================================================
set -euo pipefail

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
BOT_USER="${SUDO_USER:-$USER}"

echo "=== AION Arbitrage Bot – setup ==="
echo "Repo: $REPO_DIR | User: $BOT_USER"

# ── 1. System packages ──────────────────────────────────────────────────────
echo "[1/6] Installing system packages..."
apt-get update -qq
apt-get install -y python3 python3-pip python3-venv git curl

# ── 2. Python virtual environment ───────────────────────────────────────────
echo "[2/6] Creating Python venv..."
python3 -m venv "$REPO_DIR/.venv"
source "$REPO_DIR/.venv/bin/activate"
pip install --upgrade pip wheel

# ── 3. Python dependencies ──────────────────────────────────────────────────
echo "[3/6] Installing Python dependencies..."
pip install -r "$REPO_DIR/requirements.txt"

# ── 4. Install the bot as an editable package ───────────────────────────────
echo "[4/6] Installing bot package..."
pip install -e "$REPO_DIR"

# ── 5. Environment file ─────────────────────────────────────────────────────
if [ ! -f "$REPO_DIR/.env" ]; then
    echo "[5/6] Creating .env from .env.example (EDIT THIS FILE!)"
    cp "$REPO_DIR/.env.example" "$REPO_DIR/.env"
    echo ""
    echo "  *** ACTION REQUIRED ***"
    echo "  Edit $REPO_DIR/.env and set your POLYMARKET_PRIVATE_KEY"
    echo ""
else
    echo "[5/6] .env already exists – skipping copy"
fi

# Create logs directory
mkdir -p "$REPO_DIR/logs"

# ── 6. Systemd service ──────────────────────────────────────────────────────
echo "[6/6] Installing systemd service..."
VENV_PYTHON="$REPO_DIR/.venv/bin/python"

cat > /etc/systemd/system/aion-bot.service << EOF
[Unit]
Description=AION Arbitrage Bot (Binance/Polymarket)
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=$BOT_USER
WorkingDirectory=$REPO_DIR
ExecStart=$VENV_PYTHON -m trading_bot.main
Restart=on-failure
RestartSec=15
StandardOutput=journal
StandardError=journal
SyslogIdentifier=aion-bot
# Security hardening
NoNewPrivileges=true
PrivateTmp=true

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable aion-bot.service

echo ""
echo "=== Setup complete ==="
echo ""
echo "Next steps:"
echo "  1. Edit .env:               nano $REPO_DIR/.env"
echo "  2. Start the bot:           systemctl start aion-bot"
echo "  3. Watch logs:              journalctl -u aion-bot -f"
echo "  4. Stop the bot:            systemctl stop aion-bot"
echo "  5. Disable autostart:       systemctl disable aion-bot"
echo ""
