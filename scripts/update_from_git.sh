#!/usr/bin/env bash
set -euo pipefail

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$APP_DIR"

git fetch origin main
git pull --ff-only origin main

python3 -m venv .venv
. .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo "BeachScore AI atualizado em $APP_DIR"
echo "Inicie com: .venv/bin/python app.py"
