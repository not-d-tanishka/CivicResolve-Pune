import os
import tempfile
import unittest
try:
    import flask  # noqa: F401
except ImportError:
    raise unittest.SkipTest("Install Flask from requirements.txt to run route and end-to-end tests")
from app import create_app
from app.database import connect

class AppTests(unittest.TestCase):
    def setUp(self):
        self.folder=tempfile.TemporaryDirectory()
        self.app=create_app({"TESTING":True,"DATABASE":os.path.join(self.folder.name,"app.db")})
        self.client=self.app.test_client()

    def tearDown(self): self.folder.cleanup()

    def test_dashboard_and_register(self):
        dashboard=self.client.get("/")
        self.assertEqual(dashboard.status_code,200)
        dashboard_text=dashboard.get_data(as_text=True)
        for removed_copy in ("Academic prototype","Pune Municipal Corporation service","Seeded reports are simulated","SIMULATED","DEMO","Student project","No report is sent"):
            self.assertNotIn(removed_copy,dashboard_text)
        dsa=self.client.get("/dsa")
        self.assertEqual(dsa.status_code,200)
        self.assertIn("Priority queue · max heap",dsa.get_data(as_text=True))
        script=self.client.get("/static/dsa.js")
        self.assertEqual(script.status_code,200)
        self.assertIn("mergeRange",script.get_data(as_text=True))
        script.close()
        response=self.client.post("/complaints/new",data={"category":"Pothole","locality":"Kothrud","location_description":"Karve Road","description":"A new pothole","severity":"4","affected_people":"12"},follow_redirects=True)
        self.assertEqual(response.status_code,200)
        with self.app.app_context():
            db=connect(self.app.config["DATABASE"])
            self.assertEqual(db.execute("SELECT COUNT(*) FROM complaints").fetchone()[0],1)
            db.close()

    def test_invalid_report_is_rejected(self):
        response=self.client.post("/complaints/new",data={"category":"Wrong","locality":"Kothrud","description":"","location_description":"road","severity":"8","affected_people":"-2"})
        self.assertEqual(response.status_code,200)
        with self.app.app_context():
            db=connect(self.app.config["DATABASE"])
            self.assertEqual(db.execute("SELECT COUNT(*) FROM complaints").fetchone()[0],0)
            db.close()

    def test_duplicate_review_group_status_and_analytics(self):
        for category,description in (("Pothole","Deep pothole near the crossing"),("Pothole","Large pothole at the crossing"),("Streetlight","Streetlight out at crossing")):
            self.client.post("/complaints/new",data={"category":category,"locality":"Kothrud","location_description":"Karve Road crossing","description":description,"severity":"4","affected_people":"18"})
        self.client.post("/duplicates",data={},follow_redirects=True)
        with self.app.app_context():
            db=connect(self.app.config["DATABASE"])
            self.assertEqual(db.execute("SELECT COUNT(*) FROM duplicate_candidates WHERE review_status='Pending'").fetchone()[0],1)
            candidate=db.execute("SELECT candidate_id FROM duplicate_candidates").fetchone()[0]
            db.close()
        self.client.post(f"/duplicates/{candidate}/confirm",follow_redirects=True)
        with self.app.app_context():
            db=connect(self.app.config["DATABASE"])
            self.assertEqual(db.execute("SELECT COUNT(*) FROM complaints").fetchone()[0],3)
            self.assertEqual(db.execute("SELECT COUNT(*) FROM issues").fetchone()[0],1)
            self.assertEqual(db.execute("SELECT COUNT(*) FROM issue_complaints").fetchone()[0],2)
            issue_id=db.execute("SELECT issue_id FROM issues").fetchone()[0]
            db.close()
        response=self.client.post(f"/issues/{issue_id}/status",data={"status":"In Progress"},follow_redirects=True)
        self.assertEqual(response.status_code,200)
        self.assertEqual(self.client.get("/analytics").status_code,200)
        with self.app.app_context():
            db=connect(self.app.config["DATABASE"])
            self.assertEqual(db.execute("SELECT status FROM issues WHERE issue_id=?",(issue_id,)).fetchone()[0],"In Progress")
            self.assertEqual(db.execute("SELECT COUNT(*) FROM status_history WHERE issue_id IS NOT NULL").fetchone()[0],1)
            db.close()
        restarted=create_app({"TESTING":True,"DATABASE":self.app.config["DATABASE"]})
        self.assertIn("In Progress",restarted.test_client().get(f"/issues/{issue_id}").get_data(as_text=True))

    def test_rejected_pair_preserves_reports_without_creating_issue(self):
        for description in ("Broken streetlight at the bus stop","Street light broken near bus stop"):
            self.client.post("/complaints/new",data={"category":"Streetlight","locality":"Baner","location_description":"Main bus stop","description":description,"severity":"2","affected_people":"5"})
        self.client.post("/duplicates",data={})
        with self.app.app_context():
            db=connect(self.app.config["DATABASE"])
            candidate=db.execute("SELECT candidate_id FROM duplicate_candidates WHERE review_status='Pending'").fetchone()[0]
            db.close()
        self.client.post(f"/duplicates/{candidate}/reject",follow_redirects=True)
        with self.app.app_context():
            db=connect(self.app.config["DATABASE"])
            self.assertEqual(db.execute("SELECT COUNT(*) FROM complaints").fetchone()[0],2)
            self.assertEqual(db.execute("SELECT COUNT(*) FROM issues").fetchone()[0],0)
            self.assertEqual(db.execute("SELECT review_status FROM duplicate_candidates").fetchone()[0],"Rejected")
            db.close()

if __name__=="__main__": unittest.main()
