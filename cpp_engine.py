import os
import subprocess

ENGINE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "cpp", "build", "civic_engine"))

class EngineError(RuntimeError):
    pass

def run_engine(payload):
    if not os.path.isfile(ENGINE):
        raise EngineError("C++ engine is missing. Build it with: make -C cpp")
    try:
        action = payload["action"]
        if action == "score":
            body = f"score\n{payload['severity']} {payload['affected']} {payload['age_days']}\n"
        elif action == "duplicates":
            lines = ["duplicates"]
            for c in payload["complaints"]:
                values = [c[k] for k in ("complaint_id", "category", "locality", "location_description", "description")]
                lines.append("\t".join(str(v).replace("\t", " ").replace("\n", " ") for v in values))
            body = "\n".join(lines) + "\n"
        elif action == "rank":
            body = "rank\n" + "".join(f"{row['issue_id']} {row['priority_score']}\n" for row in payload["issues"])
        elif action == "benchmark":
            body = "benchmark\n"
        else:
            raise EngineError("Unsupported C++ action")
        timeout = 60 if action == "benchmark" else 10
        result = subprocess.run([ENGINE], input=body, text=True, capture_output=True, timeout=timeout, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise EngineError(f"Could not run the C++ engine: {exc}") from exc
    if result.returncode != 0:
        raise EngineError(result.stderr.strip() or "C++ engine returned an error")
    if payload["action"] == "score":
        try: score=float(result.stdout.strip())
        except ValueError as exc: raise EngineError("C++ engine returned malformed score") from exc
        if not 0 <= score <= 10: raise EngineError("C++ engine returned a score outside 0 to 10")
        return {"score":score}
    if payload["action"] == "rank":
        ranked=[]
        for line in result.stdout.splitlines():
            fields=line.split("\t")
            if len(fields)!=2: raise EngineError("C++ engine returned malformed ranked row")
            try: score=float(fields[1])
            except ValueError as exc: raise EngineError("C++ engine returned a nonnumeric rank") from exc
            if not 0 <= score <= 10: raise EngineError("C++ engine returned a priority outside 0 to 10")
            ranked.append({"issue_id":fields[0],"score":score})
        return {"ranked":ranked}
    if payload["action"] == "benchmark":
        lines=result.stdout.splitlines()
        if not lines or lines[0].split("\t") != ["size","linear_ns","hash_ns","merge_sort_ns","heap_ns","duplicate_scan_ns"]:
            raise EngineError("C++ engine returned malformed benchmark header")
        measurements=[]
        try:
            for line in lines[1:]:
                values=line.split("\t")
                if len(values)!=6: raise ValueError("wrong number of benchmark columns")
                row=dict(zip(("size","linear_ns","hash_ns","merge_sort_ns","heap_ns","duplicate_scan_ns"),map(int,values)))
                if row["size"] not in (100,500,1000,5000) or any(value<0 for value in row.values()): raise ValueError("invalid benchmark value")
                measurements.append(row)
        except ValueError as exc:
            raise EngineError("C++ engine returned invalid benchmark measurements") from exc
        if [row["size"] for row in measurements] != [100,500,1000,5000]:
            raise EngineError("C++ engine returned incomplete benchmark sizes")
        return {"measurements":measurements}
    lines=result.stdout.splitlines()
    if not lines or lines[0].split("\t") != ["a","b","description_similarity","location_similarity","overall_score"]:
        raise EngineError("C++ engine returned malformed candidate header")
    candidates = []
    for line in lines[1:]:
        fields = line.split("\t")
        if len(fields) != 5: raise EngineError("C++ engine returned malformed candidate row")
        try:
            similarity, location, score = float(fields[2]), float(fields[3]), float(fields[4])
        except ValueError as exc:
            raise EngineError("C++ engine returned a nonnumeric candidate score") from exc
        if not all(0 <= value <= 1 for value in (similarity,location,score)):
            raise EngineError("C++ engine returned a score outside 0 to 1")
        candidates.append({"a": fields[0], "b": fields[1], "similarity": similarity, "score": score, "category_match": 1, "location_match": int(location>=0.5)})
    return {"candidates": candidates}
