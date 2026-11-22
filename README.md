# CivicResolve Pune

A small college project (FDS course) for handling civic complaints like potholes, broken streetlights and garbage. It finds complaints that probably report the same problem, lets an admin confirm them, and ranks the problems by priority.

This is not an official Pune Municipal Corporation service. All the sample data is made up.

## What it does

- Register complaints, search and filter them, and update their status
- Suggests possible duplicate complaints, and an admin confirms or rejects each one (nothing is merged automatically, and the original complaints are never deleted)
- Ranks issues in a priority queue
- Shows simple statistics
- DSA Lab page that walks through merge sort and the priority queue step by step

The web app is built with Flask and SQLite. The data structure work (hash map, Levenshtein distance, priority score, merge sort, max-heap and the benchmark) is written in C++17 as a command-line program that the Flask app calls.

## How to run it (macOS)

You need Python 3.9 or newer and a C++17 compiler. Check with `python3 --version` and `clang++ --version`.

Run these from the project folder (the one with this README):

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
make -C cpp
python scripts/initialize_database.py
python scripts/seed_demo_data.py
python -m flask --app app run --host 127.0.0.1
```

Then open http://127.0.0.1:5001 in your browser. Press Ctrl-C to stop.

Shortcut: `./run.sh` builds the C++ part, sets up the database and starts the app without wiping your data. It uses port 5001 because macOS often uses port 5000 for something else. If 5000 is free, you can use `PORT=5000 ./run.sh`.

To reset the demo data: `python scripts/reset_demo_data.py --yes`

## Tests

- C++: `make -C cpp test`
- Python: `.venv/bin/python -m unittest discover -s tests -v`

## Project structure

- `app/` Flask routes, validation, database and services
- `cpp/` the C++ engine
- `scripts/` database setup and demo data
- `docs/` explanations of the design, algorithms and testing

## Benchmark

You can run it in the app (Analytics, then Run DSA benchmark) or from the terminal:

```sh
printf 'benchmark\n' | cpp/build/civic_engine
```

It tests made-up data with 100, 500, 1,000 and 5,000 rows and prints times in nanoseconds. It doesn't change the database. The results depend on your computer.

## Limitations

- Local demo only, with no login
- No real ward or location data; locality names are just labels
- Duplicate matching only works on English text, and it only suggests matches, so a person has to decide
- The benchmark uses synthetic data, so don't treat the numbers as exact
