import os
import redis
import json
from fastapi import FastAPI, HTTPException, Body
from typing import List, Dict, Any
from pydantic import BaseModel

app = FastAPI(title="MAVDP DevSecOps API", version="2.0.0")

# Connection to the Brain instance (via Redis)
redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
r = redis.from_url(redis_url, decode_responses=True)

class TaskRequest(BaseModel):
    target: str
    engine_type: str

@app.get("/")
def read_root():
    return {"status": "MAVDP Brain API Online"}

@app.post("/tasks/submit")
def submit_task(request: TaskRequest):
    """
    Triggers an autonomous audit for a specific target.
    Used by CI/CD pipelines to start scans on commit.
    """
    task_id = f"task_{os.getpid()}_{request.engine_type}"
    task_data = {
        "task_id": task_id,
        "target": request.target,
        "engine_type": request.engine_type,
        "status": "pending"
    }
    r.lpush(f"mavdp:queue:{request.engine_type}", json.dumps(task_data))
    return {"message": "Task submitted", "task_id": task_id}

@app.get("/findings")
def get_findings(limit: int = 100) -> List[Dict[str, Any]]:
    """
    Retrieves the latest vulnerability findings.
    """
    findings_raw = r.lrange("mavdp:findings", 0, limit - 1)
    return [json.loads(f) for f in findings_raw]

@app.get("/stats")
def get_stats():
    """
    System-wide statistics for the dashboard.
    """
    return {
        "total_findings": r.llen("mavdp:findings"),
        "active_engines": r.hlen("mavdp:engines"),
        "crash_counts": r.hgetall("mavdp:crash_counts")
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
