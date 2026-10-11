#!/usr/bin/env bash
set -euo pipefail

JARVIS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=== J.A.R.V.I.S. setup ==="
echo ""

# --- backend ---
echo "[1/4] Setting up backend (Python venv + dependencies)..."
cd "$JARVIS_DIR/backend"
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet

if [[ ! -f .env ]]; then
  cp .env.example .env
  echo "      Created backend/.env from .env.example -- edit it if you need to"
  echo "      change the port, model, or add cloud AI API keys."
fi

echo "[2/4] Running database migrations..."
alembic upgrade head

echo "[3/4] Setting up frontend (npm dependencies)..."
cd "$JARVIS_DIR/frontend"
npm install --silent

echo "[4/4] Checking for Ollama..."
if command -v ollama >/dev/null 2>&1; then
  echo "      Ollama is installed."
  if ! ollama list 2>/dev/null | grep -q "llama3.2:3b"; then
    echo "      Pulling the default model (llama3.2:3b) -- this can take a while..."
    ollama pull llama3.2:3b
  fi
else
  echo "      Ollama is NOT installed. Install it from https://ollama.com if you"
  echo "      want local AI features. The app still works without it (falls back"
  echo "      to deterministic, non-AI behavior)."
fi

echo ""
echo "=== Setup complete ==="
echo "Run it with: ./start.sh"
