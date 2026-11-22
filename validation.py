import re

CATEGORIES = ("Pothole", "Streetlight", "Drainage", "Garbage", "Footpath", "Water Leakage", "Public Facility")
LOCALITIES = ("Kothrud", "Baner", "Hadapsar", "Shivajinagar", "Viman Nagar", "Deccan", "Aundh", "Warje", "Yerawada", "Bibwewadi")
STATUSES = ("Pending", "In Progress", "Resolved")

def validate_complaint(form):
    errors = []
    category, locality = form.get("category", ""), form.get("locality", "")
    description, landmark = form.get("description", "").strip(), form.get("location_description", "").strip()
    try: severity = int(form.get("severity", ""))
    except ValueError: severity = 0
    try: affected = int(form.get("affected_people", "0"))
    except ValueError: affected = -1
    if category not in CATEGORIES: errors.append("Choose a valid category.")
    if locality not in LOCALITIES: errors.append("Choose a listed Pune locality.")
    if not description or len(description) > 1000: errors.append("Description is required (up to 1000 characters).")
    if not landmark or len(landmark) > 160: errors.append("Location description is required (up to 160 characters).")
    if severity not in range(1, 6): errors.append("Severity must be 1 to 5.")
    if affected < 0: errors.append("Affected people must be a nonnegative whole number.")
    return errors, dict(category=category, locality=locality, description=description, location_description=landmark, severity=severity, affected_people=affected)

def valid_id(value, prefix):
    return bool(re.fullmatch(prefix + r"\d{6}", value or ""))
