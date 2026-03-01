import json
import random
import time
import requests
import redis
import datetime
import hashlib

class APIEngine:
    """
    Stateful Protocol Fuzzer for APIs.
    Supports Swagger/OpenAPI ingestion and sequence mutation.
    """
    def __init__(self, redis_url=None):
        self.redis_url = redis_url or "redis://localhost:6379/0"
        self.r = redis.from_url(self.redis_url, decode_responses=True)
        self.engine_type = "api"
        self.session = requests.Session()
        
    def load_schema(self, schema_json):
        """
        Parses OpenAPI/Swagger to identify endpoints and parameters.
        """
        schema = json.loads(schema_json)
        endpoints = []
        for path, methods in schema.get('paths', {}).items():
            for method, details in methods.items():
                endpoints.append({
                    "path": path,
                    "method": method.upper(),
                    "params": details.get('parameters', []),
                    "responses": details.get('responses', {})
                })
        return endpoints

    def mutate_params(self, params):
        """
        Mutation logic for different parameter types.
        """
        mutated = {}
        for p in params:
            name = p.get('name')
            ptype = p.get('schema', {}).get('type', 'string')
            
            if ptype == 'integer':
                mutated[name] = random.choice([0, -1, 2**31-1, 99999, "A" * 10])
            else:
                mutated[name] = random.choice(["' OR 1=1 --", "../../../etc/passwd", "A" * 1000, "", "\x00"])
        return mutated

    def run_sequence(self, endpoints, sequence_length=3):
        """
        Executes a random sequence of API calls to detect state anomalies.
        Example: Create -> Delete -> Modify (Checking for 404 or logic errors)
        """
        sequence = random.choices(endpoints, k=sequence_length)
        history = []
        
        for step in sequence:
            # In a real tool, we would use the 'base_url' of the target
            # For demonstration, we simulate the requests
            try:
                # Simulating request and response
                resp_code = random.choice([200, 201, 400, 401, 403, 404, 500])
                history.append({
                    "path": step['path'],
                    "method": step['method'],
                    "status": resp_code
                })
                
                # Logic Anomaly Detection: 
                # If we DELETE and then SUCCESSFUL MODIFY, that's a logic bug (Broken Object Level Authorization)
                if len(history) >= 2:
                    last = history[-2]
                    curr = history[-1]
                    if last['method'] == 'DELETE' and last['status'] == 200 and curr['method'] == 'PATCH' and curr['status'] == 200:
                        return "LOGIC_BUG", history
                        
                if resp_code == 500:
                    return "SERVER_ERROR", history
                    
            except Exception as e:
                return "FAIL", str(e)
                
        return "OK", history

    def start(self):
        print("[*] API Stateful Engine operational.")
        while True:
            task_raw = self.r.brpop("mavdp:queue:api", timeout=5)
            if task_raw:
                task = json.loads(task_raw[1])
                target = task['target']
                # mock schema
                mock_schema = '{"paths": {"/user": {"post": {}, "get": {}, "delete": {}, "patch": {}}}}'
                endpoints = self.load_schema(mock_schema)
                
                print(f"[+] Starting API session for {target}")
                for _ in range(50):
                    status, history = self.run_sequence(endpoints)
                    if status in ["LOGIC_BUG", "SERVER_ERROR"]:
                        severity = "HIGH" if status == "LOGIC_BUG" else "MEDIUM"
                        telemetry = {
                            "target_id": target,
                            "engine_type": self.engine_type,
                            "timestamp": datetime.datetime.now().isoformat(),
                            "severity_estimate": severity,
                            "crash_hash": hashlib.sha256(str(history).encode()).hexdigest()[:16],
                            "metadata": {"type": status, "trace": history}
                        }
                        self.r.publish("mavdp:telemetry", json.dumps(telemetry))
                        print(f"[!] Finding: {status} in sequence")

if __name__ == "__main__":
    engine = APIEngine()
    engine.start()
