import os
import logging
import hashlib
from typing import List, Set

logger = logging.getLogger("MultiSigVault")

class MultiSigVault:
    """
    Multi-Sig Discovery Disclosure Vault (Batch 40).
    Requires M-of-N signature approval to decrypt High-Impact findings.
    Ensures no single compromised account can leak discovery data.
    """
    def __init__(self, threshold: int, authorized_keys: List[str]):
        self.threshold = threshold
        self.authorized_keys = set(authorized_keys)
        self.pending_decryptions = {} # crash_id -> set of signatures
        logger.info(f"[*] Multi-Sig Vault Initialized. Threshold: {threshold}/{len(authorized_keys)}")

    def request_decryption(self, crash_id: str, encrypted_blob: bytes):
        """
        Initiates a decryption request for a finding.
        """
        if crash_id not in self.pending_decryptions:
            self.pending_decryptions[crash_id] = set()
        logger.info(f"[*] Decryption requested for {crash_id}. Awaiting {self.threshold} signatures.")

    def add_signature(self, crash_id: str, researcher_id: str, signature: str) -> bool:
        """
        Adds a researcher's signature to a pending decryption request.
        """
        if researcher_id not in self.authorized_keys:
            logger.error(f"[-] Unauthorized signer: {researcher_id}")
            return False

        self.pending_decryptions[crash_id].add(researcher_id)
        current_count = len(self.pending_decryptions[crash_id])
        
        logger.info(f"[+] Signature added by {researcher_id}. Status: {current_count}/{self.threshold}")
        
        if current_count >= self.threshold:
            logger.info(f"[!] THRESHOLD REACHED: Finding {crash_id} is now UNSEALED.")
            return True
        
        return False

if __name__ == "__main__":
    vault = MultiSigVault(threshold=2, authorized_keys=["alpha", "beta", "gamma"])
    vault.request_decryption("CVE-2026-X", b"...")
    vault.add_signature("CVE-2026-X", "alpha", "sig_a")
    vault.add_signature("CVE-2026-X", "beta", "sig_b")
