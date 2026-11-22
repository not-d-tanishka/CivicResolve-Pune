import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import init_db, connect
from app.validation import LOCALITIES, CATEGORIES
from datetime import datetime, timedelta
import random

init_db(); db=connect(); rng=random.Random(20261030)
examples=[("Pothole","Deep pothole near the junction", "Karve Road junction"),("Pothole","Large pothole causing trouble on road", "Karve Road junction"),("Streetlight","Streetlight not working at night", "Karve Road junction"),("Drainage","Drain blocked after rainfall", "Market lane"),("Garbage","Overflowing waste bin", "Bus stop"),("Footpath","Broken footpath slabs", "Main road"),("Water Leakage","Water leaking from roadside pipe", "Crossing")]
if db.execute("SELECT COUNT(*) FROM complaints WHERE is_demo_data=1").fetchone()[0]==0:
    start_id=db.execute("SELECT COALESCE(MAX(CAST(SUBSTR(complaint_id,3) AS INTEGER)),0)+1 FROM complaints WHERE complaint_id LIKE 'CR%'").fetchone()[0]
    for i in range(50):
        category,description,place=examples[i%len(examples)]
        locality=LOCALITIES[(i*3)%len(LOCALITIES)]
        # Inject obvious repeat reports in the same place for a few review examples.
        if i in (1,): locality=LOCALITIES[0]
        if i==0: locality=LOCALITIES[0]
        if i==2: locality=LOCALITIES[0]
        if i>=7:
            category=CATEGORIES[(i*5)%len(CATEGORIES)]; description=f"{category} maintenance concern near {place.lower()} #{i}"
        when=datetime.now()-timedelta(days=(i*7)%100,hours=i%24)
        db.execute("INSERT INTO complaints(complaint_id,category,description,locality,location_description,severity,affected_people,reported_at,status,is_demo_data) VALUES(?,?,?,?,?,?,?,?,?,1)",(f"CR{start_id+i:06d}",category,description,locality,place,rng.randint(1,5),rng.randint(0,120),when.isoformat(timespec="seconds"),("Pending","In Progress","Resolved")[i%3]))
    db.commit(); print("Inserted 50 fictional demonstration complaints.")
else:
    print("Demo complaints already exist; no rows inserted.")
db.close()
