# Project overview

CivicResolve is a local academic prototype for organizing community maintenance reports. Residents or demo users record category, free-text description, Pune locality, landmark, severity and estimated impact. Staff can compare suggested duplicates, confirm/reject them, and view grouped issues in a transparent priority queue.

## Scope and requirements

Functional scope: complaint capture/search/filter, candidate generation, manual duplicate decisions, issue grouping, status audit, priority ranking and database-derived counts. Non-functional scope: local operation, parameterized SQL, foreign-key constraints, responsive HTML and explainable deterministic algorithms.

Assumptions: locality labels are user supplied and are not verified ward/geospatial data. Impact estimates are approximate. A group severity is the maximum member severity; group impact is the maximum member estimate to avoid summing potentially overlapping people. Prototype limitations: no authentication, no external service, no location verification, English-only matching, and synthetic microbenchmarks that may not predict production workloads.
