# Testing report

## Executed checks

- `make -C cpp clean all test`: PASS; C++17 build and self-tests check hash-map CRUD behavior, Levenshtein edge cases, merge sort, max-heap tie ordering, scoring and duplicate filtering.
- `.venv/bin/python -m unittest discover -s tests -v`: PASS; all 12 tests passed, including four real Python-to-C++ subprocess tests and four Flask route tests.
- Flask route coverage: dashboard, complaint registration and validation, duplicate proposal, confirmation and rejection, original report preservation, issue status update and persistence through a new Flask app instance, database-backed analytics, and the DSA Lab page/script.
- SQLite coverage: check constraints, unique complaint IDs, foreign keys, canonical candidate ordering, one-group-per-complaint, and transaction rollback.
- `PYTHONPYCACHEPREFIX=/private/tmp/civicresolve-pycache .venv/bin/python -m py_compile app/*.py scripts/*.py tests/*.py`: PASS; all Python source compiles.
- `python scripts/initialize_database.py`: PASS; schema and locality rows initialized.
- `python scripts/seed_demo_data.py`: PASS; inserted 50 fictional complaints. Running it again returned “Demo complaints already exist; no rows inserted.”
- `./run.sh`: PASS; compiled check, initialized the database, and started Flask. Browser verification showed the dashboard and 50 reports. The launcher now defaults to port 5001 to avoid macOS Control Center's port 5000 listener.
- C++ benchmark executed for 100, 500, 1,000 and 5,000 synthetic complaints; measured values are recorded in `COMPLEXITY_ANALYSIS.md`.

## Scope limits

The end-to-end acceptance scenario was exercised through Flask's test client with a clean temporary SQLite database; the seeded 50-record database was also opened in the running app. A separate restart of the live server was not performed, but persistence was verified by creating a new Flask app instance against the same test database file. The application remains a local educational prototype without authentication or verified municipal data.
