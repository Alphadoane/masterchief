import os
import logging
import time

# Note: In production, we'd use 'boto3' for S3/MinIO
try:
    import boto3
    from botocore.exceptions import ClientError
    S3_AVAILABLE = True
except ImportError:
    S3_AVAILABLE = False

logger = logging.getLogger("CorpusClient")

class CorpusClient:
    """
    Handles decentralized corpus synchronization.
    Saves and loads fuzzer seeds from cloud storage.
    """
    def __init__(self, bucket_name="mavdp-corpus"):
        self.endpoint = os.getenv("MINIO_ENDPOINT", "http://minio-service:9000")
        self.access_key = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
        self.secret_key = os.getenv("MINIO_SECRET_KEY", "minioadmin")
        self.bucket = bucket_name
        self.s3 = None
        
        if S3_AVAILABLE:
            self.s3 = boto3.client(
                's3',
                endpoint_url=self.endpoint,
                aws_access_key_id=self.access_key,
                aws_secret_access_key=self.secret_key
            )
            try:
                self.s3.create_bucket(Bucket=self.bucket)
            except Exception:
                pass # Already exists

    def sync_push(self, file_path: str, seed_name: str):
        """
        Uploads a new seed to the shared cloud corpus.
        """
        if not self.s3:
            logger.warning("S3 client not initialized. Mocking push.")
            return True
        
        try:
            self.s3.upload_file(file_path, self.bucket, seed_name)
            return True
        except Exception as e:
            logger.error(f"Failed to push corpus: {e}")
            return False

    def sync_pull_all(self, local_dir: str):
        """
        Downloads all seeds from the shared cloud corpus.
        """
        if not self.s3:
            logger.warning("S3 client not initialized. Mocking pull.")
            return []

        if not os.path.exists(local_dir):
            os.makedirs(local_dir)

        downloaded = []
        try:
            objects = self.s3.list_objects_v2(Bucket=self.bucket)
            for obj in objects.get('Contents', []):
                key = obj['Key']
                local_path = os.path.join(local_dir, key)
                self.s3.download_file(self.bucket, key, local_path)
                downloaded.append(local_path)
            return downloaded
        except Exception as e:
            logger.error(f"Failed to pull corpus: {e}")
            return []

if __name__ == "__main__":
    client = CorpusClient()
    print("[*] CorpusClient initialized.")
