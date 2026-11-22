#!/bin/sh
set -eu
if [ -x .venv/bin/python ]; then PYTHON=.venv/bin/python; else PYTHON=python3; fi
command -v "$PYTHON" >/dev/null || { echo 'Python 3 is required.' >&2; exit 1; }
"$PYTHON" -c 'import flask' 2>/dev/null || { echo 'Flask is missing. Run: python3 -m venv .venv && .venv/bin/python -m pip install -r requirements.txt' >&2; exit 1; }
if command -v clang++ >/dev/null; then CXX=${CXX:-clang++}; elif command -v g++ >/dev/null; then CXX=${CXX:-g++}; else echo 'Install a C++17 compiler.' >&2; exit 1; fi
export CXX
make -C cpp
"$PYTHON" scripts/initialize_database.py
PORT=${PORT:-5001}
"$PYTHON" -m flask --app app run --host 127.0.0.1 --port "$PORT"
