import subprocess
import os
import time
import logging
import signal
from typing import Optional

logger = logging.getLogger("AFLWrapper")

class AFLWrapper:
    """
    Orchestrates the AFL++ lifecyle.
    Handles startup, monitoring, and crash retrieval.
    """
    def __init__(self, binary_path: str, in_dir: str, out_dir: str):
        self.binary_path = binary_path
        self.in_dir = in_dir
        self.out_dir = out_dir
        self.process: Optional[subprocess.Popen] = None

    def start(self):
        """
        Launches afl-fuzz.
        Example command: afl-fuzz -i in -o out -- ./target @@
        """
        if not os.path.exists(self.in_dir):
            os.makedirs(self.in_dir)
            with open(os.path.join(self.in_dir, "seed"), "w") as f:
                f.write("initial_seed")

        cmd = [
            "afl-fuzz",
            "-i", self.in_dir,
            "-o", self.out_dir,
            "-m", "none", # No memory limit for research-grade binaries
            "--", self.binary_path, "@@"
        ]

        logger.info(f"Starting AFL++: {' '.join(cmd)}")
        try:
            # We run in a new process group to allow clean shutdown
            self.process = subprocess.Popen(
                cmd, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                preexec_fn=os.setsid
            )
        except FileNotFoundError:
            logger.error("afl-fuzz not found in PATH. Ensure AFL++ is installed.")
            self.process = None

    def stop(self):
        if self.process:
            logger.info("Stopping AFL++...")
            os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)
            self.process.wait()

    def get_new_crashes(self) -> list:
        """
        Scans the AFL output directory for new unique crashes.
        """
        crash_dir = os.path.join(self.out_dir, "default", "crashes")
        if not os.path.exists(crash_dir):
            return []
        
        crashes = []
        for f in os.listdir(crash_dir):
            if f.startswith("id:"):
                crashes.append(os.path.join(crash_dir, f))
        return crashes

if __name__ == "__main__":
    # Example usage
    wrapper = AFLWrapper("./target", "./in", "./out")
    print("[*] AFLWrapper initialized.")
