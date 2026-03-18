import os
import time
import json
import logging
import redis
from typing import Dict, Any

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("Brain")

class Orchestrator:
    """
    The Brain of MAVDP. Coordinates targets, engines, and results.
    """
    def __init__(self):
        self.redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        try:
            self.r = redis.from_url(self.redis_url, decode_responses=True)
            logger.info(f"Connected to Redis at {self.redis_url}")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self.r = None

        self.engines = {}
        logger.info("MAVDP Orchestration Layer Initialized.")

    def register_engine(self, engine_id: str, engine_type: str):
        self.engines[engine_id] = {"type": engine_type, "status": "idle"}
        # Store engine info in Redis for persistence/discovery
        if self.r:
            self.r.hset("mavdp:engines", engine_id, json.dumps(self.engines[engine_id]))
        logger.info(f"Registered engine: {engine_id} ({engine_type})")

    def schedule_task(self, target: str, engine_type: str):
        task_id = f"task_{int(time.time())}"
        task_data = {
            "task_id": task_id,
            "target": target,
            "engine_type": engine_type,
            "status": "pending",
            "created_at": time.time()
        }
        
        if self.r:
            # Push task to the specific engine queue
            self.r.lpush(f"mavdp:queue:{engine_type}", json.dumps(task_data))
            self.r.hset("mavdp:tasks", task_id, json.dumps(task_data))
        
        logger.info(f"Scheduled task {task_id} for target {target} using {engine_type} engine.")
        return task_id

    def listen_telemetry(self):
        """
        Listens for telemetry from engines on the redis pubsub.
        """
        if not self.r:
            return

        pubsub = self.r.pubsub()
        pubsub.subscribe("mavdp:telemetry")
        logger.info("Listening for engine telemetry...")
        
        for message in pubsub.listen():
            if message['type'] == 'message':
                self.process_telemetry(message['data'])

    def deduplicate_crash(self, crash_hash: str):
        """
        Clusters similar findings to avoid redundancy.
        """
        if not self.r: return False
        
        count = self.r.hincrby("mavdp:crash_counts", crash_hash, 1)
        if count > 1:
            logger.info(f"Duplicate crash detected: {crash_hash} (Count: {count})")
            return True # Is duplicate
        return False

    def score_finding(self, telemetry: Dict[str, Any]):
        """
        Cross-domain scoring model (The Risk Engine).
        Weights factors like memory corruption vs auth bypass.
        """
        base_score = 0.0
        engine_type = telemetry.get('engine_type')
        severity = telemetry.get('severity_estimate', 'INFO')
        
        # Base weight by severity
        severity_map = {"INFO": 0, "LOW": 2, "MEDIUM": 5, "HIGH": 8, "CRITICAL": 10}
        base_score += severity_map.get(severity, 0)
        
        # Domain-specific weight
        domain_weights = {
            "kernel": 1.5,     # Kernel crashes are high impact
            "api": 1.2,        # API logic bugs often lead to data leaks
            "web": 1.0,
            "native_binary": 1.1,
            "iot": 1.3
        }
        
        final_score = base_score * domain_weights.get(engine_type, 1.0)
        return min(10.0, final_score)

    def adaptive_reallocation(self, engine_type: str, coverage_delta: float):
        """
        Adaptive Learning Layer: Reallocates resources based on yield.
        If an engine is finding a lot of new coverage, increase its priority.
        """
        if coverage_delta > 0:
            current_pri = float(self.r.hget("mavdp:engine_priority", engine_type) or 1.0)
            new_pri = current_pri + 0.1
            self.r.hset("mavdp:engine_priority", engine_type, new_pri)
            logger.info(f"Adaptive Reallocation: Increased priority for {engine_type} to {new_pri:.2f}")

    def process_telemetry(self, raw_data: str):
        try:
            data = json.loads(raw_data)
            engine_type = data.get('engine_type')
            target_id = data.get('target_id')
            crash_hash = data.get('crash_hash')
            coverage_delta = data.get('coverage_delta', 0)
            severity = data.get('severity_estimate', 'INFO')

            # 1. Deduplication
            if crash_hash and self.deduplicate_crash(f"{engine_type}:{crash_hash}"):
                return

            # 2. Risk Scoring
            risk_score = self.score_finding(data)
            data['final_risk_score'] = risk_score
            
            # 3. Autonomous Self-Healing (Batch 12)
            if severity in ["HIGH", "CRITICAL"] and "source_code" in data.get('metadata', {}):
                from fixer import FixerAgent
                fixer = FixerAgent()
                patch = fixer.analyze_and_patch(data['metadata']['source_code'], data)
                if patch:
                    logger.info(f"[+] Autonomous Patch Proposed for {target_id}")
                    data['metadata']['patch_proposal'] = patch
                    fixer.verify_patch(target_id, patch)

            # 4. Cross-Domain Pivot Analysis (Batch 15)
            from pivot import PivotCorrelationEngine
            pivot = PivotCorrelationEngine(self)
            pivot.analyze_finding_for_pivot(data)

            # 5. Zero-Knowledge OPSEC (Batch 17)
            from opsec import ZeroKnowledgeOPSEC
            opsec = ZeroKnowledgeOPSEC()
            secured_finding = opsec.encrypt_finding(data)

            # 6. Adaptive Learning
            self.adaptive_reallocation(engine_type, coverage_delta)

            logger.info(f"PROCESSED finding: {engine_type} | Target: {target_id} | RISK: {risk_score}/10 | SECURED: True")
            
            # Persist the processed and encrypted finding
            if self.r:
                self.r.lpush("mavdp:findings", secured_finding)
                
        except Exception as e:
            logger.error(f"Failed to process telemetry: {e}")

if __name__ == "__main__":
    brain = Orchestrator()
    
    # 1. Register and Task Native Binary Engine
    brain.register_engine("native_bin_01", "native_binary")
    brain.schedule_task("vulnerable_target.py", "native_binary")
    
    # 2. Register and Task API Engine
    brain.register_engine("api_fuzzer_01", "api")
    brain.schedule_task("https://api.mavdp.internal/v2", "api")
    
    # 3. Register and Task Blockchain Engine
    brain.register_engine("chain_audit_01", "blockchain")
    brain.schedule_task("0x71C7656EC7ab88b098defB751B7401B5f6d8976F", "blockchain")
    
    # 4. Listen for system-wide telemetry
    brain.listen_telemetry()

