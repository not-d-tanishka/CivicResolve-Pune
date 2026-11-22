from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
import logging
from .database import get_db
from .validation import validate_complaint, CATEGORIES, LOCALITIES, STATUSES, valid_id
from .services import generate_candidates, review_candidate, recalculate_priorities
from .cpp_engine import EngineError, run_engine

bp=Blueprint("main",__name__)

@bp.before_app_request
def ensure_schema():
    from .database import init_db
    init_db()

@bp.teardown_app_request
def close(error=None):
    from .database import close_db
    close_db(error)

@bp.route("/")
def index():
    db=get_db(); counts={"complaints":db.execute("SELECT COUNT(*) FROM complaints").fetchone()[0],"issues":db.execute("SELECT COUNT(*) FROM issues").fetchone()[0],"pending":db.execute("SELECT COUNT(*) FROM complaints WHERE status='Pending'").fetchone()[0],"candidates":db.execute("SELECT COUNT(*) FROM duplicate_candidates WHERE review_status='Pending'").fetchone()[0]}
    recent=db.execute("SELECT * FROM complaints ORDER BY reported_at DESC,id DESC LIMIT 8").fetchall()
    return render_template("index.html",counts=counts,top=db.execute("SELECT * FROM issues ORDER BY priority_score DESC,issue_id LIMIT 5").fetchall(),recent=recent)

@bp.route("/complaints")
def complaints():
    db=get_db(); q=request.args.get("q","").strip(); status=request.args.get("status","")
    sql="SELECT * FROM complaints WHERE 1=1"; params=[]
    if q: sql+=" AND (complaint_id LIKE ? OR description LIKE ? OR locality LIKE ?)"; params.extend([f"%{q}%"]*3)
    if status in STATUSES: sql+=" AND status=?"; params.append(status)
    return render_template("complaints.html",rows=db.execute(sql+" ORDER BY reported_at DESC",params).fetchall(),statuses=STATUSES)

@bp.route("/complaints/new",methods=["GET","POST"])
def new_complaint():
    if request.method=="POST":
        errors,data=validate_complaint(request.form)
        if errors:
            for error in errors: flash(error,"error")
        else:
            db=get_db(); n=db.execute("SELECT COALESCE(MAX(CAST(SUBSTR(complaint_id,3) AS INTEGER)),0)+1 FROM complaints WHERE complaint_id LIKE 'CR%' ").fetchone()[0]; key=f"CR{n:06d}"
            db.execute("INSERT INTO complaints(complaint_id,category,description,locality,location_description,severity,affected_people,reported_at,status,is_demo_data) VALUES(?,?,?,?,?,?,?,CURRENT_TIMESTAMP,'Pending',0)",(key,data["category"],data["description"],data["locality"],data["location_description"],data["severity"],data["affected_people"]))
            db.commit(); flash(f"Complaint {key} registered.","success"); return redirect(url_for("main.complaints"))
    return render_template("complaint_form.html",categories=CATEGORIES,localities=LOCALITIES)

@bp.route("/complaints/<complaint_id>")
def complaint_detail(complaint_id):
    if not valid_id(complaint_id,"CR"): abort(404)
    row=get_db().execute("SELECT * FROM complaints WHERE complaint_id=?",(complaint_id,)).fetchone()
    if row is None: abort(404)
    return render_template("complaint_detail.html",row=row,statuses=STATUSES)

@bp.route("/complaints/<complaint_id>/status",methods=["POST"])
def update_status(complaint_id):
    if not valid_id(complaint_id,"CR"): abort(404)
    status=request.form.get("status")
    if status not in STATUSES: flash("Invalid status.","error"); return redirect(url_for("main.complaint_detail",complaint_id=complaint_id))
    db=get_db(); c=db.execute("SELECT * FROM complaints WHERE complaint_id=?",(complaint_id,)).fetchone()
    if c is None: abort(404)
    db.execute("UPDATE complaints SET status=?,updated_at=CURRENT_TIMESTAMP WHERE id=?",(status,c["id"]))
    db.execute("INSERT INTO status_history(complaint_id,old_status,new_status,changed_by,note) VALUES(?,?,?,?,?)",(c["id"],c["status"],status,"local-admin","Demonstration status update")); db.commit()
    flash("Status updated.","success"); return redirect(url_for("main.complaint_detail",complaint_id=complaint_id))

@bp.route("/duplicates",methods=["GET","POST"])
def duplicates():
    db=get_db()
    if request.method=="POST":
        try: n=generate_candidates(); flash(f"Candidate scan complete: {n} possible pairs found.","success")
        except EngineError as error: flash(str(error),"error")
        return redirect(url_for("main.duplicates"))
    rows=db.execute("SELECT d.*,a.complaint_id a_id,a.description a_desc,a.location_description a_loc,b.complaint_id b_id,b.description b_desc,b.location_description b_loc FROM duplicate_candidates d JOIN complaints a ON a.id=d.complaint_id_a JOIN complaints b ON b.id=d.complaint_id_b WHERE d.review_status='Pending' ORDER BY d.overall_match_score DESC").fetchall()
    return render_template("duplicates.html",rows=rows)

@bp.route("/duplicates/<int:candidate_id>/<decision>",methods=["POST"])
def decide_duplicate(candidate_id,decision):
    if decision not in ("confirm","reject"): abort(404)
    try: review_candidate(candidate_id,decision=="confirm"); flash("Review saved.","success")
    except ValueError as error: flash(str(error),"error")
    except Exception:
        logging.exception("Duplicate review failed")
        flash("The review could not be saved. No partial changes were committed.","error")
    return redirect(url_for("main.duplicates"))

@bp.route("/issues")
def issues():
    try: rows=recalculate_priorities()
    except EngineError as error: flash(str(error),"error"); rows=[]
    return render_template("issues.html",rows=rows)

@bp.route("/issues/<issue_id>")
def issue_detail(issue_id):
    if not valid_id(issue_id,"IS"): abort(404)
    db=get_db(); issue=db.execute("SELECT * FROM issues WHERE issue_id=?",(issue_id,)).fetchone()
    if issue is None: abort(404)
    complaints=db.execute("SELECT c.* FROM complaints c JOIN issue_complaints ic ON ic.complaint_id=c.id WHERE ic.issue_id=?",(issue["id"],)).fetchall()
    return render_template("issue_detail.html",issue=issue,complaints=complaints)

@bp.route("/issues/<issue_id>/status",methods=["POST"])
def update_issue_status(issue_id):
    if not valid_id(issue_id,"IS"): abort(404)
    status=request.form.get("status")
    if status not in STATUSES: flash("Invalid status.","error"); return redirect(url_for("main.issue_detail",issue_id=issue_id))
    db=get_db(); issue=db.execute("SELECT * FROM issues WHERE issue_id=?",(issue_id,)).fetchone()
    if issue is None: abort(404)
    db.execute("UPDATE issues SET status=?,updated_at=CURRENT_TIMESTAMP WHERE id=?",(status,issue["id"]))
    db.execute("INSERT INTO status_history(issue_id,old_status,new_status,changed_by,note) VALUES(?,?,?,?,?)",(issue["id"],issue["status"],status,"local-admin","Demonstration issue status update")); db.commit()
    flash("Issue status updated.","success"); return redirect(url_for("main.issue_detail",issue_id=issue_id))

@bp.route("/analytics")
def analytics():
    db=get_db()
    return render_template("analytics.html",locality=db.execute("SELECT locality,COUNT(*) count FROM complaints GROUP BY locality ORDER BY count DESC").fetchall(),category=db.execute("SELECT category,COUNT(*) count FROM complaints GROUP BY category ORDER BY count DESC").fetchall(),statuses=db.execute("SELECT status,COUNT(*) count FROM complaints GROUP BY status").fetchall())

@bp.route("/benchmark",methods=["GET","POST"])
def benchmark():
    measurements=None
    if request.method=="POST":
        try: measurements=run_engine({"action":"benchmark"})["measurements"]
        except EngineError as error: flash(str(error),"error")
    return render_template("benchmark.html",measurements=measurements)

@bp.route("/dsa")
def dsa_lab():
    return render_template("dsa_lab.html")
