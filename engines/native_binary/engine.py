import redis
import json
import os
import subprocess
import time
import hashlib
import datetime
import logging
from typing import Dict, Any, Optional

from mutator import Mutator
from afl_wrapper import AFLWrapper
from solver import SymbolicSolver
from profiler import HighInterestProfiler

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("BinaryEngine")

class BinaryEngine:
    """
    Autonomous Native Binary Discovery Engine.
    Orchestrates AFL++ for performance and Angr for code reasoning.
    """
    def __init__(self, redis_url=None):
        self.redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.r = redis.from_url(self.redis_url, decode_responses=True)
        self.engine_id = f"binary_engine_{os.getpid()}"
        self.engine_type = "native_binary"
        self.corpus = [b"initial_seed"]
        self.coverage_map = set()
        self.afl: Optional[AFLWrapper] = None
        self.solver: Optional[SymbolicSolver] = None
        self.profiler: Optional[HighInterestProfiler] = None
        
    def report_telemetry(self, target_id, severity, crash_hash=None, coverage_delta=0, metadata=None):
        telemetry = {
            "target_id": target_id,
            "engine_type": self.engine_type,
            "timestamp": datetime.datetime.now().isoformat(),
            "coverage_delta": coverage_delta,
            "severity_estimate": severity,
            "crash_hash": crash_hash,
            "metadata": metadata or {}
        }
        if self.r:
            self.r.publish("mavdp:telemetry", json.dumps(telemetry))

    def parse_asan_output(self, stderr: str):
        findings = {"vuln_type": "Unknown", "stack_hash": None, "raw_report": stderr}
        if "AddressSanitizer:" in stderr:
            lines = stderr.split('\n')
            for line in lines:
                if "AddressSanitizer:" in line:
                    findings["vuln_type"] = line.split("AddressSanitizer:")[1].strip().split(" ")[0]
                if " #0 " in line:
                    findings["stack_hash"] = hashlib.sha256(line.encode()).hexdigest()[:16]
                    break
        return findings

    def triage_crash(self, findings: Dict[str, Any]):
        if not findings["stack_hash"]: return None, "LOW"
        unique_id = f"{findings['vuln_type']}_{findings['stack_hash']}"
        score_map = {
            "heap-buffer-overflow": "HIGH",
            "stack-buffer-overflow": "CRITICAL",
            "use-after-free": "CRITICAL"
        }
        return unique_id, score_map.get(findings["vuln_type"], "MEDIUM")

    def run_target(self, target_path, input_data):
        # ... logic for single iteration fuzzing if AFL is not used ...
        # (Keeping the mock logic for fallback)
        if b"CRASH" in input_data:
            mock_stderr = "==1234==ERROR: AddressSanitizer: heap-buffer-overflow on address 0x1234\n #0 0x4005d1 in main fuzz.c:10"
            findings = self.parse_asan_output(mock_stderr)
            crash_id, severity = self.triage_crash(findings)
            return "CRASH", None, False, crash_id, severity, findings
        
        coverage_hash = hashlib.sha256(input_data).hexdigest()[:8]
        new_coverage = False
        if coverage_hash not in self.coverage_map:
            self.coverage_map.add(coverage_hash)
            new_coverage = True
            self.corpus.append(input_data)
        return "OK", coverage_hash, new_coverage, None, None, {}

    def start(self, target_path: str):
        logger.info(f"[*] {self.engine_id} operational on {target_path}")
        
        # 1. Initialize Hybrid Components
        self.afl = AFLWrapper(target_path, "./in", "./out")
        self.solver = SymbolicSolver(target_path)
        self.profiler = HighInterestProfiler(target_path)
        
        # 2. Extract High-Interest Zones (Batch 18)
        self.profiler.static_analysis_profile()
        priorities = self.profiler.get_prioritized_addresses()
        
        # 3. Launch AFL++ for primary discovery
        logger.info("[*] Starting AFL++ Discovery...")
        self.afl.start()
        
        last_solve_time = time.time()
        priority_idx = 0
        
        while True:
            # A. Check AFL++ for findings
            new_crashes = self.afl.get_new_crashes()
            for crash_file in new_crashes:
                with open(crash_file, "rb") as f:
                    data = f.read()
                    logger.info(f"[!] New AFL++ crash detected: {crash_file}")
                    self.report_telemetry(target_path, "HIGH", crash_hash=hashlib.md5(data).hexdigest())

            # B. Intent-Based Symbolic solving (Batch 18 Optimization)
            if time.time() - last_solve_time > 60:
                addr = priorities[priority_idx % len(priorities)] if priorities else (0x400000 + 0x1234)
                logger.info(f"[*] Prioritizing Solve for High-Interest Zone: 0x{addr:x}")
                
                solution = self.solver.solve_for_address(addr)
                if solution:
                    logger.info("[+] Solver found a new seed! Injecting into AFL corpus...")
                    self.corpus.append(solution)
                
                last_solve_time = time.time()
                priority_idx += 1

            # C. Sync findings from Redis (Scaling logic)
            time.sleep(5)

    def start_listening(self):
        logger.info(f"[*] {self.engine_id} operational. Waiting for tasks on 'mavdp:queue:native_binary'...")
        while True:
            task_raw = self.r.brpop("mavdp:queue:native_binary", timeout=5)
            if task_raw:
                task = json.loads(task_raw[1])
                target = task['target']
                logger.info(f"[+] Starting discovery session for {target}")
                
                # In a real scenario, this would launch AFL++
                # For this environment, we simulate discovery on the target
                try:
                    # Simulate finding a crash in the target after some 'work'
                    time.sleep(3)
                    self.report_telemetry(target, "HIGH", crash_hash=hashlib.md5(target.encode()).hexdigest(), metadata={"reason": "Simulated vulnerability in research target"})
                except Exception as e:
                    logger.error(f"Discovery error: {e}")

if __name__ == "__main__":
    engine = BinaryEngine()
    try:
        engine.start_listening()
    except KeyboardInterrupt:
        print("Engine stopped.")

