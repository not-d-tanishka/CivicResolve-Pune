# Complexity analysis

| Operation | Structure | Expected complexity |
|---|---|---|
| Linear scan | Array/vector | O(n) |
| Hash-map lookup/insert | `unordered_map` | Average O(1), worst O(n) |
| Levenshtein | Two-row dynamic programming | O(mn) time, O(min(m,n)) auxiliary space |
| Candidate scan | Pair loop + text distance | O(n² × string-distance) worst case |
| Heap insertion/removal | Binary max-heap | O(log n) |
| Heap storage | Vector | O(n) |
| Merge sort | Recursive merge sort | O(n log n) time, O(n) auxiliary space |
| Dijkstra | Not implemented | Not applicable |

The application uses the C++ heap to rank persisted issue scores. Category and locality filtering reduce similarity evaluations in many datasets, but all pairs may still pass those filters. Database indexing/query planning, process startup and web rendering are not captured by these bounds.

## Observed synthetic benchmark

Measured with Apple clang 21.0.0, `-O2`, C++17, arm64 macOS, on 2026-11-18. Run using `printf 'benchmark\\n' | cpp/build/civic_engine`. Values are nanoseconds. Linear and hash columns each time 100 lookups of the last key; other columns are averages of three runs. The duplicate scan uses deterministic synthetic category/locality/text values and includes filtering plus similarity computations.

| Rows | Linear search (100 lookups) | Hash lookup (100) | Merge sort | Heap insert+pop | Duplicate scan |
|---:|---:|---:|---:|---:|---:|
| 100 | 5,167 | 542 | 2,361 | 12,166 | 172,833 |
| 500 | 24,375 | 291 | 10,652 | 61,986 | 7,572,125 |
| 1,000 | 47,333 | 459 | 22,722 | 138,569 | 31,983,694 |
| 5,000 | 227,333 | 500 | 136,319 | 1,066,819 | 829,788,486 |

These are single-machine observations, not guarantees; small hash timings are especially sensitive to timer granularity and system load. Duplicate generation grows quickly even after category/locality gates. Dijkstra's algorithm is not part of this system and is not implemented.
