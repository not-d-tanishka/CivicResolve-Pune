# Line-by-line guide

This guide follows the meaningful source groups and function execution order. Blank lines and closing braces are omitted. The small project deliberately keeps each module short; read it alongside the named source file.

## `cpp/src/main.cpp`

- Standard headers provide algorithms, character handling, math, streams, strings, hash map and vectors.
- `Complaint` stores a public ID and the four fields used in comparison. It is plain data; no heap ownership is involved.
- `clean` loops over bytes, lowercases ASCII letters, keeps digits and letters, and replaces runs of punctuation/whitespace with one space. The `space` flag prevents repeated spaces. Its limitation is byte-oriented English normalization.
- `distance` first swaps arguments when needed so the second string is shorter, then allocates previous/current DP rows. Initial previous row represents converting empty text to each prefix. Each cell chooses insert/delete/substitute. Swapping rows retains O(min(m,n)) memory.
- `merge_sort` stops on vectors of size zero or one, recursively sorts each half, merges values in order into the scratch vector, and copies the merged range back. The scratch vector avoids repeated allocations, while recursion uses logarithmic stack depth.
- `elapsed_ns` wraps a callable in `high_resolution_clock` start/stop timestamps and returns the elapsed nanoseconds.
- `run_benchmark` creates fixed-size synthetic workloads. It times repeated linear and hash lookups, merge sort, max-heap insertion/removal, and the category/locality-filtered similarity scan. It prints a tab-separated header and results for 100, 500, 1,000 and 5,000 rows; the benchmark does not write to SQLite.
- `similarity` normalizes both inputs, finds the longer normalized length, special-cases zero to avoid division by zero, then returns one minus normalized edit distance.
- `Issue` pairs the ranking key with a numeric score. `MaxHeap::higher` orders greater scores first and breaks ties using ascending IDs.
- `MaxHeap::push` appends then bubbles upward; `pop` removes the root, moves the final item to root and sifts downward. Empty-pop is not called by the loop, which checks `empty()` first.
- `main` reads the first input line as an action and rejects absent/unknown actions with a nonzero return and stderr message.
- In `score`, stream extraction validates the three integers and guards severity, impact and age. Each component is capped/normalized and the weighted sum is printed. C++ caller parses the numeric response.
- In `duplicates`, each tab-separated row becomes a complaint. The unordered map indexes IDs; the pair loops apply the category/locality gates before calculating text/landmark similarities. A score threshold emits an unconfirmed candidate row; no database is modified by C++.
- In `rank`, pairs of ID/score are read into the heap and popped in deterministic priority order. Python supplies the persisted issue scores and uses the returned order in the priority queue.
- In `benchmark`, the engine runs the controlled synthetic measurements and prints tab-separated nanosecond durations.
- In `selftest`, the executable checks hash-map insert/duplicate/find/missing/update/remove behavior, edit distance and empty-string similarity, merge-sort ordering, heap removal and tie ordering. It exits nonzero with a focused stderr message if an invariant fails.

## Python modules

- `app/database.py`: schema constants hold DDL and constraints. `connect` creates parent folders, creates a SQLite connection, sets row objects, and enables FK enforcement for that connection. `get_db` caches one connection per Flask request. `close_db` releases it. `init_db` executes idempotent DDL.
- `app/validation.py`: category/locality/status tuples are allowlists. `validate_complaint` parses integer fields defensively, checks length, enum and range constraints, and returns both error messages and normalized values. `valid_id` constrains public route IDs to a prefix and six digits.
- `app/cpp_engine.py`: resolves the compiled binary path, checks it exists, creates the documented text protocol, invokes a subprocess with timeout/captured output, rejects nonzero exit, then parses numeric or tab-separated response rows. It raises `EngineError` so routes can show a setup message.
- `app/services.py`: `recalculate_priorities` computes issue age, invokes actual C++ score code, and updates the persisted score. `generate_candidates` sends complaints through C++, maps returned public IDs back to internal integer keys, and inserts canonical pairs. `review_candidate` uses `BEGIN IMMEDIATE`; rejection changes review fields only, while confirmation checks category/locality and existing memberships, creates or reuses one issue, links both originals, recomputes aggregate max severity/impact and priority, updates review state, then commits. Any exception rolls the entire transaction back.
- `app/routes.py`: `ensure_schema` creates the schema before requests; `close` ends request connections. Page functions use bound query parameters. POST handlers validate form values and IDs before changing state. Templates autoescape values. Duplicate decisions only accept the two known actions; issue/complaint detail endpoints return 404 on invalid IDs.
- `app/__init__.py`: factory sets local configuration and registers the route blueprint; module-level `app` supports Flask CLI.
- `scripts/initialize_database.py`: creates schema then inserts known locality labels without coordinates.
- `scripts/seed_demo_data.py`: uses fixed random seed and inserts records only if no simulated rows exist. Every seeded row has the demo flag set and fictitious descriptions.
- `scripts/reset_demo_data.py`: requires explicit `--yes`, deletes candidates attached to demo complaints then only rows marked demo, in one transaction.

## Browser templates and styling

`base.html` provides navigation, visible disclaimer and flashed messages; each page extends it. Forms use POST for state changes and Jinja autoescaping. `style.css` defines colors, spacing, responsive tables/cards and narrow-screen layout. Dashboard and analytics values are read from SQL, not constants.
