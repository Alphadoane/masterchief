import redis
import json
import time
import random
import datetime

REDIS_URL = "redis://localhost:6379/0"

def mock_engine():
    r = redis.from_url(REDIS_URL, decode_responses=True)
    engine_id = "mock_worker_01"
    engine_type = "native_binary"
    
    print(f"[*] Mock Engine {engine_id} started. Waiting for tasks...")
    
    while True:
        # 1. Listen for tasks
        task_raw = r.brpop(f"mavdp:queue:{engine_type}", timeout=5)
        if task_raw:
            task = json.loads(task_raw[1])
            print(f"[+] Received task: {task['task_id']} for target: {task['target']}")
            
            # 2. Simulate work
            time.sleep(2)
            
            # 3. Send telemetry
            telemetry = {
                "target_id": task['target'],
                "engine_type": engine_type,
                "timestamp": datetime.datetime.now().isoformat(),
                "coverage_delta": random.randint(1, 100),
                "severity_estimate": random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"]),
                "crash_hash": f"stack_hash_{random.getrandbits(32):x}",
                "metadata": {"reason": "Heap overflow detected in mock"}
            }
            
            r.publish("mavdp:telemetry", json.dumps(telemetry))
            print(f"[^] Telemetry sent for {task['task_id']}")
        else:
            # Send a heartbeat or just wait
            pass

if __name__ == "__main__":
    try:
        mock_engine()
    except KeyboardInterrupt:
        print("Stopping mock engine.")
    except Exception as e:
        print(f"Error: {e}")
