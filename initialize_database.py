import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import init_db, connect
from app.validation import LOCALITIES

init_db()
db=connect()
for name in LOCALITIES:
    db.execute("INSERT OR IGNORE INTO locations(locality_name,description,is_demo_location) VALUES(?,?,1)",(name,"Demonstration locality label; no verified coordinates."))
db.commit(); db.close()
print("Database schema and Pune locality references are ready.")
