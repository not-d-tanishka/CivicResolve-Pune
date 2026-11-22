import argparse
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import connect, init_db

p=argparse.ArgumentParser(description="Remove simulated records only")
p.add_argument("--yes",action="store_true",help="confirm deletion of records marked as demo data")
args=p.parse_args()
if not args.yes: raise SystemExit("No changes made. Re-run with --yes to remove demo complaints and their candidates.")
init_db(); db=connect(); db.execute("BEGIN IMMEDIATE")
ids=[r[0] for r in db.execute("SELECT id FROM complaints WHERE is_demo_data=1")]
demo_ids=set(ids)
issue_ids=[r[0] for r in db.execute("SELECT DISTINCT issue_id FROM issue_complaints WHERE complaint_id IN (SELECT id FROM complaints WHERE is_demo_data=1)")]
for issue_id in issue_ids:
    members=[r[0] for r in db.execute("SELECT complaint_id FROM issue_complaints WHERE issue_id=?",(issue_id,))]
    demo_members=[cid for cid in members if cid in demo_ids]
    if len(demo_members)==len(members):
        db.execute("DELETE FROM status_history WHERE issue_id=?",(issue_id,))
        db.execute("DELETE FROM issues WHERE id=?",(issue_id,))
    else:
        db.executemany("DELETE FROM issue_complaints WHERE issue_id=? AND complaint_id=?",[(issue_id,cid) for cid in demo_members])
        remaining=db.execute("SELECT c.severity,c.affected_people FROM complaints c JOIN issue_complaints ic ON ic.complaint_id=c.id WHERE ic.issue_id=?",(issue_id,)).fetchall()
        db.execute("UPDATE issues SET severity=?,affected_people=?,updated_at=CURRENT_TIMESTAMP WHERE id=?",(max(r[0] for r in remaining),max(r[1] for r in remaining),issue_id))
for cid in ids:
    db.execute("DELETE FROM duplicate_candidates WHERE complaint_id_a=? OR complaint_id_b=?",(cid,cid))
    db.execute("DELETE FROM status_history WHERE complaint_id=?",(cid,))
db.executemany("DELETE FROM complaints WHERE id=?",[(i,) for i in ids]); db.commit(); db.close()
print(f"Removed {len(ids)} simulated complaints. Real/user complaints were preserved.")
