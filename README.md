# CivicResolve Pune

An academic civic complaint prioritization and duplicate review prototype. It is not an official Pune Municipal Corporation service. Seeded records are fictional and marked as demonstration data.

## Features

- Flask web app with SQLite persistence.
- C++17 command-line engine for hash indexing, Levenshtein duplicate scoring, priority scoring, merge sorting, max-heap ranking and measured benchmarks.
- DSA Lab with step-through merge-sort and priority-queue walkthroughs.
- Administrator review is required before reports are grouped; complaint records are preserved.
- Complaint registration, search/filter, status updates, duplicate review, issue queue and analytics.

## Setup on macOS

Requires Python 3.9+ and a C++17 compiler. This workspace was verified with Python 3.9.6 and Apple clang 21.0.0. Check using `python3 --version` and `clang++ --version`. No Homebrew assumption is made.

```sh
# Run these commands from this project directory (the folder containing README.md).
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
make -C cpp
python scripts/initialize_database.py
python scripts/seed_demo_data.py
python -m flask --app app run --host 127.0.0.1
```

Open http://127.0.0.1:5001; stop with Ctrl-C. `./run.sh` builds and safely initializes the DB, then starts Flask without resetting data. Port 5001 avoids macOS Control Center's common port 5000 listener. Set `PORT=5000 ./run.sh` to override when that port is free. Reset only with `python scripts/reset_demo_data.py --yes`. C++ tests: `make -C cpp test`; Python tests: `.venv/bin/python -m unittest discover -s tests -v`.

## Structure

`app/` Flask routes, validation, database and services; `cpp/` algorithms and tab-separated process interface; `scripts/` database and demo-data lifecycle; `docs/` explanations. The compact structure avoids empty placeholder files.

The measured comparison is available in the app at **Analytics → Run DSA benchmark** and directly from the engine with `printf 'benchmark\n' | cpp/build/civic_engine`. It runs synthetic workloads at 100, 500, 1,000 and 5,000 rows and reports nanoseconds; it does not modify the database.

## Limitations

Local demo only; no authentication, no verified coordinates/wards and no official municipal connection. Matching is transparent English-text suggestion, not proof. Locality names are labels. Benchmarks are synthetic microbenchmarks and vary by machine and load.
