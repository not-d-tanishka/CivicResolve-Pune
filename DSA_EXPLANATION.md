# DSA explanation

## Hash-map lookup

The executable builds `std::unordered_map<string,size_t>` from complaint ID to its row index during a duplicate scan. Insert uses `emplace`, so an existing key is not overwritten. This uses the standard library hash table (not a newly invented hash function): expected lookup/insertion O(1), worst-case O(n) when keys collide. SQLite remains persistent source of truth.

## Text similarity and candidate reduction

`clean` lowercases ASCII alphanumeric characters and collapses punctuation/spacing. `distance` uses Levenshtein dynamic programming, with two rows: insertion, deletion and substitution choose the minimum edit cost. `similarity = 1 - distance/max(lengths)`; two empty normalized values score 1. Category and locality must match before text work. Description similarity and landmark similarity form `0.65*description + 0.35*landmark`; score at least 0.35 is a review suggestion. It never auto-groups. English ASCII normalization is intentionally limited; Marathi is not translated.

## Priority and heap

Severity component is severity on 1–5 mapped to 0–10 using `(severity-1)*2.5`; impact component is min(10, affected/10); waiting component is min(10, age_days/7). Final score is `0.50*severity + 0.30*impact + 0.20*waiting`, on 0–10. C++ `MaxHeap` ranks higher score first; equal scores break by ascending issue ID. The current web service recalculates using this C++ scoring rule before display. C++ process invocation is part of end-to-end overhead.

## Merge sort and benchmark

The C++ `merge_sort` recursively divides a vector into halves, sorts each half, and merges the ordered halves into a scratch vector. It is stable because equal values are taken from the left half first. Time is O(n log n) and auxiliary storage is O(n). The controlled benchmark runs deterministic synthetic inputs at 100, 500, 1,000 and 5,000 rows. It compares 100 linear and hash lookups, average merge-sort duration, average heap insertion/removal, and average duplicate scan duration over three runs. These are measured observations, not guaranteed performance.

## Complexity

Pair scan considers O(n²) pairs in the worst case; category/locality checks reduce expensive text comparisons in ordinary data but do not remove that worst case. Levenshtein takes O(mn) time and O(min(m,n)) space (the code uses two rows proportional to the second string length). Heap push/pop O(log n), storage O(n). Hash lookup average O(1), worst O(n). Database query and process-launch costs are separate from these in-memory bounds.
