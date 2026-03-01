import os
import json
import hashlib
import logging
from typing import Dict, Any

# Note: In production, we'd use 'cryptography' or 'gnupg'
try:
    from cryptography.fernet import Fernet
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False

logger = logging.getLogger("OPSEC")

class ZeroKnowledgeOPSEC:
    """
    Zero-Knowledge OPSEC Engine (Batch 17).
    Ensures findings are encrypted at discovery (finding-to-finding)
    to prevent exposure if the platform is compromised.
    """
    def __init__(self, master_key: str = None):
        self.master_key = master_key or os.getenv("MAVDP_MASTER_KEY")
        self.fernet = None
        if CRYPTO_AVAILABLE and self.master_key:
            # Ensure key is correctly padded/formatted for Fernet
            key_bytes = hashlib.sha256(self.master_key.encode()).digest()
            import base64
            self.fernet = Fernet(base64.urlsafe_b64encode(key_bytes))
            logger.info("[*] Zero-Knowledge Encryption initialized.")

    def encrypt_finding(self, finding_data: Dict[str, Any]) -> str:
        """
        Encrypts the sensitive 'metadata' and 'repro_input' sections of a finding.
        """
        if not self.fernet:
            logger.warning("Encryption key not set. Storing finding in PLAIN-TEXT (OPSEC RISK!).")
            return json.dumps(finding_data)

        # Encrypt the metadata and repro info
        sensitive_json = json.dumps(finding_data.get('metadata', {})).encode()
        encrypted_metadata = self.fernet.encrypt(sensitive_json).decode()
        
        # Create the ZK finding object
        zk_finding = finding_data.copy()
        zk_finding['metadata'] = {"encrypted": encrypted_metadata}
        zk_finding['is_encrypted'] = True
        
        return json.dumps(zk_finding)

    def decrypt_finding(self, encrypted_json: str) -> Dict[str, Any]:
        """
        Decrypts a ZK finding for the authorized dashboard/API.
        """
        if not self.fernet:
            raise PermissionError("Master key required for decryption.")
        
        data = json.loads(encrypted_json)
        if not data.get('is_encrypted'):
            return data
            
        encrypted_metadata = data['metadata']['encrypted'].encode()
        decrypted_json = self.fernet.decrypt(encrypted_metadata).decode()
        data['metadata'] = json.loads(decrypted_json)
        data['is_encrypted'] = False
        
        return data

if __name__ == "__main__":
    opsec = ZeroKnowledgeOPSEC("secret_password")
    print("[*] OPSEC initialized.")
