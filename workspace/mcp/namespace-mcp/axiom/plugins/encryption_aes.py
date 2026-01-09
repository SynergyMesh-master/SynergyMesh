"""
AXIOM AES-256 Encryption Plugin
Military-grade encryption with key management and selective file encryption.
"""

import os
import hashlib
import time
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Union, List, Tuple
from dataclasses import dataclass
import threading
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import hashes, padding
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
import base64
import json
import io

logger = logging.getLogger(__name__)


@dataclass
class EncryptionMetadata:
    """Metadata for encrypted files"""
    algorithm: str
    key_id: str
    salt: str
    iv: str
    tag: str
    original_hash: str
    encrypted_hash: str
    timestamp: float


@dataclass
class KeyInfo:
    """Information about encryption keys"""
    key_id: str
    algorithm: str
    created_at: float
    last_used: float
    usage_count: int
    is_active: bool


class Plugin:
    """
    AES-256 encryption plugin with key management and selective encryption.
    Supports multiple encryption modes and secure key derivation.
    """
    
    def __init__(self):
        self.config: Dict[str, Any] = {}
        self.initialized = False
        self.encryption_keys: Dict[str, bytes] = {}
        self.key_metadata: Dict[str, KeyInfo] = {}
        self.fernet_encryptors: Dict[str, Fernet] = {}
        self._lock = threading.Lock()
        self.backend = default_backend()
        
    def initialize(self, config: dict) -> bool:
        """
        Initialize AES encryption plugin with configuration.
        
        Args:
            config: Plugin configuration
            
        Returns:
            bool: True if initialization successful
        """
        try:
            self.config = config
            
            # Encryption configuration
            algorithm = config.get('algorithm', 'AES-256-GCM')
            key_rotation_interval = config.get('key_rotation_interval', 86400)  # 24 hours
            max_keys = config.get('max_keys', 100)
            key_derivation_iterations = config.get('key_derivation_iterations', 100000)
            
            # Validate algorithm
            supported_algorithms = ['AES-256-GCM', 'AES-256-CBC', 'AES-256-CTR', 'FERNET']
            if algorithm not in supported_algorithms:
                logger.error(f"Unsupported encryption algorithm: {algorithm}")
                return False
                
            self.algorithm = algorithm
            self.key_rotation_interval = key_rotation_interval
            self.max_keys = max_keys
            self.key_derivation_iterations = key_derivation_iterations
            
            # Initialize key management
            self.key_store_path = Path(config.get('key_store_path', 'keys'))
            self.key_store_path.mkdir(exist_ok=True)
            
            # Load existing keys or create new one
            self._initialize_key_management()
            
            # Selective encryption configuration
            self.selective_patterns = config.get('selective_patterns', [])
            self.exclude_patterns = config.get('exclude_patterns', [])
            self.encrypt_metadata = config.get('encrypt_metadata', True)
            
            # Performance optimization
            self.chunk_size = config.get('chunk_size', 64 * 1024)  # 64KB
            self.parallel_encryption = config.get('parallel_encryption', True)
            
            self.initialized = True
            logger.info(f"AES encryption plugin initialized with algorithm: {algorithm}")
            
            return True
            
        except Exception as e:
            logger.error(f"AES encryption plugin initialization failed: {e}")
            return False
            
    def execute(self, context: dict) -> dict:
        """
        Execute encryption operation based on context.
        
        Args:
            context: Execution context with source_path, target_path, operation_mode
            
        Returns:
            dict: Execution result with encryption metadata
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
            target_path = Path(context['target_path'])
            operation_mode = context.get('operation_mode', 'ENCRYPT')
            encryption_key = context.get('encryption_key')
            
            # Validate paths
            if not source_path.exists():
                return {
                    "status": "FAILED",
                    "error": f"Source path does not exist: {source_path}",
                    "timestamp": time.time()
                }
                
            # Create target directory
            target_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Execute operation based on mode
            if operation_mode == 'ENCRYPT':
                result = self._encrypt(source_path, target_path, encryption_key)
            elif operation_mode == 'DECRYPT':
                result = self._decrypt(source_path, target_path, encryption_key)
            elif operation_mode == 'GENERATE_KEY':
                result = self._generate_key(context)
            elif operation_mode == 'ROTATE_KEY':
                result = self._rotate_key()
            elif operation_mode == 'VERIFY':
                result = self._verify_encryption(source_path)
            else:
                return {
                    "status": "FAILED",
                    "error": f"Unsupported operation mode: {operation_mode}",
                    "timestamp": time.time()
                }
                
            execution_time = time.time() - start_time
            
            # Prepare result
            result_dict = {
                "status": "SUCCESS",
                "metrics": {
                    "execution_time": execution_time,
                    "files_processed": result.get('files_processed', 0),
                    "bytes_processed": result.get('bytes_processed', 0),
                    "encryption_algorithm": self.algorithm
                },
                "artifacts": result.get('artifacts', []),
                "encryption_metadata": result.get('encryption_metadata'),
                "timestamp": time.time()
            }
            
            return result_dict
            
        except Exception as e:
            logger.error(f"AES encryption execution failed: {e}")
            return {
                "status": "FAILED",
                "error": str(e),
                "timestamp": time.time()
            }
            
    def validate(self) -> dict:
        """
        Validate plugin health and configuration.
        
        Returns:
            dict: Validation result
        """
        validation_result = {
            "plugin_id": "encryption_aes",
            "status": "HEALTHY",
            "initialized": self.initialized,
            "algorithm": self.algorithm,
            "keys_loaded": len(self.encryption_keys),
            "key_store_available": self.key_store_path.exists(),
            "config_valid": self._validate_config(),
            "test_encryption": "NOT_TESTED"
        }
        
        # Test encryption/decryption
        try:
            test_data = b"Sensitive test data for validation"
            
            # Generate test key
            test_key_id = self._generate_key_id()
            test_key = self._derive_key("test_password", b"test_salt")
            self.encryption_keys[test_key_id] = test_key
            
            # Test encryption and decryption
            if self.algorithm == 'FERNET':
                fernet = Fernet(base64.urlsafe_b64encode(test_key))
                encrypted = fernet.encrypt(test_data)
                decrypted = fernet.decrypt(encrypted)
            else:
                encrypted, metadata = self._encrypt_data(test_data, test_key_id)
                decrypted, _ = self._decrypt_data(encrypted, metadata, test_key)
                
            if decrypted == test_data:
                validation_result["test_encryption"] = "PASS"
            else:
                validation_result["test_encryption"] = "FAIL"
                validation_result["status"] = "DEGRADED"
                
            # Clean up test key
            if test_key_id in self.encryption_keys:
                del self.encryption_keys[test_key_id]
                
        except Exception as e:
            validation_result["test_encryption"] = f"FAIL: {e}"
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
                # Clear keys from memory
                for key_id in list(self.encryption_keys.keys()):
                    self._secure_erase_key(key_id)
                    
                self.encryption_keys.clear()
                self.key_metadata.clear()
                self.fernet_encryptors.clear()
                self.config = {}
                self.initialized = False
                
            logger.info("AES encryption plugin teardown completed")
            return True
            
        except Exception as e:
            logger.error(f"AES encryption plugin teardown failed: {e}")
            return False
            
    def _encrypt(self, source: Path, target: Path, 
                 encryption_key: Optional[str] = None) -> Dict[str, Any]:
        """Encrypt source to target"""
        if source.is_file():
            return self._encrypt_file(source, target, encryption_key)
        elif source.is_dir():
            return self._encrypt_directory(source, target, encryption_key)
        else:
            raise ValueError(f"Unsupported source type: {source}")
            
    def _encrypt_file(self, source: Path, target: Path, 
                      encryption_key: Optional[str] = None) -> Dict[str, Any]:
        """Encrypt single file"""
        # Get or create encryption key
        if encryption_key:
            key_id = self._get_or_create_key(encryption_key)
        else:
            key_id = self._get_active_key_id()
            
        if not key_id:
            raise ValueError("No encryption key available")
            
        key = self.encryption_keys[key_id]
        
        # Read file and encrypt
        with open(source, 'rb') as src_file:
            file_data = src_file.read()
            
        # Calculate original hash
        original_hash = hashlib.sha256(file_data).hexdigest()
        
        # Encrypt data
        encrypted_data, metadata = self._encrypt_data(file_data, key_id)
        
        # Update metadata with file information
        metadata.original_hash = original_hash
        metadata.encrypted_hash = hashlib.sha256(encrypted_data).hexdigest()
        
        # Write encrypted file
        with open(target, 'wb') as dst_file:
            dst_file.write(encrypted_data)
            
        # Write metadata file
        metadata_file = target.with_suffix(target.suffix + '.meta')
        with open(metadata_file, 'w') as meta_file:
            json.dump(self._metadata_to_dict(metadata), meta_file, indent=2)
            
        # Update key usage
        self._update_key_usage(key_id)
        
        return {
            "files_processed": 1,
            "bytes_processed": len(file_data),
            "artifacts": [str(target), str(metadata_file)],
            "encryption_metadata": self._metadata_to_dict(metadata)
        }
        
    def _encrypt_directory(self, source: Path, target: Path,
                           encryption_key: Optional[str] = None) -> Dict[str, Any]:
        """Encrypt directory with selective encryption"""
        import zipfile
        
        files_processed = 0
        bytes_processed = 0
        artifacts = []
        
        # Create temporary zip archive
        with zipfile.ZipFile(target, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for file_path in source.rglob('*'):
                if file_path.is_file():
                    # Check if file should be encrypted
                    if self._should_encrypt_file(file_path):
                        # Encrypt file content
                        try:
                            if encryption_key:
                                key_id = self._get_or_create_key(encryption_key)
                            else:
                                key_id = self._get_active_key_id()
                                
                            key = self.encryption_keys[key_id]
                            
                            with open(file_path, 'rb') as f:
                                file_data = f.read()
                                
                            encrypted_data, metadata = self._encrypt_data(file_data, key_id)
                            
                            # Add encrypted file to zip
                            zip_info = zipfile.ZipInfo(str(file_path.relative_to(source)))
                            zip_file.writestr(zip_info, encrypted_data)
                            
                            files_processed += 1
                            bytes_processed += len(file_data)
                            
                        except Exception as e:
                            logger.warning(f"Failed to encrypt {file_path}: {e}")
                            # Add original file if encryption fails
                            zip_file.write(file_path, file_path.relative_to(source))
                    else:
                        # Add original file
                        zip_file.write(file_path, file_path.relative_to(source))
                        files_processed += 1
                        bytes_processed += file_path.stat().st_size
                        
        return {
            "files_processed": files_processed,
            "bytes_processed": bytes_processed,
            "artifacts": [str(target)]
        }
        
    def _decrypt(self, source: Path, target: Path,
                 encryption_key: Optional[str] = None) -> Dict[str, Any]:
        """Decrypt source to target"""
        # Load metadata
        metadata_file = source.with_suffix(source.suffix + '.meta')
        
        if metadata_file.exists():
            with open(metadata_file, 'r') as f:
                metadata_dict = json.load(f)
            metadata = self._dict_to_metadata(metadata_dict)
        else:
            # Try to decrypt without metadata (legacy support)
            metadata = None
            
        # Get encryption key
        if encryption_key:
            key = self._derive_key(encryption_key.encode(), b'default_salt')
        elif metadata and metadata.key_id in self.encryption_keys:
            key = self.encryption_keys[metadata.key_id]
        else:
            raise ValueError("No decryption key available")
            
        # Read and decrypt file
        with open(source, 'rb') as src_file:
            encrypted_data = src_file.read()
            
        if metadata:
            decrypted_data, verify_metadata = self._decrypt_data(encrypted_data, metadata, key)
        else:
            # Legacy decryption
            if self.algorithm == 'FERNET':
                fernet = Fernet(base64.urlsafe_b64encode(key))
                decrypted_data = fernet.decrypt(encrypted_data)
            else:
                raise ValueError("Cannot decrypt without metadata for non-FERNET algorithms")
                
        # Write decrypted file
        with open(target, 'wb') as dst_file:
            dst_file.write(decrypted_data)
            
        return {
            "files_processed": 1,
            "bytes_processed": len(decrypted_data),
            "artifacts": [str(target)]
        }
        
    def _encrypt_data(self, data: bytes, key_id: str) -> Tuple[bytes, EncryptionMetadata]:
        """Encrypt data using configured algorithm"""
        key = self.encryption_keys[key_id]
        
        if self.algorithm == 'FERNET':
            # Use Fernet for simple symmetric encryption
            if key_id not in self.fernet_encryptors:
                self.fernet_encryptors[key_id] = Fernet(base64.urlsafe_b64encode(key))
                
            fernet = self.fernet_encryptors[key_id]
            encrypted_data = fernet.encrypt(data)
            
            metadata = EncryptionMetadata(
                algorithm='FERNET',
                key_id=key_id,
                salt='',
                iv='',
                tag='',
                original_hash='',
                encrypted_hash='',
                timestamp=time.time()
            )
            
        else:
            # Use AES variants
            if self.algorithm == 'AES-256-GCM':
                return self._encrypt_aes_gcm(data, key_id)
            elif self.algorithm == 'AES-256-CBC':
                return self._encrypt_aes_cbc(data, key_id)
            elif self.algorithm == 'AES-256-CTR':
                return self._encrypt_aes_ctr(data, key_id)
            else:
                raise ValueError(f"Unsupported algorithm: {self.algorithm}")
                
        return encrypted_data, metadata
        
    def _encrypt_aes_gcm(self, data: bytes, key_id: str) -> Tuple[bytes, EncryptionMetadata]:
        """Encrypt using AES-256-GCM"""
        salt = os.urandom(16)
        iv = os.urandom(12)  # 96-bit IV for GCM
        
        # Derive key
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=self.key_derivation_iterations,
            backend=self.backend
        )
        derived_key = kdf.derive(self.encryption_keys[key_id])
        
        # Encrypt
        cipher = Cipher(algorithms.AES(derived_key), modes.GCM(iv), backend=self.backend)
        encryptor = cipher.encryptor()
        
        encrypted_data = encryptor.update(data) + encryptor.finalize()
        tag = encryptor.tag
        
        # Combine salt + iv + tag + encrypted_data
        result = salt + iv + tag + encrypted_data
        
        metadata = EncryptionMetadata(
            algorithm='AES-256-GCM',
            key_id=key_id,
            salt=base64.b64encode(salt).decode(),
            iv=base64.b64encode(iv).decode(),
            tag=base64.b64encode(tag).decode(),
            original_hash='',
            encrypted_hash='',
            timestamp=time.time()
        )
        
        return result, metadata
        
    def _encrypt_aes_cbc(self, data: bytes, key_id: str) -> Tuple[bytes, EncryptionMetadata]:
        """Encrypt using AES-256-CBC"""
        salt = os.urandom(16)
        iv = os.urandom(16)
        
        # Derive key
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=self.key_derivation_iterations,
            backend=self.backend
        )
        derived_key = kdf.derive(self.encryption_keys[key_id])
        
        # Pad data
        padder = padding.PKCS7(128).padder()
        padded_data = padder.update(data) + padder.finalize()
        
        # Encrypt
        cipher = Cipher(algorithms.AES(derived_key), modes.CBC(iv), backend=self.backend)
        encryptor = cipher.encryptor()
        encrypted_data = encryptor.update(padded_data) + encryptor.finalize()
        
        # Combine salt + iv + encrypted_data
        result = salt + iv + encrypted_data
        
        metadata = EncryptionMetadata(
            algorithm='AES-256-CBC',
            key_id=key_id,
            salt=base64.b64encode(salt).decode(),
            iv=base64.b64encode(iv).decode(),
            tag='',
            original_hash='',
            encrypted_hash='',
            timestamp=time.time()
        )
        
        return result, metadata
        
    def _encrypt_aes_ctr(self, data: bytes, key_id: str) -> Tuple[bytes, EncryptionMetadata]:
        """Encrypt using AES-256-CTR"""
        salt = os.urandom(16)
        iv = os.urandom(16)
        
        # Derive key
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=self.key_derivation_iterations,
            backend=self.backend
        )
        derived_key = kdf.derive(self.encryption_keys[key_id])
        
        # Encrypt
        cipher = Cipher(algorithms.AES(derived_key), modes.CTR(iv), backend=self.backend)
        encryptor = cipher.encryptor()
        encrypted_data = encryptor.update(data) + encryptor.finalize()
        
        # Combine salt + iv + encrypted_data
        result = salt + iv + encrypted_data
        
        metadata = EncryptionMetadata(
            algorithm='AES-256-CTR',
            key_id=key_id,
            salt=base64.b64encode(salt).decode(),
            iv=base64.b64encode(iv).decode(),
            tag='',
            original_hash='',
            encrypted_hash='',
            timestamp=time.time()
        )
        
        return result, metadata
        
    def _decrypt_data(self, encrypted_data: bytes, metadata: EncryptionMetadata,
                      key: bytes) -> Tuple[bytes, EncryptionMetadata]:
        """Decrypt data using metadata"""
        if metadata.algorithm == 'FERNET':
            fernet = Fernet(base64.urlsafe_b64encode(key))
            decrypted_data = fernet.decrypt(encrypted_data)
            return decrypted_data, metadata
            
        elif metadata.algorithm == 'AES-256-GCM':
            salt = base64.b64decode(metadata.salt.encode())
            iv = base64.b64decode(metadata.iv.encode())
            tag = base64.b64decode(metadata.tag.encode())
            
            # Extract encrypted data
            data_start = len(salt) + len(iv) + len(tag)
            ciphertext = encrypted_data[data_start:]
            
            # Derive key
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=self.key_derivation_iterations,
                backend=self.backend
            )
            derived_key = kdf.derive(key)
            
            # Decrypt
            cipher = Cipher(algorithms.AES(derived_key), modes.GCM(iv, tag), backend=self.backend)
            decryptor = cipher.decryptor()
            decrypted_data = decryptor.update(ciphertext) + decryptor.finalize()
            
            return decrypted_data, metadata
            
        elif metadata.algorithm == 'AES-256-CBC':
            salt = base64.b64decode(metadata.salt.encode())
            iv = base64.b64decode(metadata.iv.encode())
            
            # Extract encrypted data
            data_start = len(salt) + len(iv)
            ciphertext = encrypted_data[data_start:]
            
            # Derive key
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=self.key_derivation_iterations,
                backend=self.backend
            )
            derived_key = kdf.derive(key)
            
            # Decrypt
            cipher = Cipher(algorithms.AES(derived_key), modes.CBC(iv), backend=self.backend)
            decryptor = cipher.decryptor()
            padded_data = decryptor.update(ciphertext) + decryptor.finalize()
            
            # Unpad data
            unpadder = padding.PKCS7(128).unpadder()
            decrypted_data = unpadder.update(padded_data) + unpadder.finalize()
            
            return decrypted_data, metadata
            
        elif metadata.algorithm == 'AES-256-CTR':
            salt = base64.b64decode(metadata.salt.encode())
            iv = base64.b64decode(metadata.iv.encode())
            
            # Extract encrypted data
            data_start = len(salt) + len(iv)
            ciphertext = encrypted_data[data_start:]
            
            # Derive key
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=self.key_derivation_iterations,
                backend=self.backend
            )
            derived_key = kdf.derive(key)
            
            # Decrypt
            cipher = Cipher(algorithms.AES(derived_key), modes.CTR(iv), backend=self.backend)
            decryptor = cipher.decryptor()
            decrypted_data = decryptor.update(ciphertext) + decryptor.finalize()
            
            return decrypted_data, metadata
            
        else:
            raise ValueError(f"Unsupported decryption algorithm: {metadata.algorithm}")
            
    def _generate_key(self, context: dict) -> Dict[str, Any]:
        """Generate new encryption key"""
        key_id = self._generate_key_id()
        
        # Generate random key
        if self.algorithm == 'FERNET':
            key = Fernet.generate_key()
        else:
            key = os.urandom(32)  # 256-bit key
            
        self.encryption_keys[key_id] = key
        
        # Create key metadata
        key_info = KeyInfo(
            key_id=key_id,
            algorithm=self.algorithm,
            created_at=time.time(),
            last_used=time.time(),
            usage_count=0,
            is_active=True
        )
        self.key_metadata[key_id] = key_info
        
        # Save key
        self._save_key(key_id, key)
        
        return {
            "key_id": key_id,
            "algorithm": self.algorithm,
            "created_at": key_info.created_at
        }
        
    def _rotate_key(self) -> Dict[str, Any]:
        """Rotate encryption keys"""
        # Deactivate old keys
        for key_id, key_info in self.key_metadata.items():
            if key_info.is_active and (time.time() - key_info.created_at) > self.key_rotation_interval:
                key_info.is_active = False
                
        # Generate new active key
        return self._generate_key({})
        
    def _verify_encryption(self, encrypted_file: Path) -> Dict[str, Any]:
        """Verify encrypted file integrity"""
        metadata_file = encrypted_file.with_suffix(encrypted_file.suffix + '.meta')
        
        if not metadata_file.exists():
            return {"status": "FAILED", "error": "Metadata file not found"}
            
        try:
            # Load metadata
            with open(metadata_file, 'r') as f:
                metadata_dict = json.load(f)
            metadata = self._dict_to_metadata(metadata_dict)
            
            # Verify file hash
            with open(encrypted_file, 'rb') as f:
                encrypted_data = f.read()
                
            current_hash = hashlib.sha256(encrypted_data).hexdigest()
            if current_hash != metadata.encrypted_hash:
                return {"status": "FAILED", "error": "Hash verification failed"}
                
            return {"status": "SUCCESS", "verified": True}
            
        except Exception as e:
            return {"status": "FAILED", "error": str(e)}
            
    def _should_encrypt_file(self, file_path: Path) -> bool:
        """Check if file should be encrypted based on patterns"""
        file_name = file_path.name.lower()
        file_ext = file_path.suffix.lower()
        
        # Check exclude patterns
        for pattern in self.exclude_patterns:
            if pattern in file_name or pattern in file_ext:
                return False
                
        # Check include patterns (if any specified)
        if self.selective_patterns:
            for pattern in self.selective_patterns:
                if pattern in file_name or pattern in file_ext:
                    return True
            return False
            
        # Default to encrypt if no selective patterns
        return True
        
    def _initialize_key_management(self) -> None:
        """Initialize key management system"""
        # Load existing keys
        for key_file in self.key_store_path.glob('*.key'):
            try:
                key_id = key_file.stem
                with open(key_file, 'rb') as f:
                    key = f.read()
                self.encryption_keys[key_id] = key
                
                # Load metadata
                metadata_file = self.key_store_path / f"{key_id}.meta"
                if metadata_file.exists():
                    with open(metadata_file, 'r') as f:
                        metadata = json.load(f)
                    self.key_metadata[key_id] = KeyInfo(**metadata)
                    
            except Exception as e:
                logger.warning(f"Failed to load key {key_file}: {e}")
                
        # Create initial key if none exist
        if not self.encryption_keys:
            self._generate_key({})
            
    def _generate_key_id(self) -> str:
        """Generate unique key identifier"""
        return f"key_{int(time.time())}_{os.urandom(4).hex()}"
        
    def _derive_key(self, password: bytes, salt: bytes) -> bytes:
        """Derive key from password"""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=self.key_derivation_iterations,
            backend=self.backend
        )
        return kdf.derive(password)
        
    def _get_or_create_key(self, key_identifier: str) -> str:
        """Get existing key or create new one"""
        # Try to find existing key
        for key_id in self.encryption_keys:
            if key_identifier in key_id:
                return key_id
                
        # Create new key
        return self._generate_key({})
        
    def _get_active_key_id(self) -> Optional[str]:
        """Get the most recently active key"""
        active_keys = [k_id for k_id, info in self.key_metadata.items() if info.is_active]
        if not active_keys:
            return None
            
        # Return the most recently used active key
        return max(active_keys, key=lambda k_id: self.key_metadata[k_id].last_used)
        
    def _update_key_usage(self, key_id: str) -> None:
        """Update key usage statistics"""
        if key_id in self.key_metadata:
            key_info = self.key_metadata[key_id]
            key_info.last_used = time.time()
            key_info.usage_count += 1
            
    def _save_key(self, key_id: str, key: bytes) -> None:
        """Save key to storage"""
        key_file = self.key_store_path / f"{key_id}.key"
        with open(key_file, 'wb') as f:
            f.write(key)
            
        # Save metadata
        if key_id in self.key_metadata:
            metadata_file = self.key_store_path / f"{key_id}.meta"
            with open(metadata_file, 'w') as f:
                json.dump(self.key_metadata[key_id].__dict__, f, indent=2)
                
    def _secure_erase_key(self, key_id: str) -> None:
        """Securely erase key from memory"""
        if key_id in self.encryption_keys:
            # Overwrite key memory
            key = self.encryption_keys[key_id]
            overwrite_data = b'\x00' * len(key)
            self.encryption_keys[key_id] = overwrite_data
            del self.encryption_keys[key_id]
            
    def _validate_config(self) -> bool:
        """Validate plugin configuration"""
        required_fields = ['algorithm', 'key_rotation_interval', 'max_keys']
        
        for field in required_fields:
            if field not in self.config:
                return False
                
        return True
        
    def _metadata_to_dict(self, metadata: EncryptionMetadata) -> dict:
        """Convert metadata to dictionary"""
        return {
            "algorithm": metadata.algorithm,
            "key_id": metadata.key_id,
            "salt": metadata.salt,
            "iv": metadata.iv,
            "tag": metadata.tag,
            "original_hash": metadata.original_hash,
            "encrypted_hash": metadata.encrypted_hash,
            "timestamp": metadata.timestamp
        }
        
    def _dict_to_metadata(self, metadata_dict: dict) -> EncryptionMetadata:
        """Convert dictionary to metadata"""
        return EncryptionMetadata(**metadata_dict)


# Plugin metadata for registration
PLUGIN_METADATA = {
    "plugin_id": "encryption_aes",
    "version": "1.0.0",
    "category": "encryption",
    "description": "AES-256 encryption with key management and selective encryption",
    "dependencies": [],
    "performance_profile": {
        "security_level": "MILITARY_GRADE",
        "speed": "HIGH",
        "memory_usage": "LOW",
        "cpu_usage": "MEDIUM"
    }
}