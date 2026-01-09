"""
AXIOM S3 Storage Backend Plugin
Cloud storage integration with S3, multipart uploads, and advanced features.
"""

import os
import json
import time
import logging
import threading
import hashlib
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple, BinaryIO
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    import boto3
    from botocore.exceptions import ClientError, NoCredentialsError
    from botocore.config import Config
    import multipart
    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False
    boto3 = None

logger = logging.getLogger(__name__)


@dataclass
class S3Config:
    """S3 configuration parameters"""
    bucket_name: str
    region: str
    access_key_id: Optional[str] = None
    secret_access_key: Optional[str] = None
    session_token: Optional[str] = None
    endpoint_url: Optional[str] = None
    use_ssl: bool = True
    verify_ssl: bool = True
    signature_version: str = 's3v4'
    addressing_style: str = 'auto'


@dataclass
class UploadMetrics:
    """Metrics for upload operations"""
    files_uploaded: int
    bytes_uploaded: int
    upload_time: float
    upload_speed: float  # MB/s
    multipart_uploads: int
    failed_uploads: int


@dataclass
class S3ObjectMetadata:
    """Metadata for S3 objects"""
    key: str
    size: int
    etag: str
    last_modified: float
    storage_class: str
    metadata: Dict[str, str]


class Plugin:
    """
    S3 storage backend plugin with multipart uploads, retry logic,
    and advanced cloud storage features.
    """
    
    def __init__(self):
        self.config: Dict[str, Any] = {}
        self.initialized = False
        self.s3_client = None
        self.s3_resource = None
        self.bucket = None
        self.upload_config = {}
        self._lock = threading.Lock()
        self.executor = ThreadPoolExecutor(max_workers=8)
        
    def initialize(self, config: dict) -> bool:
        """
        Initialize S3 storage plugin.
        
        Args:
            config: Plugin configuration
            
        Returns:
            bool: True if initialization successful
        """
        if not BOTO3_AVAILABLE:
            logger.error("boto3 not available. Install with: pip install boto3")
            return False
            
        try:
            self.config = config
            
            # Extract S3 configuration
            s3_config = S3Config(
                bucket_name=config['bucket_name'],
                region=config.get('region', 'us-east-1'),
                access_key_id=config.get('access_key_id'),
                secret_access_key=config.get('secret_access_key'),
                session_token=config.get('session_token'),
                endpoint_url=config.get('endpoint_url'),
                use_ssl=config.get('use_ssl', True),
                verify_ssl=config.get('verify_ssl', True),
                signature_version=config.get('signature_version', 's3v4'),
                addressing_style=config.get('addressing_style', 'auto')
            )
            
            # Configure boto3
            boto_config = Config(
                region_name=s3_config.region,
                signature_version=s3_config.signature_version,
                s3={'addressing_style': s3_config.addressing_style},
                retries={'max_attempts': config.get('max_retries', 3)},
                max_pool_connections=config.get('max_pool_connections', 50)
            )
            
            # Create S3 client
            self.s3_client = boto3.client(
                's3',
                endpoint_url=s3_config.endpoint_url,
                aws_access_key_id=s3_config.access_key_id,
                aws_secret_access_key=s3_config.secret_access_key,
                aws_session_token=s3_config.session_token,
                config=boto_config,
                use_ssl=s3_config.use_ssl,
                verify=s3_config.verify_ssl
            )
            
            # Create S3 resource
            self.s3_resource = boto3.resource(
                's3',
                endpoint_url=s3_config.endpoint_url,
                aws_access_key_id=s3_config.access_key_id,
                aws_secret_access_key=s3_config.secret_access_key,
                aws_session_token=s3_config.session_token,
                config=boto_config,
                use_ssl=s3_config.use_ssl,
                verify=s3_config.verify_ssl
            )
            
            # Get bucket reference
            self.bucket = self.s3_resource.Bucket(s3_config.bucket_name)
            
            # Upload configuration
            self.upload_config = {
                'multipart_threshold': config.get('multipart_threshold', 64 * 1024 * 1024),  # 64MB
                'multipart_chunksize': config.get('multipart_chunksize', 16 * 1024 * 1024),  # 16MB
                'max_concurrency': config.get('max_concurrency', 8),
                'use_threads': config.get('use_threads', True),
                'storage_class': config.get('storage_class', 'STANDARD'),
                'server_side_encryption': config.get('server_side_encryption', 'AES256'),
                'metadata': config.get('default_metadata', {}),
                'tags': config.get('default_tags', {}),
                'content_type_detection': config.get('content_type_detection', True)
            }
            
            # Test connection
            if not self._test_connection():
                return False
                
            # Create bucket if it doesn't exist
            if not self._bucket_exists():
                self._create_bucket()
                
            self.initialized = True
            logger.info(f"S3 storage plugin initialized for bucket: {s3_config.bucket_name}")
            
            return True
            
        except Exception as e:
            logger.error(f"S3 storage plugin initialization failed: {e}")
            return False
            
    def execute(self, context: dict) -> dict:
        """
        Execute storage operation based on context.
        
        Args:
            context: Execution context with source_path, target_path, operation_mode
            
        Returns:
            dict: Execution result with storage metrics
        """
        if not self.initialized:
            return {
                "status": "FAILED",
                "error": "Plugin not initialized",
                "timestamp": time.time()
            }
            
        try:
            start_time = time.time()
            
            # Extract context parameters
            source_path = Path(context['source_path'])
            operation_mode = context.get('operation_mode', 'UPLOAD')
            
            # Validate source path
            if not source_path.exists():
                return {
                    "status": "FAILED",
                    "error": f"Source path does not exist: {source_path}",
                    "timestamp": time.time()
                }
                
            # Execute operation based on mode
            if operation_mode == 'UPLOAD':
                result = self._upload_to_s3(source_path, context)
            elif operation_mode == 'DOWNLOAD':
                result = self._download_from_s3(source_path, Path(context['target_path']))
            elif operation_mode == 'LIST':
                result = self._list_s3_objects(context)
            elif operation_mode == 'DELETE':
                result = self._delete_from_s3(context)
            elif operation_mode == 'SYNC':
                result = self._sync_to_s3(source_path, context)
            elif operation_mode == 'VERIFY':
                result = self._verify_s3_integrity(context)
            else:
                return {
                    "status": "FAILED",
                    "error": f"Unsupported operation mode: {operation_mode}",
                    "timestamp": time.time()
                }
                
            execution_time = time.time() - start_time
            
            # Prepare result
            return {
                "status": "SUCCESS",
                "metrics": {
                    "execution_time": execution_time,
                    "files_processed": result.get('files_processed', 0),
                    "bytes_transferred": result.get('bytes_transferred', 0),
                    "transfer_speed": result.get('transfer_speed', 0.0),
                    "operation": operation_mode
                },
                "artifacts": result.get('artifacts', []),
                "s3_objects": result.get('s3_objects', []),
                "timestamp": time.time()
            }
            
        except Exception as e:
            logger.error(f"S3 storage execution failed: {e}")
            return {
                "status": "FAILED",
                "error": str(e),
                "timestamp": time.time()
            }
            
    def validate(self) -> dict:
        """
        Validate plugin health and S3 connectivity.
        
        Returns:
            dict: Validation result
        """
        validation_result = {
            "plugin_id": "storage_s3",
            "status": "HEALTHY",
            "initialized": self.initialized,
            "boto3_available": BOTO3_AVAILABLE,
            "s3_client_available": self.s3_client is not None,
            "bucket_accessible": False,
            "config_valid": self._validate_config(),
            "test_upload": "NOT_TESTED"
        }
        
        if self.initialized and self.s3_client:
            try:
                # Test bucket access
                self.s3_client.head_bucket(Bucket=self.bucket.name)
                validation_result["bucket_accessible"] = True
                
                # Test upload/download
                test_key = f"axiom_test_{int(time.time())}.txt"
                test_data = b"S3 plugin test data"
                
                # Upload test file
                self.s3_client.put_object(
                    Bucket=self.bucket.name,
                    Key=test_key,
                    Body=test_data,
                    Metadata={'test': 'true'}
                )
                
                # Download and verify
                response = self.s3_client.get_object(Bucket=self.bucket.name, Key=test_key)
                downloaded_data = response['Body'].read()
                
                if downloaded_data == test_data:
                    validation_result["test_upload"] = "PASS"
                else:
                    validation_result["test_upload"] = "FAIL"
                    validation_result["status"] = "DEGRADED"
                    
                # Clean up test file
                self.s3_client.delete_object(Bucket=self.bucket.name, Key=test_key)
                
            except Exception as e:
                validation_result["test_upload"] = f"FAIL: {e}"
                validation_result["status"] = "FAILED"
                
        return validation_result
        
    def teardown(self) -> bool:
        """
        Cleanup resources and prepare for unload.
        
        Returns:
            bool: True if teardown successful
        """
        try:
            with self._lock:
                # Shutdown thread pool
                if self.executor:
                    self.executor.shutdown(wait=True)
                    
                self.s3_client = None
                self.s3_resource = None
                self.bucket = None
                self.config = {}
                self.initialized = False
                
            logger.info("S3 storage plugin teardown completed")
            return True
            
        except Exception as e:
            logger.error(f"S3 storage plugin teardown failed: {e}")
            return False
            
    def _upload_to_s3(self, source_path: Path, context: dict) -> Dict[str, Any]:
        """Upload file or directory to S3"""
        s3_prefix = context.get('s3_prefix', '')
        
        if source_path.is_file():
            return self._upload_file(source_path, s3_prefix)
        elif source_path.is_dir():
            return self._upload_directory(source_path, s3_prefix)
        else:
            raise ValueError(f"Unsupported source type: {source_path}")
            
    def _upload_file(self, local_file: Path, s3_prefix: str = '') -> Dict[str, Any]:
        """Upload single file to S3"""
        file_size = local_file.stat().st_size
        s3_key = f"{s3_prefix}/{local_file.name}" if s3_prefix else local_file.name
        
        # Determine upload method
        if file_size > self.upload_config['multipart_threshold']:
            result = self._multipart_upload(local_file, s3_key)
        else:
            result = self._simple_upload(local_file, s3_key)
            
        return {
            "files_processed": 1,
            "bytes_transferred": result['bytes_uploaded'],
            "transfer_speed": result['upload_speed'],
            "s3_objects": [result['s3_object']],
            "artifacts": [s3_key]
        }
        
    def _upload_directory(self, local_dir: Path, s3_prefix: str = '') -> Dict[str, Any]:
        """Upload directory to S3"""
        files_uploaded = 0
        bytes_uploaded = 0
        s3_objects = []
        artifacts = []
        
        # Collect all files
        files_to_upload = []
        for file_path in local_dir.rglob('*'):
            if file_path.is_file():
                relative_path = file_path.relative_to(local_dir)
                files_to_upload.append((file_path, relative_path))
                
        # Upload files concurrently if enabled
        if self.upload_config['use_threads'] and len(files_to_upload) > 1:
            futures = []
            
            for file_path, relative_path in files_to_upload:
                s3_key = f"{s3_prefix}/{relative_path}" if s3_prefix else str(relative_path)
                future = self.executor.submit(self._upload_file_internal, file_path, s3_key)
                futures.append((future, s3_key))
                
            for future, s3_key in futures:
                try:
                    result = future.result()
                    files_uploaded += 1
                    bytes_uploaded += result['bytes_uploaded']
                    s3_objects.append(result['s3_object'])
                    artifacts.append(s3_key)
                except Exception as e:
                    logger.error(f"Failed to upload {s3_key}: {e}")
        else:
            # Sequential upload
            for file_path, relative_path in files_to_upload:
                s3_key = f"{s3_prefix}/{relative_path}" if s3_prefix else str(relative_path)
                try:
                    result = self._upload_file_internal(file_path, s3_key)
                    files_uploaded += 1
                    bytes_uploaded += result['bytes_uploaded']
                    s3_objects.append(result['s3_object'])
                    artifacts.append(s3_key)
                except Exception as e:
                    logger.error(f"Failed to upload {s3_key}: {e}")
                    
        return {
            "files_processed": files_uploaded,
            "bytes_transferred": bytes_uploaded,
            "transfer_speed": bytes_uploaded / (time.time() - time.time() or 0.001) / (1024*1024),
            "s3_objects": s3_objects,
            "artifacts": artifacts
        }
        
    def _upload_file_internal(self, local_file: Path, s3_key: str) -> Dict[str, Any]:
        """Internal file upload method"""
        file_size = local_file.stat().st_size
        
        if file_size > self.upload_config['multipart_threshold']:
            return self._multipart_upload(local_file, s3_key)
        else:
            return self._simple_upload(local_file, s3_key)
            
    def _simple_upload(self, local_file: Path, s3_key: str) -> Dict[str, Any]:
        """Simple file upload"""
        start_time = time.time()
        
        # Prepare upload parameters
        upload_args = {
            'Bucket': self.bucket.name,
            'Key': s3_key,
            'StorageClass': self.upload_config['storage_class']
        }
        
        if self.upload_config['server_side_encryption']:
            upload_args['ServerSideEncryption'] = self.upload_config['server_side_encryption']
            
        # Add metadata
        metadata = self.upload_config['metadata'].copy()
        metadata['original_filename'] = local_file.name
        metadata['upload_time'] = str(int(time.time()))
        metadata['file_hash'] = self._calculate_file_hash(local_file)
        upload_args['Metadata'] = metadata
        
        # Add content type
        if self.upload_config['content_type_detection']:
            import mimetypes
            content_type, _ = mimetypes.guess_type(str(local_file))
            if content_type:
                upload_args['ContentType'] = content_type
                
        # Upload file
        with open(local_file, 'rb') as f:
            upload_args['Body'] = f
            response = self.s3_client.put_object(**upload_args)
            
        upload_time = time.time() - start_time
        file_size = local_file.stat().st_size
        upload_speed = (file_size / (1024*1024)) / upload_time if upload_time > 0 else 0
        
        s3_object = {
            'key': s3_key,
            'etag': response['ETag'].strip('"'),
            'size': file_size,
            'storage_class': self.upload_config['storage_class']
        }
        
        return {
            's3_object': s3_object,
            'bytes_uploaded': file_size,
            'upload_speed': upload_speed
        }
        
    def _multipart_upload(self, local_file: Path, s3_key: str) -> Dict[str, Any]:
        """Multipart upload for large files"""
        start_time = time.time()
        
        # Initiate multipart upload
        initiate_args = {
            'Bucket': self.bucket.name,
            'Key': s3_key,
            'StorageClass': self.upload_config['storage_class']
        }
        
        if self.upload_config['server_side_encryption']:
            initiate_args['ServerSideEncryption'] = self.upload_config['server_side_encryption']
            
        # Add metadata
        metadata = self.upload_config['metadata'].copy()
        metadata['original_filename'] = local_file.name
        metadata['upload_time'] = str(int(time.time()))
        metadata['file_hash'] = self._calculate_file_hash(local_file)
        metadata['upload_type'] = 'multipart'
        initiate_args['Metadata'] = metadata
        
        # Add content type
        if self.upload_config['content_type_detection']:
            import mimetypes
            content_type, _ = mimetypes.guess_type(str(local_file))
            if content_type:
                initiate_args['ContentType'] = content_type
                
        response = self.s3_client.create_multipart_upload(**initiate_args)
        upload_id = response['UploadId']
        
        try:
            # Upload parts
            parts = []
            part_number = 1
            bytes_uploaded = 0
            
            with open(local_file, 'rb') as f:
                while True:
                    chunk = f.read(self.upload_config['multipart_chunksize'])
                    if not chunk:
                        break
                        
                    part_response = self.s3_client.upload_part(
                        Bucket=self.bucket.name,
                        Key=s3_key,
                        PartNumber=part_number,
                        UploadId=upload_id,
                        Body=chunk
                    )
                    
                    parts.append({
                        'ETag': part_response['ETag'],
                        'PartNumber': part_number
                    })
                    
                    bytes_uploaded += len(chunk)
                    part_number += 1
                    
            # Complete multipart upload
            complete_args = {
                'Bucket': self.bucket.name,
                'Key': s3_key,
                'UploadId': upload_id,
                'MultipartUpload': {'Parts': parts}
            }
            
            complete_response = self.s3_client.complete_multipart_upload(**complete_args)
            
        except Exception as e:
            # Abort multipart upload on error
            try:
                self.s3_client.abort_multipart_upload(
                    Bucket=self.bucket.name,
                    Key=s3_key,
                    UploadId=upload_id
                )
            except:
                pass
            raise e
            
        upload_time = time.time() - start_time
        file_size = local_file.stat().st_size
        upload_speed = (file_size / (1024*1024)) / upload_time if upload_time > 0 else 0
        
        s3_object = {
            'key': s3_key,
            'etag': complete_response['ETag'].strip('"'),
            'size': file_size,
            'storage_class': self.upload_config['storage_class']
        }
        
        return {
            's3_object': s3_object,
            'bytes_uploaded': bytes_uploaded,
            'upload_speed': upload_speed
        }
        
    def _download_from_s3(self, s3_path: Path, local_target: Path) -> Dict[str, Any]:
        """Download file or directory from S3"""
        local_target.mkdir(parents=True, exist_ok=True)
        
        if isinstance(s3_path, str):
            # Single file download
            return self._download_file(s3_path, local_target)
        else:
            # Multiple files download
            return self._download_files(s3_path, local_target)
            
    def _download_file(self, s3_key: str, local_file: Path) -> Dict[str, Any]:
        """Download single file from S3"""
        start_time = time.time()
        
        try:
            response = self.s3_client.get_object(Bucket=self.bucket.name, Key=s3_key)
            
            with open(local_file, 'wb') as f:
                for chunk in response['Body'].iter_chunks(chunk_size=8192):
                    f.write(chunk)
                    
            download_time = time.time() - start_time
            file_size = local_file.stat().st_size
            download_speed = (file_size / (1024*1024)) / download_time if download_time > 0 else 0
            
            return {
                "files_processed": 1,
                "bytes_transferred": file_size,
                "transfer_speed": download_speed,
                "artifacts": [str(local_file)]
            }
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                return {
                    "status": "FAILED",
                    "error": f"S3 object not found: {s3_key}"
                }
            raise e
            
    def _download_files(self, s3_prefix: str, local_dir: Path) -> Dict[str, Any]:
        """Download multiple files from S3"""
        files_downloaded = 0
        bytes_downloaded = 0
        artifacts = []
        
        # List objects with prefix
        paginator = self.s3_client.get_paginator('list_objects_v2')
        pages = paginator.paginate(Bucket=self.bucket.name, Prefix=s3_prefix)
        
        for page in pages:
            if 'Contents' in page:
                for obj in page['Contents']:
                    s3_key = obj['Key']
                    
                    # Calculate local file path
                    relative_path = s3_key[len(s3_prefix):].lstrip('/')
                    local_file = local_dir / relative_path
                    local_file.parent.mkdir(parents=True, exist_ok=True)
                    
                    try:
                        result = self._download_file(s3_key, local_file)
                        files_downloaded += result['files_processed']
                        bytes_downloaded += result['bytes_transferred']
                        artifacts.extend(result['artifacts'])
                    except Exception as e:
                        logger.error(f"Failed to download {s3_key}: {e}")
                        
        return {
            "files_processed": files_downloaded,
            "bytes_transferred": bytes_downloaded,
            "transfer_speed": bytes_downloaded / (time.time() - time.time() or 0.001) / (1024*1024),
            "artifacts": artifacts
        }
        
    def _list_s3_objects(self, context: dict) -> Dict[str, Any]:
        """List objects in S3 bucket"""
        prefix = context.get('s3_prefix', '')
        max_keys = context.get('max_keys', 1000)
        
        objects = []
        paginator = self.s3_client.get_paginator('list_objects_v2')
        pages = paginator.paginate(Bucket=self.bucket.name, Prefix=prefix, PaginationConfig={'MaxItems': max_keys})
        
        for page in pages:
            if 'Contents' in page:
                for obj in page['Contents']:
                    s3_object = {
                        'key': obj['Key'],
                        'size': obj['Size'],
                        'last_modified': obj['LastModified'].timestamp(),
                        'etag': obj['ETag'].strip('"'),
                        'storage_class': obj.get('StorageClass', 'STANDARD')
                    }
                    objects.append(s3_object)
                    
        return {
            "objects": objects,
            "total_count": len(objects)
        }
        
    def _delete_from_s3(self, context: dict) -> Dict[str, Any]:
        """Delete objects from S3"""
        keys_to_delete = context.get('s3_keys', [])
        if isinstance(keys_to_delete, str):
            keys_to_delete = [keys_to_delete]
            
        deleted_count = 0
        failed_count = 0
        
        # Delete in batches of 1000 (S3 limit)
        for i in range(0, len(keys_to_delete), 1000):
            batch = keys_to_delete[i:i+1000]
            
            delete_objects = [{'Key': key} for key in batch]
            
            try:
                response = self.s3_client.delete_objects(
                    Bucket=self.bucket.name,
                    Delete={'Objects': delete_objects}
                )
                
                deleted_count += len(response.get('Deleted', []))
                
                if 'Errors' in response:
                    failed_count += len(response['Errors'])
                    for error in response['Errors']:
                        logger.error(f"Failed to delete {error['Key']}: {error['Message']}")
                        
            except Exception as e:
                logger.error(f"Batch delete failed: {e}")
                failed_count += len(batch)
                
        return {
            "deleted_count": deleted_count,
            "failed_count": failed_count
        }
        
    def _sync_to_s3(self, local_path: Path, context: dict) -> Dict[str, Any]:
        """Sync local directory to S3"""
        s3_prefix = context.get('s3_prefix', '')
        delete_removed = context.get('delete_removed', False)
        
        # Get local files
        local_files = set()
        for file_path in local_path.rglob('*'):
            if file_path.is_file():
                relative_path = file_path.relative_to(local_path)
                s3_key = f"{s3_prefix}/{relative_path}" if s3_prefix else str(relative_path)
                local_files.add((s3_key, file_path))
                
        # Get S3 files
        s3_objects = self._list_s3_objects({'s3_prefix': s3_prefix})['objects']
        s3_files = {obj['key'] for obj in s3_objects}
        
        # Upload new/modified files
        files_to_upload = []
        for s3_key, local_file in local_files:
            if s3_key not in s3_files:
                files_to_upload.append((local_file, s3_key, 'NEW'))
            else:
                # Check if file is modified
                local_hash = self._calculate_file_hash(local_file)
                s3_hash = self._get_s3_object_hash(s3_key)
                
                if local_hash != s3_hash:
                    files_to_upload.append((local_file, s3_key, 'MODIFIED'))
                    
        # Upload files
        uploaded_count = 0
        bytes_uploaded = 0
        
        for local_file, s3_key, reason in files_to_upload:
            try:
                result = self._upload_file_internal(local_file, s3_key)
                uploaded_count += 1
                bytes_uploaded += result['bytes_uploaded']
                logger.debug(f"Uploaded {s3_key} ({reason})")
            except Exception as e:
                logger.error(f"Failed to upload {s3_key}: {e}")
                
        # Delete files from S3 if requested
        deleted_count = 0
        if delete_removed:
            s3_files_to_delete = s3_files - {s3_key for s3_key, _ in local_files}
            if s3_files_to_delete:
                delete_result = self._delete_from_s3({'s3_keys': list(s3_files_to_delete)})
                deleted_count = delete_result['deleted_count']
                
        return {
            "files_processed": uploaded_count,
            "bytes_transferred": bytes_uploaded,
            "files_uploaded": uploaded_count,
            "files_deleted": deleted_count
        }
        
    def _verify_s3_integrity(self, context: dict) -> Dict[str, Any]:
        """Verify integrity of S3 objects"""
        s3_keys = context.get('s3_keys', [])
        if isinstance(s3_keys, str):
            s3_keys = [s3_keys]
            
        verified_count = 0
        failed_count = 0
        
        for s3_key in s3_keys:
            try:
                # Get object metadata
                response = self.s3_client.head_object(Bucket=self.bucket.name, Key=s3_key)
                
                # Get local file hash if available
                original_hash = response.get('Metadata', {}).get('file_hash')
                
                if original_hash:
                    # Download and verify
                    import tempfile
                    with tempfile.NamedTemporaryFile() as tmp:
                        self.s3_client.download_fileobj(
                            Bucket=self.bucket.name,
                            Key=s3_key,
                            Fileobj=tmp
                        )
                        tmp.seek(0)
                        downloaded_hash = hashlib.sha256(tmp.read()).hexdigest()
                        
                        if downloaded_hash == original_hash:
                            verified_count += 1
                        else:
                            failed_count += 1
                            logger.warning(f"Hash mismatch for {s3_key}")
                else:
                    # Basic check - ensure object exists
                    verified_count += 1
                    
            except Exception as e:
                logger.error(f"Failed to verify {s3_key}: {e}")
                failed_count += 1
                
        return {
            "verified_count": verified_count,
            "failed_count": failed_count,
            "total_checked": len(s3_keys)
        }
        
    def _test_connection(self) -> bool:
        """Test S3 connection and credentials"""
        try:
            self.s3_client.head_bucket(Bucket=self.bucket.name)
            return True
        except NoCredentialsError:
            logger.error("AWS credentials not found")
            return False
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                logger.error(f"Bucket {self.bucket.name} not found")
            else:
                logger.error(f"S3 connection test failed: {e}")
            return False
        except Exception as e:
            logger.error(f"S3 connection test failed: {e}")
            return False
            
    def _bucket_exists(self) -> bool:
        """Check if bucket exists"""
        try:
            self.s3_client.head_bucket(Bucket=self.bucket.name)
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                return False
            raise e
            
    def _create_bucket(self) -> None:
        """Create S3 bucket"""
        create_args = {'Bucket': self.bucket.name}
        
        # Only include region for non-us-east-1
        if self.bucket.name.startswith('s3://') == False and self.config.get('region') != 'us-east-1':
            create_args['CreateBucketConfiguration'] = {
                'LocationConstraint': self.config.get('region')
            }
            
        self.s3_client.create_bucket(**create_args)
        logger.info(f"Created S3 bucket: {self.bucket.name}")
        
    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA256 hash of file"""
        hash_sha256 = hashlib.sha256()
        
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
                
        return hash_sha256.hexdigest()
        
    def _get_s3_object_hash(self, s3_key: str) -> Optional[str]:
        """Get stored hash of S3 object from metadata"""
        try:
            response = self.s3_client.head_object(Bucket=self.bucket.name, Key=s3_key)
            return response.get('Metadata', {}).get('file_hash')
        except:
            return None
            
    def _validate_config(self) -> bool:
        """Validate plugin configuration"""
        required_fields = ['bucket_name']
        
        for field in required_fields:
            if field not in self.config:
                return False
                
        return True


# Plugin metadata for registration
PLUGIN_METADATA = {
    "plugin_id": "storage_s3",
    "version": "1.0.0",
    "category": "storage_backend",
    "description": "S3 cloud storage with multipart uploads and advanced features",
    "dependencies": ["boto3"],
    "performance_profile": {
        "speed": "HIGH",
        "scalability": "UNLIMITED",
        "reliability": "HIGH",
        "cost_efficiency": "MEDIUM"
    }
}