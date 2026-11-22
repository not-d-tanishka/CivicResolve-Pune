"""Direct C++ subprocess contract tests; intentionally needs no Flask import."""
import importlib.util
import os
import unittest

MODULE_PATH=os.path.join(os.path.dirname(__file__),"..","app","cpp_engine.py")
spec=importlib.util.spec_from_file_location("civic_cpp_engine",MODULE_PATH)
engine=importlib.util.module_from_spec(spec); spec.loader.exec_module(engine)

class EngineContractTests(unittest.TestCase):
    def test_score_and_rejects_bad_input(self):
        self.assertAlmostEqual(engine.run_engine({"action":"score","severity":5,"affected":30,"age_days":14})["score"],6.3)
        self.assertEqual(engine.run_engine({"action":"score","severity":1,"affected":0,"age_days":0})["score"],0)
        with self.assertRaises(engine.EngineError): engine.run_engine({"action":"score","severity":8,"affected":0,"age_days":0})

    def test_candidate_filter_and_text_similarity(self):
        records=[
            {"complaint_id":"CR000001","category":"Pothole","locality":"Kothrud","location_description":"Karve Road","description":"large pothole near junction"},
            {"complaint_id":"CR000002","category":"Pothole","locality":"Kothrud","location_description":"Karve Road","description":"pothole by junction"},
            {"complaint_id":"CR000003","category":"Streetlight","locality":"Kothrud","location_description":"Karve Road","description":"streetlight broken"},
            {"complaint_id":"CR000004","category":"Pothole","locality":"Kothrud","location_description":"Senapati Bapat Road","description":"large pothole near junction"},
        ]
        pairs=engine.run_engine({"action":"duplicates","complaints":records})["candidates"]
        lookup={(p["a"],p["b"]):p for p in pairs}
        self.assertIn(("CR000001","CR000002"),lookup)
        self.assertEqual(lookup[("CR000001","CR000002")]["location_match"],1)
        self.assertIn(("CR000001","CR000004"),lookup)
        self.assertEqual(lookup[("CR000001","CR000004")]["location_match"],0)
        self.assertNotIn(("CR000001","CR000003"),lookup)

    def test_heap_rank_tie_break(self):
        ranked=engine.run_engine({"action":"rank","issues":[{"issue_id":"IS000002","priority_score":8},{"issue_id":"IS000001","priority_score":8}]})["ranked"]
        self.assertEqual([r["issue_id"] for r in ranked],["IS000001","IS000002"])

    def test_benchmark_has_all_sizes_and_nonnegative_times(self):
        rows=engine.run_engine({"action":"benchmark"})["measurements"]
        self.assertEqual([r["size"] for r in rows],[100,500,1000,5000])
        self.assertTrue(all(v>=0 for row in rows for v in row.values()))

if __name__=="__main__": unittest.main(verbosity=2)
