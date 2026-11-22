from datetime import datetime, timezone
from .database import get_db
from .cpp_engine import run_engine

def recalculate_priorities(db=None):
    db=db or get_db()
    rows=db.execute("SELECT * FROM issues").fetchall()
    for row in rows:
        created=datetime.fromisoformat(row["created_at"].replace(" ","T")).replace(tzinfo=timezone.utc)
        age=max(0,(datetime.now(timezone.utc)-created).days)
        score=run_engine({"action":"score","severity":row["severity"],"affected":row["affected_people"],"age_days":age})["score"]
        db.execute("UPDATE issues SET priority_score=?,updated_at=CURRENT_TIMESTAMP WHERE id=?",(score,row["id"]))
    rows=db.execute("SELECT * FROM issues").fetchall()
    ranked=run_engine({"action":"rank","issues":[dict(r) for r in rows]})["ranked"]
    by_id={r["issue_id"]:r for r in rows}
    return [by_id[r["issue_id"]] for r in ranked]

def generate_candidates():
    db=get_db(); rows=[dict(r) for r in db.execute("SELECT * FROM complaints ORDER BY id")]
    ids={r["complaint_id"]:r["id"] for r in rows}
    result=run_engine({"action":"duplicates","complaints":rows})
    for p in result["candidates"]:
        a,b=sorted((ids[p["a"]],ids[p["b"]]))
        db.execute("INSERT OR IGNORE INTO duplicate_candidates(complaint_id_a,complaint_id_b,category_match,location_match,similarity_score,overall_match_score) VALUES(?,?,?,?,?,?)",(a,b,p["category_match"],p["location_match"],p["similarity"],p["score"]))
    db.commit(); return len(result["candidates"])

def review_candidate(candidate_id, confirm):
    db=get_db()
    try:
        db.execute("BEGIN IMMEDIATE")
        c=db.execute("SELECT * FROM duplicate_candidates WHERE candidate_id=?",(candidate_id,)).fetchone()
        if c is None: raise ValueError("Duplicate candidate not found.")
        if c["review_status"]!="Pending": raise ValueError("This candidate has already been reviewed.")
        if not confirm:
            db.execute("UPDATE duplicate_candidates SET review_status='Rejected',reviewed_at=CURRENT_TIMESTAMP,review_reason='Rejected during manual review' WHERE candidate_id=?",(candidate_id,)); db.commit(); return
        a=db.execute("SELECT * FROM complaints WHERE id=?",(c["complaint_id_a"],)).fetchone()
        b=db.execute("SELECT * FROM complaints WHERE id=?",(c["complaint_id_b"],)).fetchone()
        if a["category"]!=b["category"] or a["locality"].casefold()!=b["locality"].casefold(): raise ValueError("Reports do not meet matching category and locality rules.")
        links=db.execute("SELECT issue_id FROM issue_complaints WHERE complaint_id IN (?,?)",(a["id"],b["id"])).fetchall()
        issue_ids={r["issue_id"] for r in links}
        if len(issue_ids)>1: raise ValueError("Reports belong to conflicting issues; review a safe group merge manually.")
        if issue_ids: issue_id=next(iter(issue_ids))
        else:
            next_id=db.execute("SELECT COALESCE(MAX(CAST(SUBSTR(issue_id,3) AS INTEGER)),0)+1 FROM issues WHERE issue_id LIKE 'IS%'").fetchone()[0]
            issue_id=db.execute("INSERT INTO issues(issue_id,category,locality,location_description,summary,severity,affected_people,priority_score,status) VALUES(?,?,?,?,?,?,?,0,'Pending')",(f"IS{next_id:06d}",a["category"],a["locality"],a["location_description"],a["description"],max(a["severity"],b["severity"]),max(a["affected_people"],b["affected_people"]))).lastrowid
        for item in (a,b):
            db.execute("INSERT OR IGNORE INTO issue_complaints(issue_id,complaint_id,linked_by,link_reason) VALUES(?,?,?,?)",(issue_id,item["id"],"local-admin","Manually confirmed duplicate candidate"))
        group=db.execute("SELECT c.* FROM complaints c JOIN issue_complaints ic ON ic.complaint_id=c.id WHERE ic.issue_id=?",(issue_id,)).fetchall()
        db.execute("UPDATE issues SET severity=?,affected_people=?,updated_at=CURRENT_TIMESTAMP WHERE id=?",(max(r["severity"] for r in group),max(r["affected_people"] for r in group),issue_id))
        db.execute("UPDATE duplicate_candidates SET review_status='Confirmed',reviewed_at=CURRENT_TIMESTAMP,review_reason='Confirmed during manual review' WHERE candidate_id=?",(candidate_id,))
        recalculate_priorities(db); db.commit()
    except Exception:
        db.rollback(); raise
