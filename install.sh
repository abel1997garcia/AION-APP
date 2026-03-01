#!/bin/bash
# ============================================================
# AION Bot - Script de instalacion para VPS Linux (Lituania)
# ============================================================
set -e

echo "==> Actualizando sistema..."
apt-get update -qq && apt-get install -y -qq python3 python3-pip python3-venv git

echo "==> Creando entorno virtual..."
python3 -m venv venv
source venv/bin/activate

echo "==> Instalando dependencias..."
pip install --upgrade pip -q
pip install -r requirements.txt -q

echo "==> Configurando .env..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo ""
    echo "  IMPORTANTE: Edita el archivo .env con tu PRIVATE_KEY:"
    echo "  nano .env"
    echo ""
fi

echo "==> Creando directorio de logs..."
mkdir -p logs

echo ""
echo "=============================="
echo "  Instalacion completada!"
echo "=============================="
echo ""
echo "Proximos pasos:"
echo "  1. nano .env                        # configurar tu wallet"
echo "  2. source venv/bin/activate"
echo "  3. python main.py --dry-run         # probar sin operar"
echo "  4. python main.py                   # operacion real"
echo ""
echo "Para ejecutar en background con systemd:"
echo "  sudo cp aion-bot.service /etc/systemd/system/"
echo "  sudo systemctl enable aion-bot && sudo systemctl start aion-bot"
