import os
import sqlite3
from flask import current_app, g, has_app_context

SCHEMA = """
CREATE TABLE IF NOT EXISTS locations(location_id INTEGER PRIMARY KEY, locality_name TEXT UNIQUE NOT NULL, description TEXT, latitude REAL, longitude REAL, is_demo_location INTEGER NOT NULL DEFAULT 1 CHECK(is_demo_location IN (0,1)));
CREATE TABLE IF NOT EXISTS complaints(id INTEGER PRIMARY KEY, complaint_id TEXT UNIQUE NOT NULL, category TEXT NOT NULL, description TEXT NOT NULL, locality TEXT NOT NULL, location_description TEXT NOT NULL, severity INTEGER NOT NULL CHECK(severity BETWEEN 1 AND 5), affected_people INTEGER NOT NULL CHECK(affected_people>=0), reported_at TEXT NOT NULL, status TEXT NOT NULL CHECK(status IN ('Pending','In Progress','Resolved')), reporter_reference TEXT, is_demo_data INTEGER NOT NULL DEFAULT 0 CHECK(is_demo_data IN (0,1)), created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS issues(id INTEGER PRIMARY KEY, issue_id TEXT UNIQUE NOT NULL, category TEXT NOT NULL, locality TEXT NOT NULL, location_description TEXT NOT NULL, summary TEXT NOT NULL, severity INTEGER NOT NULL CHECK(severity BETWEEN 1 AND 5), affected_people INTEGER NOT NULL CHECK(affected_people>=0), priority_score REAL NOT NULL DEFAULT 0, status TEXT NOT NULL CHECK(status IN ('Pending','In Progress','Resolved')), created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS issue_complaints(issue_id INTEGER NOT NULL REFERENCES issues(id) ON DELETE CASCADE, complaint_id INTEGER NOT NULL UNIQUE REFERENCES complaints(id) ON DELETE CASCADE, linked_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, linked_by TEXT NOT NULL, link_reason TEXT NOT NULL, PRIMARY KEY(issue_id,complaint_id));
CREATE TABLE IF NOT EXISTS duplicate_candidates(candidate_id INTEGER PRIMARY KEY, complaint_id_a INTEGER NOT NULL REFERENCES complaints(id), complaint_id_b INTEGER NOT NULL REFERENCES complaints(id), category_match INTEGER NOT NULL CHECK(category_match IN (0,1)), location_match INTEGER NOT NULL CHECK(location_match IN (0,1)), similarity_score REAL NOT NULL CHECK(similarity_score BETWEEN 0 AND 1), overall_match_score REAL NOT NULL CHECK(overall_match_score BETWEEN 0 AND 1), review_status TEXT NOT NULL DEFAULT 'Pending' CHECK(review_status IN ('Pending','Confirmed','Rejected')), reviewed_at TEXT, review_reason TEXT, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, CHECK(complaint_id_a<complaint_id_b), UNIQUE(complaint_id_a,complaint_id_b));
CREATE TABLE IF NOT EXISTS status_history(history_id INTEGER PRIMARY KEY, complaint_id INTEGER REFERENCES complaints(id), issue_id INTEGER REFERENCES issues(id), old_status TEXT, new_status TEXT NOT NULL, changed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, changed_by TEXT NOT NULL, note TEXT, CHECK((complaint_id IS NOT NULL)+(issue_id IS NOT NULL)=1));
CREATE INDEX IF NOT EXISTS idx_complaint_category ON complaints(category);
CREATE INDEX IF NOT EXISTS idx_complaint_locality ON complaints(locality);
CREATE INDEX IF NOT EXISTS idx_complaint_status ON complaints(status);
CREATE INDEX IF NOT EXISTS idx_complaint_reported ON complaints(reported_at);
CREATE INDEX IF NOT EXISTS idx_issue_status ON issues(status);
CREATE INDEX IF NOT EXISTS idx_issue_priority ON issues(priority_score DESC);
CREATE INDEX IF NOT EXISTS idx_candidate_review ON duplicate_candidates(review_status);
CREATE INDEX IF NOT EXISTS idx_link_issue ON issue_complaints(issue_id);
"""

def connect(path=None):
    if path is None:
        path = current_app.config.get("DATABASE", "data/civicresolve.db") if has_app_context() else "data/civicresolve.db"
    if path != ":memory:":
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    db = sqlite3.connect(path)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys=ON")
    return db

def get_db():
    if "db" not in g:
        g.db = connect()
    return g.db

def close_db(error=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()

def init_db(path=None):
    db = connect(path)
    db.executescript(SCHEMA)
    db.close()
