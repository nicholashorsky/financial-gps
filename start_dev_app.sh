#!/usr/bin/env bash
set -euo pipefail

project_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
streamlit_bin="$project_dir/.venv/bin/streamlit"

if [[ ! -x "$streamlit_bin" ]]; then
    echo "Financial GPS virtual environment was not found at $project_dir/.venv."
    echo "Create it and install dependencies with:"
    echo "  python3 -m venv .venv"
    echo "  .venv/bin/pip install -r requirements-dev.txt"
    exit 1
fi

export FINANCIAL_GPS_TEST_LOGIN=1
cd "$project_dir"

echo "Starting Financial GPS with the beta test login enabled..."
echo "Your browser should open http://localhost:8501 automatically."
echo "Press Ctrl+C here to stop the application."

exec "$streamlit_bin" run app.py \
    --server.headless=false \
    --server.showEmailPrompt=false \
    --browser.gatherUsageStats=false
