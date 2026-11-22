"""SQLite schema checks that run even when Flask is not installed."""
import ast
import os
import sqlite3
import tempfile
import unittest

ROOT=os.path.dirname(os.path.dirname(__file__))
tree=ast.parse(open(os.path.join(ROOT,"app","database.py"),encoding="utf-8").read())
SCHEMA=next(ast.literal_eval(node.value) for node in tree.body if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=="SCHEMA" for t in node.targets))

class DatabaseSchemaTests(unittest.TestCase):
    def setUp(self):
        self.folder=tempfile.TemporaryDirectory()
        self.db=sqlite3.connect(os.path.join(self.folder.name,"test.db"))
        self.db.execute("PRAGMA foreign_keys=ON"); self.db.executescript(SCHEMA)

    def tearDown(self):
        self.db.close(); self.folder.cleanup()

    def complaint(self,key="CR000001",severity=3,affected=2):
        return (key,"Pothole","road issue","Kothrud","Karve Road",severity,affected,"2026-11-18T10:00:00","Pending")

    def add_complaint(self,row):
        self.db.execute("INSERT INTO complaints(complaint_id,category,description,locality,location_description,severity,affected_people,reported_at,status) VALUES(?,?,?,?,?,?,?,?,?)",row)

    def test_field_constraints_unique_ids_and_foreign_keys(self):
        self.add_complaint(self.complaint())
        with self.assertRaises(sqlite3.IntegrityError): self.add_complaint(self.complaint("CR000002",6,2))
        with self.assertRaises(sqlite3.IntegrityError): self.add_complaint(self.complaint("CR000003",3,-1))
        with self.assertRaises(sqlite3.IntegrityError): self.add_complaint(self.complaint())
        with self.assertRaises(sqlite3.IntegrityError): self.db.execute("INSERT INTO issue_complaints(issue_id,complaint_id,linked_by,link_reason) VALUES(1,1,'test','missing parent')")

    def test_candidate_pair_order_and_group_unique_membership(self):
        self.add_complaint(self.complaint()); self.add_complaint(self.complaint("CR000002"))
        self.db.execute("INSERT INTO duplicate_candidates(complaint_id_a,complaint_id_b,category_match,location_match,similarity_score,overall_match_score) VALUES(1,2,1,1,.8,.9)")
        with self.assertRaises(sqlite3.IntegrityError): self.db.execute("INSERT INTO duplicate_candidates(complaint_id_a,complaint_id_b,category_match,location_match,similarity_score,overall_match_score) VALUES(2,1,1,1,.8,.9)")
        self.db.execute("INSERT INTO issues(issue_id,category,locality,location_description,summary,severity,affected_people,priority_score,status) VALUES('IS000001','Pothole','Kothrud','Karve Road','Road issue',3,2,4,'Pending')")
        self.db.execute("INSERT INTO issue_complaints(issue_id,complaint_id,linked_by,link_reason) VALUES(1,1,'test','confirmed')")
        with self.assertRaises(sqlite3.IntegrityError): self.db.execute("INSERT INTO issue_complaints(issue_id,complaint_id,linked_by,link_reason) VALUES(1,1,'test','repeat')")

    def test_transaction_rolls_back_all_changes(self):
        self.db.execute("BEGIN")
        self.add_complaint(self.complaint())
        self.db.rollback()
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM complaints").fetchone()[0],0)

if __name__=="__main__": unittest.main(verbosity=2)
