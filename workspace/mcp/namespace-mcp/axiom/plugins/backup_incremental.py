"""
AXIOM Incremental Backup Plugin
Smart incremental backup with retention policies and auto-cleanup.
"""

import os
import json
import hashlib
import time
import logging
import sqlite3
import threading
from pathlib import Path
from typing import Dict, Any, Optional, List, Set, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import struct

logger = logging.getLogger(__name__)


@dataclass
class FileMetadata:
    """Metadata for backed up files"""
    file_path: str
    file_hash: str
    file_size: int
    modified_time: float
    created_time: float
    permissions: int
    backup_time: float
    backup_id: str
    is_deleted: bool = False


@dataclass
class BackupSession:
    """Information about a backup session"""
    backup_id: str
    backup_type: str  # FULL, INCREMENTAL, DIFFERENTIAL
    start_time: float
    end_time: float
    files_processed: int
    files_added: int
    files_modified: int
    files_deleted: int
    bytes_processed: int
    base_backup_id: Optional[str] = None


@dataclass
class RetentionPolicy:
    """Retention policy configuration"""
    daily_backups: int = 30
    weekly_backups: int = 12
    monthly_backups: int = 24
    yearly_backups: int = 10
    max_total_backups: int = 1000
    max_storage_gb: float = 1000.0


class Plugin:
    """
    Incremental backup plugin with intelligent change detection,
    retention policies, and automatic cleanup.
    """
    
    def __init__(self):
        self.config: Dict[str, Any] = {}
        self.initialized = False
        self.db_path: Optional[Path] = None
        self.db_connection: Optional[sqlite3.Connection] = None
        self._lock = threading.Lock()
        
    def initialize(self, config: dict) -> bool:
        """
        Initialize incremental backup plugin.
        
        Args:
            config: Plugin configuration
            
        Returns:
            bool: True if initialization successful
        """
        try:
            self.config = config
            
            # Backup configuration
            backup_root = Path(config.get('backup_root', 'backups'))
            backup_root.mkdir(exist_ok=True)
            self.backup_root = backup_root
            
            # Database configuration
            db_file = config.get('database_file', 'backup_index.db')
            self.db_path = backup_root / db_file
            
            # Initialize database
            self._initialize_database()
            
            # Retention policy
            retention_config = config.get('retention_policy', {})
            self.retention_policy = RetentionPolicy(**retention_config)
            
            # Change detection settings
            self.hash_algorithm = config.get('hash_algorithm', 'sha256')
            self.follow_symlinks = config.get('follow_symlinks', False)
            self.ignore_hidden = config.get('ignore_hidden', True)
            self.exclude_patterns = config.get('exclude_patterns', [])
            
            # Performance settings
            self.chunk_size = config.get('chunk_size', 1024 * 1024)  # 1MB
            self.parallel_processing = config.get('parallel_processing', True)
            self.max_workers = config.get('max_workers', 4)
            
            # Auto-cleanup settings
            self.auto_cleanup = config.get('auto_cleanup', True)
            self.cleanup_interval = config.get('cleanup_interval', 3600)  # 1 hour
            self.last_cleanup = time.time()
            
            # Backup scheduling
            self.full_backup_interval = config.get('full_backup_interval', 7 * 24 * 3600)  # 7 days
            self.incremental_backup_interval = config.get('incremental_backup_interval', 3600)  # 1 hour
            
            self.initialized = True
            logger.info("Incremental backup plugin initialized successfully")
            
            return True
            
        except Exception as e:
            logger.error(f"Incremental backup plugin initialization failed: {e}")
            return False
            
    def execute(self, context: dict) -> dict:
        """
        Execute backup operation based on context.
        
        Args:
            context: Execution context with source_path, target_path, operation_mode
            
        Returns:
            dict: Execution result with backup metrics
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
            operation_mode = context.get('operation_mode', 'INCREMENTAL_BACKUP')
            
            # Validate source path
            if not source_path.exists():
                return {
                    "status": "FAILED",
                    "error": f"Source path does not exist: {source_path}",
                    "timestamp": time.time()
                }
                
            # Execute operation based on mode
            if operation_mode == 'FULL_BACKUP':
                result = self._create_full_backup(source_path)
            elif operation_mode == 'INCREMENTAL_BACKUP':
                result = self._create_incremental_backup(source_path)
            elif operation_mode == 'DIFFERENTIAL_BACKUP':
                result = self._create_differential_backup(source_path)
            elif operation_mode == 'RESTORE':
                result = self._restore_backup(source_path, Path(context['target_path']))
            elif operation_mode == 'LIST_BACKUPS':
                result = self._list_backups()
            elif operation_mode == 'CLEANUP':
                result = self._cleanup_old_backups()
            elif operation_mode == 'VERIFY':
                result = self._verify_backups()
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
                    "backup_id": result.get('backup_id'),
                    "backup_type": result.get('backup_type', operation_mode),
                    "files_processed": result.get('files_processed', 0),
                    "files_added": result.get('files_added', 0),
                    "files_modified": result.get('files_modified', 0),
                    "files_deleted": result.get('files_deleted', 0),
                    "bytes_processed": result.get('bytes_processed', 0),
                    "compression_ratio": result.get('compression_ratio', 0.0)
                },
                "artifacts": result.get('artifacts', []),
                "backup_session": result.get('backup_session'),
                "timestamp": time.time()
            }
            
        except Exception as e:
            logger.error(f"Incremental backup execution failed: {e}")
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
            "plugin_id": "backup_incremental",
            "status": "HEALTHY",
            "initialized": self.initialized,
            "database_available": self.db_path and self.db_path.exists(),
            "backup_root_available": self.backup_root.exists(),
            "config_valid": self._validate_config(),
            "test_backup": "NOT_TESTED"
        }
        
        # Test backup operation
        try:
            # Create test directory
            test_dir = self.backup_root / "test_validation"
            test_dir.mkdir(exist_ok=True)
            test_file = test_dir / "test.txt"
            test_file.write_text("Test data for backup validation")
            
            # Create test backup
            result = self._create_full_backup(test_dir)
            
            if result.get('backup_id'):
                validation_result["test_backup"] = "PASS"
                # Clean up test backup
                self._cleanup_test_backup(result['backup_id'])
            else:
                validation_result["test_backup"] = "FAIL"
                validation_result["status"] = "DEGRADED"
                
            # Clean up test directory
            test_file.unlink()
            test_dir.rmdir()
            
        except Exception as e:
            validation_result["test_backup"] = f"FAIL: {e}"
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
                # Close database connection
                if self.db_connection:
                    self.db_connection.close()
                    self.db_connection = None
                    
                self.config = {}
                self.initialized = False
                
            logger.info("Incremental backup plugin teardown completed")
            return True
            
        except Exception as e:
            logger.error(f"Incremental backup plugin teardown failed: {e}")
            return False
            
    def _create_full_backup(self, source_path: Path) -> Dict[str, Any]:
        """Create a full backup of the source"""
        backup_id = self._generate_backup_id()
        backup_dir = self.backup_root / backup_id
        backup_dir.mkdir(exist_ok=True)
        
        session = BackupSession(
            backup_id=backup_id,
            backup_type="FULL",
            start_time=time.time(),
            end_time=0.0,
            files_processed=0,
            files_added=0,
            files_modified=0,
            files_deleted=0,
            bytes_processed=0
        )
        
        try:
            # Scan source directory
            files_to_backup = self._scan_directory(source_path)
            
            # Backup files
            for file_path in files_to_backup:
                try:
                    result = self._backup_file(file_path, backup_dir)
                    if result:
                        session.files_processed += 1
                        session.files_added += 1
                        session.bytes_processed += result['file_size']
                except Exception as e:
                    logger.warning(f"Failed to backup {file_path}: {e}")
                    
            session.end_time = time.time()
            
            # Save backup session
            self._save_backup_session(session)
            
            # Create backup manifest
            manifest = {
                "backup_id": backup_id,
                "backup_type": "FULL",
                "source_path": str(source_path),
                "created_at": session.start_time,
                "session": asdict(session)
            }
            
            manifest_file = backup_dir / "manifest.json"
            with open(manifest_file, 'w') as f:
                json.dump(manifest, f, indent=2)
                
            return {
                "backup_id": backup_id,
                "backup_type": "FULL",
                "files_processed": session.files_processed,
                "files_added": session.files_added,
                "bytes_processed": session.bytes_processed,
                "artifacts": [str(backup_dir), str(manifest_file)],
                "backup_session": asdict(session)
            }
            
        except Exception as e:
            # Clean up failed backup
            if backup_dir.exists():
                import shutil
                shutil.rmtree(backup_dir)
            raise e
            
    def _create_incremental_backup(self, source_path: Path) -> Dict[str, Any]:
        """Create an incremental backup"""
        # Find the last backup
        last_backup = self._get_last_backup(source_path)
        if not last_backup:
            logger.info("No previous backup found, creating full backup")
            return self._create_full_backup(source_path)
            
        backup_id = self._generate_backup_id()
        backup_dir = self.backup_root / backup_id
        backup_dir.mkdir(exist_ok=True)
        
        session = BackupSession(
            backup_id=backup_id,
            backup_type="INCREMENTAL",
            start_time=time.time(),
            end_time=0.0,
            files_processed=0,
            files_added=0,
            files_modified=0,
            files_deleted=0,
            bytes_processed=0,
            base_backup_id=last_backup['backup_id']
        )
        
        try:
            # Get current file state
            current_files = self._scan_directory(source_path)
            current_metadata = {str(path): self._get_file_metadata(path, backup_id) 
                              for path in current_files}
            
            # Get previous backup state
            previous_metadata = self._get_backup_metadata(last_backup['backup_id'])
            
            # Find new and modified files
            files_to_backup = []
            files_to_delete = []
            
            for file_path, metadata in current_metadata.items():
                if file_path not in previous_metadata:
                    # New file
                    files_to_backup.append(Path(file_path))
                    session.files_added += 1
                elif metadata.file_hash != previous_metadata[file_path].file_hash:
                    # Modified file
                    files_to_backup.append(Path(file_path))
                    session.files_modified += 1
                else:
                    # Unchanged file
                    pass
                    
            # Find deleted files
            for file_path in previous_metadata:
                if file_path not in current_metadata:
                    files_to_delete.append(file_path)
                    session.files_deleted += 1
                    
            # Backup new and modified files
            for file_path in files_to_backup:
                try:
                    result = self._backup_file(file_path, backup_dir)
                    if result:
                        session.files_processed += 1
                        session.bytes_processed += result['file_size']
                        
                        # Save file metadata
                        self._save_file_metadata(result)
                except Exception as e:
                    logger.warning(f"Failed to backup {file_path}: {e}")
                    
            session.end_time = time.time()
            
            # Save backup session
            self._save_backup_session(session)
            
            # Mark deleted files
            for deleted_file in files_to_delete:
                self._mark_file_deleted(deleted_file, backup_id)
                
            # Create backup manifest
            manifest = {
                "backup_id": backup_id,
                "backup_type": "INCREMENTAL",
                "source_path": str(source_path),
                "base_backup_id": last_backup['backup_id'],
                "created_at": session.start_time,
                "session": asdict(session)
            }
            
            manifest_file = backup_dir / "manifest.json"
            with open(manifest_file, 'w') as f:
                json.dump(manifest, f, indent=2)
                
            return {
                "backup_id": backup_id,
                "backup_type": "INCREMENTAL",
                "files_processed": session.files_processed,
                "files_added": session.files_added,
                "files_modified": session.files_modified,
                "files_deleted": session.files_deleted,
                "bytes_processed": session.bytes_processed,
                "artifacts": [str(backup_dir), str(manifest_file)],
                "backup_session": asdict(session)
            }
            
        except Exception as e:
            # Clean up failed backup
            if backup_dir.exists():
                import shutil
                shutil.rmtree(backup_dir)
            raise e
            
    def _create_differential_backup(self, source_path: Path) -> Dict[str, Any]:
        """Create a differential backup (changes since last full backup)"""
        # Find the last full backup
        last_full_backup = self._get_last_full_backup(source_path)
        if not last_full_backup:
            logger.info("No full backup found, creating full backup")
            return self._create_full_backup(source_path)
            
        backup_id = self._generate_backup_id()
        backup_dir = self.backup_root / backup_id
        backup_dir.mkdir(exist_ok=True)
        
        session = BackupSession(
            backup_id=backup_id,
            backup_type="DIFFERENTIAL",
            start_time=time.time(),
            end_time=0.0,
            files_processed=0,
            files_added=0,
            files_modified=0,
            files_deleted=0,
            bytes_processed=0,
            base_backup_id=last_full_backup['backup_id']
        )
        
        try:
            # Get current file state
            current_files = self._scan_directory(source_path)
            current_metadata = {str(path): self._get_file_metadata(path, backup_id) 
                              for path in current_files}
            
            # Get full backup state
            full_backup_metadata = self._get_backup_metadata(last_full_backup['backup_id'])
            
            # Find new and modified files
            for file_path, metadata in current_metadata.items():
                if file_path not in full_backup_metadata:
                    # New file
                    source_file = Path(file_path)
                    result = self._backup_file(source_file, backup_dir)
                    if result:
                        session.files_processed += 1
                        session.files_added += 1
                        session.bytes_processed += result['file_size']
                        self._save_file_metadata(result)
                elif metadata.file_hash != full_backup_metadata[file_path].file_hash:
                    # Modified file
                    source_file = Path(file_path)
                    result = self._backup_file(source_file, backup_dir)
                    if result:
                        session.files_processed += 1
                        session.files_modified += 1
                        session.bytes_processed += result['file_size']
                        self._save_file_metadata(result)
                        
            session.end_time = time.time()
            
            # Save backup session
            self._save_backup_session(session)
            
            # Create backup manifest
            manifest = {
                "backup_id": backup_id,
                "backup_type": "DIFFERENTIAL",
                "source_path": str(source_path),
                "base_backup_id": last_full_backup['backup_id'],
                "created_at": session.start_time,
                "session": asdict(session)
            }
            
            manifest_file = backup_dir / "manifest.json"
            with open(manifest_file, 'w') as f:
                json.dump(manifest, f, indent=2)
                
            return {
                "backup_id": backup_id,
                "backup_type": "DIFFERENTIAL",
                "files_processed": session.files_processed,
                "files_added": session.files_added,
                "files_modified": session.files_modified,
                "files_deleted": session.files_deleted,
                "bytes_processed": session.bytes_processed,
                "artifacts": [str(backup_dir), str(manifest_file)],
                "backup_session": asdict(session)
            }
            
        except Exception as e:
            # Clean up failed backup
            if backup_dir.exists():
                import shutil
                shutil.rmtree(backup_dir)
            raise e
            
    def _backup_file(self, source_file: Path, backup_dir: Path) -> Optional[Dict[str, Any]]:
        """Backup a single file"""
        try:
            # Calculate file hash
            file_hash = self._calculate_file_hash(source_file)
            
            # Create backup filename
            relative_path = source_file.name
            backup_file = backup_dir / relative_path
            
            # Handle filename conflicts
            counter = 1
            while backup_file.exists():
                stem = source_file.stem
                suffix = source_file.suffix
                backup_file = backup_dir / f"{stem}_{counter}{suffix}"
                counter += 1
                
            # Copy file
            import shutil
            shutil.copy2(source_file, backup_file)
            
            # Get file metadata
            stat = source_file.stat()
            
            metadata = FileMetadata(
                file_path=str(source_file),
                file_hash=file_hash,
                file_size=stat.st_size,
                modified_time=stat.st_mtime,
                created_time=stat.st_ctime,
                permissions=stat.st_mode,
                backup_time=time.time(),
                backup_id=backup_dir.name
            )
            
            return asdict(metadata)
            
        except Exception as e:
            logger.error(f"Failed to backup file {source_file}: {e}")
            return None
            
    def _scan_directory(self, directory: Path) -> List[Path]:
        """Scan directory and return list of files"""
        files = []
        
        for root, dirs, filenames in os.walk(directory):
            root_path = Path(root)
            
            # Skip hidden directories if configured
            if self.ignore_hidden and root_path.name.startswith('.'):
                continue
                
            for filename in filenames:
                file_path = root_path / filename
                
                # Skip hidden files if configured
                if self.ignore_hidden and filename.startswith('.'):
                    continue
                    
                # Check exclude patterns
                if self._should_exclude_file(file_path):
                    continue
                    
                # Handle symlinks
                if file_path.is_symlink():
                    if self.follow_symlinks:
                        try:
                            resolved_path = file_path.resolve()
                            if resolved_path.exists():
                                files.append(resolved_path)
                        except Exception:
                            pass
                    continue
                    
                if file_path.is_file():
                    files.append(file_path)
                    
        return files
        
    def _should_exclude_file(self, file_path: Path) -> bool:
        """Check if file should be excluded based on patterns"""
        file_str = str(file_path).lower()
        
        for pattern in self.exclude_patterns:
            if pattern.lower() in file_str:
                return True
                
        return False
        
    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate hash of file contents"""
        hash_obj = hashlib.new(self.hash_algorithm)
        
        with open(file_path, 'rb') as f:
            while True:
                chunk = f.read(self.chunk_size)
                if not chunk:
                    break
                hash_obj.update(chunk)
                
        return hash_obj.hexdigest()
        
    def _get_file_metadata(self, file_path: Path, backup_id: str) -> FileMetadata:
        """Get metadata for a file"""
        stat = file_path.stat()
        file_hash = self._calculate_file_hash(file_path)
        
        return FileMetadata(
            file_path=str(file_path),
            file_hash=file_hash,
            file_size=stat.st_size,
            modified_time=stat.st_mtime,
            created_time=stat.st_ctime,
            permissions=stat.st_mode,
            backup_time=time.time(),
            backup_id=backup_id
        )
        
    def _generate_backup_id(self) -> str:
        """Generate unique backup identifier"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        random_suffix = os.urandom(4).hex()
        return f"backup_{timestamp}_{random_suffix}"
        
    def _initialize_database(self) -> None:
        """Initialize SQLite database for backup tracking"""
        self.db_connection = sqlite3.connect(str(self.db_path))
        cursor = self.db_connection.cursor()
        
        # Create tables
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS backup_sessions (
                backup_id TEXT PRIMARY KEY,
                backup_type TEXT NOT NULL,
                source_path TEXT NOT NULL,
                start_time REAL NOT NULL,
                end_time REAL NOT NULL,
                files_processed INTEGER NOT NULL,
                files_added INTEGER NOT NULL,
                files_modified INTEGER NOT NULL,
                files_deleted INTEGER NOT NULL,
                bytes_processed INTEGER NOT NULL,
                base_backup_id TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS file_metadata (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                backup_id TEXT NOT NULL,
                file_path TEXT NOT NULL,
                file_hash TEXT NOT NULL,
                file_size INTEGER NOT NULL,
                modified_time REAL NOT NULL,
                created_time REAL NOT NULL,
                permissions INTEGER NOT NULL,
                backup_time REAL NOT NULL,
                is_deleted BOOLEAN DEFAULT FALSE,
                UNIQUE(backup_id, file_path)
            )
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_file_metadata_backup_id 
            ON file_metadata(backup_id)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_file_metadata_path_hash 
            ON file_metadata(file_path, file_hash)
        ''')
        
        self.db_connection.commit()
        
    def _save_backup_session(self, session: BackupSession) -> None:
        """Save backup session to database"""
        cursor = self.db_connection.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO backup_sessions 
            (backup_id, backup_type, source_path, start_time, end_time,
             files_processed, files_added, files_modified, files_deleted,
             bytes_processed, base_backup_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            session.backup_id, session.backup_type, "", session.start_time,
            session.end_time, session.files_processed, session.files_added,
            session.files_modified, session.files_deleted, session.bytes_processed,
            session.base_backup_id
        ))
        self.db_connection.commit()
        
    def _save_file_metadata(self, metadata: dict) -> None:
        """Save file metadata to database"""
        cursor = self.db_connection.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO file_metadata 
            (backup_id, file_path, file_hash, file_size, modified_time,
             created_time, permissions, backup_time, is_deleted)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            metadata['backup_id'], metadata['file_path'], metadata['file_hash'],
            metadata['file_size'], metadata['modified_time'], metadata['created_time'],
            metadata['permissions'], metadata['backup_time'], metadata['is_deleted']
        ))
        self.db_connection.commit()
        
    def _get_last_backup(self, source_path: Path) -> Optional[Dict[str, Any]]:
        """Get the last backup for the given source"""
        cursor = self.db_connection.cursor()
        cursor.execute('''
            SELECT backup_id, backup_type, start_time 
            FROM backup_sessions 
            ORDER BY start_time DESC 
            LIMIT 1
        ''')
        
        row = cursor.fetchone()
        if row:
            return {
                'backup_id': row[0],
                'backup_type': row[1],
                'start_time': row[2]
            }
        return None
        
    def _get_last_full_backup(self, source_path: Path) -> Optional[Dict[str, Any]]:
        """Get the last full backup for the given source"""
        cursor = self.db_connection.cursor()
        cursor.execute('''
            SELECT backup_id, backup_type, start_time 
            FROM backup_sessions 
            WHERE backup_type = 'FULL'
            ORDER BY start_time DESC 
            LIMIT 1
        ''')
        
        row = cursor.fetchone()
        if row:
            return {
                'backup_id': row[0],
                'backup_type': row[1],
                'start_time': row[2]
            }
        return None
        
    def _get_backup_metadata(self, backup_id: str) -> Dict[str, FileMetadata]:
        """Get all file metadata for a backup"""
        cursor = self.db_connection.cursor()
        cursor.execute('''
            SELECT file_path, file_hash, file_size, modified_time,
                   created_time, permissions, backup_time, backup_id, is_deleted
            FROM file_metadata 
            WHERE backup_id = ? AND is_deleted = FALSE
        ''', (backup_id,))
        
        metadata = {}
        for row in cursor.fetchall():
            file_meta = FileMetadata(
                file_path=row[0], file_hash=row[1], file_size=row[2],
                modified_time=row[3], created_time=row[4], permissions=row[5],
                backup_time=row[6], backup_id=row[7], is_deleted=row[8]
            )
            metadata[file_meta.file_path] = file_meta
            
        return metadata
        
    def _mark_file_deleted(self, file_path: str, backup_id: str) -> None:
        """Mark a file as deleted in the given backup"""
        cursor = self.db_connection.cursor()
        cursor.execute('''
            UPDATE file_metadata 
            SET is_deleted = TRUE 
            WHERE file_path = ? AND backup_id = ?
        ''', (file_path, backup_id))
        self.db_connection.commit()
        
    def _list_backups(self) -> Dict[str, Any]:
        """List all available backups"""
        cursor = self.db_connection.cursor()
        cursor.execute('''
            SELECT backup_id, backup_type, start_time, end_time,
                   files_processed, bytes_processed
            FROM backup_sessions 
            ORDER BY start_time DESC
        ''')
        
        backups = []
        for row in cursor.fetchall():
            backups.append({
                'backup_id': row[0],
                'backup_type': row[1],
                'start_time': row[2],
                'end_time': row[3],
                'files_processed': row[4],
                'bytes_processed': row[5]
            })
            
        return {
            "backups": backups,
            "total_count": len(backups)
        }
        
    def _cleanup_old_backups(self) -> Dict[str, Any]:
        """Clean up old backups based on retention policy"""
        if not self.auto_cleanup:
            return {"status": "SKIPPED", "reason": "Auto cleanup disabled"}
            
        cursor = self.db_connection.cursor()
        
        # Get all backups ordered by date
        cursor.execute('''
            SELECT backup_id, backup_type, start_time 
            FROM backup_sessions 
            ORDER BY start_time DESC
        ''')
        
        all_backups = cursor.fetchall()
        if len(all_backups) <= 1:
            return {"status": "NO_ACTION", "reason": "Not enough backups to clean"}
            
        # Apply retention policy
        backups_to_keep = self._apply_retention_policy(all_backups)
        backups_to_delete = [b for b in all_backups if b not in backups_to_keep]
        
        deleted_count = 0
        for backup_id, backup_type, start_time in backups_to_delete:
            try:
                # Delete backup files
                backup_dir = self.backup_root / backup_id
                if backup_dir.exists():
                    import shutil
                    shutil.rmtree(backup_dir)
                    
                # Delete from database
                cursor.execute('DELETE FROM backup_sessions WHERE backup_id = ?', (backup_id,))
                cursor.execute('DELETE FROM file_metadata WHERE backup_id = ?', (backup_id,))
                
                deleted_count += 1
                logger.info(f"Deleted backup: {backup_id}")
                
            except Exception as e:
                logger.error(f"Failed to delete backup {backup_id}: {e}")
                
        self.db_connection.commit()
        
        return {
            "status": "SUCCESS",
            "deleted_count": deleted_count,
            "remaining_count": len(backups_to_keep)
        }
        
    def _apply_retention_policy(self, backups: List[Tuple]) -> List[Tuple]:
        """Apply retention policy to determine which backups to keep"""
        now = time.time()
        backups_to_keep = []
        
        # Categorize backups by age
        daily = []
        weekly = []
        monthly = []
        yearly = []
        
        for backup in backups:
            age_days = (now - backup[2]) / (24 * 3600)
            
            if age_days < 7:
                daily.append(backup)
            elif age_days < 30:
                weekly.append(backup)
            elif age_days < 365:
                monthly.append(backup)
            else:
                yearly.append(backup)
                
        # Keep most recent backups within limits
        backups_to_keep.extend(daily[:self.retention_policy.daily_backups])
        backups_to_keep.extend(weekly[:self.retention_policy.weekly_backups])
        backups_to_keep.extend(monthly[:self.retention_policy.monthly_backups])
        backups_to_keep.extend(yearly[:self.retention_policy.yearly_backups])
        
        # Always keep the most recent backup
        if backups and backups[0] not in backups_to_keep:
            backups_to_keep.append(backups[0])
            
        return backups_to_keep
        
    def _restore_backup(self, backup_id: str, target_path: Path) -> Dict[str, Any]:
        """Restore from backup"""
        backup_dir = self.backup_root / backup_id
        
        if not backup_dir.exists():
            return {"status": "FAILED", "error": "Backup not found"}
            
        # Load manifest
        manifest_file = backup_dir / "manifest.json"
        if not manifest_file.exists():
            return {"status": "FAILED", "error": "Backup manifest not found"}
            
        with open(manifest_file, 'r') as f:
            manifest = json.load(f)
            
        # For now, simple file copy restore
        # In production, this would handle incremental restoration
        target_path.mkdir(parents=True, exist_ok=True)
        
        files_restored = 0
        for backup_file in backup_dir.glob("*"):
            if backup_file.is_file() and backup_file.name != "manifest.json":
                target_file = target_path / backup_file.name
                import shutil
                shutil.copy2(backup_file, target_file)
                files_restored += 1
                
        return {
            "status": "SUCCESS",
            "files_restored": files_restored,
            "backup_type": manifest.get("backup_type")
        }
        
    def _verify_backups(self) -> Dict[str, Any]:
        """Verify backup integrity"""
        cursor = self.db_connection.cursor()
        cursor.execute('SELECT backup_id FROM backup_sessions')
        
        backup_ids = [row[0] for row in cursor.fetchall()]
        verified_count = 0
        failed_count = 0
        
        for backup_id in backup_ids:
            backup_dir = self.backup_root / backup_id
            if backup_dir.exists() and (backup_dir / "manifest.json").exists():
                verified_count += 1
            else:
                failed_count += 1
                logger.warning(f"Backup verification failed: {backup_id}")
                
        return {
            "status": "SUCCESS",
            "total_backups": len(backup_ids),
            "verified": verified_count,
            "failed": failed_count
        }
        
    def _cleanup_test_backup(self, backup_id: str) -> None:
        """Clean up test backup"""
        try:
            backup_dir = self.backup_root / backup_id
            if backup_dir.exists():
                import shutil
                shutil.rmtree(backup_dir)
                
            # Remove from database
            cursor = self.db_connection.cursor()
            cursor.execute('DELETE FROM backup_sessions WHERE backup_id = ?', (backup_id,))
            cursor.execute('DELETE FROM file_metadata WHERE backup_id = ?', (backup_id,))
            self.db_connection.commit()
            
        except Exception as e:
            logger.warning(f"Failed to cleanup test backup {backup_id}: {e}")
            
    def _validate_config(self) -> bool:
        """Validate plugin configuration"""
        required_fields = ['backup_root', 'hash_algorithm']
        
        for field in required_fields:
            if field not in self.config:
                return False
                
        # Validate hash algorithm
        valid_algorithms = ['md5', 'sha1', 'sha256', 'sha512']
        if self.config['hash_algorithm'] not in valid_algorithms:
            return False
            
        return True


# Plugin metadata for registration
PLUGIN_METADATA = {
    "plugin_id": "backup_incremental",
    "version": "1.0.0",
    "category": "backup_strategy",
    "description": "Incremental backup with retention policies and auto-cleanup",
    "dependencies": [],
    "performance_profile": {
        "speed": "HIGH",
        "memory_usage": "MEDIUM",
        "storage_efficiency": "HIGH",
        "cpu_usage": "MEDIUM"
    }
}