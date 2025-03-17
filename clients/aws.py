import asyncio
from pathlib import Path

import aioboto3


class AWSS3Client:
    def __init__(self, file_mappings, bucket_name):
        """
        Initialize the S3 client

        Args:
            file_mappings: List of tuples (file_path, s3_key)
            bucket_name: Name of the S3 bucket
        """
        self.session = aioboto3.Session()
        self.file_mappings = file_mappings  # List of tuples (file_path, s3_key)
        self.bucket_name = bucket_name

    async def upload_files(self):
        """Upload multiple files concurrently to S3"""
        tasks = [self.upload(file_path, s3_key) for file_path, s3_key in self.file_mappings]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results to identify failures
        successes = []
        failures = []
        for i, result in enumerate(results):
            file_path, s3_key = self.file_mappings[i]
            if isinstance(result, Exception):
                failures.append((file_path, s3_key, result))
            else:
                successes.append((file_path, s3_key))

        print(f"Uploaded {len(successes)} of {len(results)} files successfully")

        if failures:
            print("Failed uploads:")
            for file_path, s3_key, error in failures:
                print(f"  {Path(file_path).name} -> {s3_key}: {error}")

        return {
            "successes": successes,  # Tuple of (file_path, s3_key)
            "failures": failures,  # Tuple of (file_path, s3_key, exception)
            "total_files": len(self.file_mappings),
            "success_count": len(successes),
            "failure_count": len(failures)
        }

    async def upload(self, file_path: Path, s3_key: str) -> str:
        """Upload a single file to S3

        Args:
            file_path: Complete path to the file to upload
            s3_key: S3 key for the file

        Returns:
            The S3 key where the file was uploaded

        Raises:
            FileNotFoundError: If the file doesn't exist
            Various boto3 exceptions on upload failure
        """
        # Check if file exists
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        print(f"Uploading {file_path.name} to {s3_key}")

        # Upload the file
        async with self.session.client("s3") as s3:
            with open(file_path, "rb") as file_data:
                await s3.upload_fileobj(file_data, self.bucket_name, s3_key)

        return s3_key
