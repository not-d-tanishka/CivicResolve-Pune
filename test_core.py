import importlib.util
import os
import unittest

VALIDATION_PATH=os.path.join(os.path.dirname(__file__),"..","app","validation.py")
spec=importlib.util.spec_from_file_location("civic_validation",VALIDATION_PATH)
validation=importlib.util.module_from_spec(spec); spec.loader.exec_module(validation)

class CoreTests(unittest.TestCase):
    def test_validate_ranges(self):
        errors,_=validation.validate_complaint({"category":"Pothole","locality":"Kothrud","description":"issue","location_description":"road","severity":"6","affected_people":"-1"})
        self.assertGreaterEqual(len(errors),2)

if __name__=="__main__": unittest.main()
