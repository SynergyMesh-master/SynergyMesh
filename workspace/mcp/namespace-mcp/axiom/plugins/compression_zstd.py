"""
AXIOM ZSTD Compression Plugin
High-performance compression with configurable levels and streaming support.
"""

import zstandard as zstd
import os
import hashlib
import time
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Union, BinaryIO
from dataclasses import dataclass
import io
import threading

logger = logging.getLogger(__name__)


@dataclass
class CompressionMetrics:
    """Metrics for compression operations"""
    original_size: int
    compressed_size: int
    compression_ratio: float
    compression_speed: float  # MB/s
    files_processed: int
    processing_time: float


class Plugin:
    """
    ZSTD compression plugin with streaming support and configurable levels.
    Supports compression levels 1-22 with optimized defaults.
    """
    
    def __init__(self):
        self.compressor: Optional[zstd.ZstdCompressor] = None
        self.decompressor: Optional[zstd.ZstdDecompressor] = None
        self.config: Dict[str, Any] = {}
        self.initialized = False
        self.metrics = CompressionMetrics(0, 0, 0.0, 0.0, 0, 0.0)
        self._lock = threading.Lock()
        
    def initialize(self, config: dict) -> bool:
        """
        Initialize ZSTD compressor with configuration.
        
        Args:
            config: Plugin configuration
            
        Returns:
            bool: True if initialization successful
        """
        try:
            self.config = config
            
            # Compression configuration
            compression_level = config.get('compression_level', 12)
            chunk_size = config.get('chunk_size', 4 * 1024 * 1024)  # 4MB default
            threads = config.get('threads', min(8, os.cpu_count() or 1))
            
            # Validate compression level (1-22 for ZSTD)
            if not isinstance(compression_level, int) or not (1 <= compression_level <= 22):
                logger.error(f"Invalid compression level: {compression_level}. Must be 1-22")
                return False
                
            # Initialize compressor with optimized settings
            compression_params = zstd.ZstdCompressionParameters(
                level=compression_level,
                window_log=config.get('window_log', 23),
                hash_log=config.get('hash_log', 23),
                chain_log=config.get('chain_log', 23),
                search_log=config.get('search_log', 23),
                min_match=config.get('min_match', 3),
                target_length=config.get('target_length', 16),
                strategy=zstd.STRATEGY_BTULTRA2 if compression_level >= 19 else zstd.STRATEGY_BTULTRA,
                threads=threads
            )
            
            self.compressor = zstd.ZstdCompressor(
                compression_params=compression_params,
                write_checksum=config.get('write_checksum', True),
                write_content_size=config.get('write_content_size', True),
                write_dict_id=config.get('write_dict_id', False)
            )
            
            # Initialize decompressor
            self.decompressor = zstd.ZstdDecompressor(
                max_window_size=config.get('max_window_size', 0)
            )
            
            # Streaming configuration
            self.chunk_size = chunk_size
            self.stream_buffer_size = config.get('stream_buffer_size', 1024 * 1024)  # 1MB
            
            self.initialized = True
            logger.info(f"ZSTD plugin initialized with level {compression_level}, {threads} threads")
            
            return True
            
        except Exception as e:
            logger.error(f"ZSTD plugin initialization failed: {e}")
            return False
            
    def execute(self, context: dict) -> dict:
        """
        Execute compression operation based on context.
        
        Args:
            context: Execution context with source_path, target_path, operation_mode
            
        Returns:
            dict: Execution result with metrics
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
            operation_mode = context.get('operation_mode', 'COMPRESS')
            
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
            if operation_mode == 'COMPRESS':
                result = self._compress(source_path, target_path)
            elif operation_mode == 'DECOMPRESS':
                result = self._decompress(source_path, target_path)
            elif operation_mode == 'ESTIMATE':
                result = self._estimate_compression(source_path)
            else:
                return {
                    "status": "FAILED",
                    "error": f"Unsupported operation mode: {operation_mode}",
                    "timestamp": time.time()
                }
                
            execution_time = time.time() - start_time
            
            # Update metrics
            self._update_metrics(result, execution_time)
            
            # Prepare result
            return {
                "status": "SUCCESS",
                "metrics": {
                    "execution_time": execution_time,
                    "compression_ratio": result.get('compression_ratio', 0.0),
                    "processed_files": result.get('files_processed', 0),
                    "bytes_processed": result.get('original_size', 0),
                    "compressed_bytes": result.get('compressed_size', 0),
                    "throughput": result.get('throughput', 0.0)
                },
                "artifacts": [str(target_path)] if operation_mode != 'ESTIMATE' else [],
                "timestamp": time.time()
            }
            
        except Exception as e:
            logger.error(f"ZSTD compression execution failed: {e}")
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
            "plugin_id": "compression_zstd",
            "status": "HEALTHY",
            "initialized": self.initialized,
            "compressor_available": self.compressor is not None,
            "decompressor_available": self.decompressor is not None,
            "config_valid": self._validate_config(),
            "performance_metrics": {
                "compression_level": self.config.get('compression_level', 12),
                "threads": self.config.get('threads', 1),
                "chunk_size": self.config.get('chunk_size', 0)
            }
        }
        
        # Test basic compression
        try:
            test_data = b"Hello, World! " * 1000
            compressed = self.compressor.compress(test_data)
            decompressed = self.decompressor.decompress(compressed)
            
            if decompressed == test_data:
                validation_result["test_compression"] = "PASS"
            else:
                validation_result["test_compression"] = "FAIL"
                validation_result["status"] = "DEGRADED"
        except Exception as e:
            validation_result["test_compression"] = f"FAIL: {e}"
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
                self.compressor = None
                self.decompressor = None
                self.config = {}
                self.initialized = False
                
            logger.info("ZSTD plugin teardown completed")
            return True
            
        except Exception as e:
            logger.error(f"ZSTD plugin teardown failed: {e}")
            return False
            
    def _compress(self, source: Path, target: Path) -> Dict[str, Any]:
        """Compress source to target using streaming"""
        if source.is_file():
            return self._compress_file(source, target)
        elif source.is_dir():
            return self._compress_directory(source, target)
        else:
            raise ValueError(f"Unsupported source type: {source}")
            
    def _compress_file(self, source: Path, target: Path) -> Dict[str, Any]:
        """Compress single file"""
        original_size = source.stat().st_size
        
        with open(source, 'rb') as src_file, open(target, 'wb') as dst_file:
            # Create compression context
            compression_ctx = self.compressor.compressobj()
            
            while True:
                chunk = src_file.read(self.chunk_size)
                if not chunk:
                    break
                    
                compressed_chunk = compression_ctx.compress(chunk)
                dst_file.write(compressed_chunk)
                
            # Flush remaining data
            remaining = compression_ctx.flush()
            dst_file.write(remaining)
            
        compressed_size = target.stat().st_size
        compression_ratio = compressed_size / original_size if original_size > 0 else 0
        
        return {
            "original_size": original_size,
            "compressed_size": compressed_size,
            "compression_ratio": compression_ratio,
            "files_processed": 1,
            "throughput": (original_size / (1024*1024)) / (time.time() - time.time() or 0.001)  # MB/s
        }
        
    def _compress_directory(self, source: Path, target: Path) -> Dict[str, Any]:
        """Compress directory to archive"""
        import tarfile
        
        # Create temporary tar archive
        tar_path = target.with_suffix('.tar')
        total_original_size = 0
        files_processed = 0
        
        try:
            # Create tar archive
            with tarfile.open(tar_path, 'w') as tar:
                for file_path in source.rglob('*'):
                    if file_path.is_file():
                        total_original_size += file_path.stat().st_size
                        files_processed += 1
                        tar.add(file_path, arcname=file_path.relative_to(source))
                        
            # Compress the tar archive
            result = self._compress_file(tar_path, target)
            result.update({
                "original_size": total_original_size,
                "files_processed": files_processed
            })
            
            return result
            
        finally:
            # Clean up temporary tar file
            if tar_path.exists():
                tar_path.unlink()
                
    def _decompress(self, source: Path, target: Path) -> Dict[str, Any]:
        """Decompress source to target"""
        compressed_size = source.stat().st_size
        
        with open(source, 'rb') as src_file, open(target, 'wb') as dst_file:
            # Create decompression context
            decompression_ctx = self.decompressor.decompressobj()
            
            while True:
                chunk = src_file.read(self.chunk_size)
                if not chunk:
                    break
                    
                decompressed_chunk = decompression_ctx.decompress(chunk)
                dst_file.write(decompressed_chunk)
                
            # Flush remaining data
            remaining = decompression_ctx.flush()
            dst_file.write(remaining)
            
        decompressed_size = target.stat().st_size
        compression_ratio = compressed_size / decompressed_size if decompressed_size > 0 else 0
        
        return {
            "original_size": decompressed_size,
            "compressed_size": compressed_size,
            "compression_ratio": compression_ratio,
            "files_processed": 1,
            "throughput": (compressed_size / (1024*1024)) / (time.time() - time.time() or 0.001)
        }
        
    def _estimate_compression(self, source: Path) -> Dict[str, Any]:
        """Estimate compression ratio by sampling"""
        sample_size = self.config.get('sample_size', 1024 * 1024)  # 1MB sample
        samples = []
        
        if source.is_file():
            # Sample from file
            with open(source, 'rb') as f:
                # Take samples from beginning, middle, and end
                file_size = source.stat().st_size
                positions = [0, file_size // 2, max(0, file_size - sample_size)]
                
                for pos in positions:
                    f.seek(pos)
                    sample = f.read(min(sample_size, file_size - pos))
                    if sample:
                        samples.append(sample)
        elif source.is_dir():
            # Sample from random files in directory
            files = list(source.rglob('*'))
            file_samples = min(10, len(files))
            
            for file_path in files[:file_samples]:
                if file_path.is_file():
                    with open(file_path, 'rb') as f:
                        sample = f.read(min(sample_size // file_samples, 1024 * 100))
                        if sample:
                            samples.append(sample)
                            
        if not samples:
            return {
                "original_size": 0,
                "compressed_size": 0,
                "compression_ratio": 1.0,
                "files_processed": 0,
                "throughput": 0.0
            }
            
        # Compress samples
        original_sample_size = sum(len(s) for s in samples)
        compressed_samples = self.compressor.compress(b''.join(samples))
        compressed_sample_size = len(compressed_samples)
        
        estimated_ratio = compressed_sample_size / original_sample_size
        
        # Estimate total sizes
        if source.is_file():
            total_original = source.stat().st_size
            files_processed = 1
        else:
            total_original = sum(f.stat().st_size for f in source.rglob('*') if f.is_file())
            files_processed = len([f for f in source.rglob('*') if f.is_file()])
            
        estimated_compressed = int(total_original * estimated_ratio)
        
        return {
            "original_size": total_original,
            "compressed_size": estimated_compressed,
            "compression_ratio": estimated_ratio,
            "files_processed": files_processed,
            "throughput": 0.0  # Not applicable for estimation
        }
        
    def _validate_config(self) -> bool:
        """Validate plugin configuration"""
        required_fields = ['compression_level', 'chunk_size']
        
        for field in required_fields:
            if field not in self.config:
                return False
                
        compression_level = self.config['compression_level']
        if not isinstance(compression_level, int) or not (1 <= compression_level <= 22):
            return False
            
        chunk_size = self.config['chunk_size']
        if not isinstance(chunk_size, int) or chunk_size <= 0:
            return False
            
        return True
        
    def _update_metrics(self, result: Dict[str, Any], execution_time: float) -> None:
        """Update internal metrics"""
        with self._lock:
            self.metrics.original_size += result.get('original_size', 0)
            self.metrics.compressed_size += result.get('compressed_size', 0)
            self.metrics.files_processed += result.get('files_processed', 0)
            self.metrics.processing_time += execution_time
            
            if self.metrics.original_size > 0:
                self.metrics.compression_ratio = self.metrics.compressed_size / self.metrics.original_size
                
            if self.metrics.processing_time > 0:
                self.metrics.compression_speed = (self.metrics.original_size / (1024*1024)) / self.metrics.processing_time
                
    def get_metrics(self) -> Dict[str, Any]:
        """Get current compression metrics"""
        with self._lock:
            return {
                "total_original_size": self.metrics.original_size,
                "total_compressed_size": self.metrics.compressed_size,
                "average_compression_ratio": self.metrics.compression_ratio,
                "compression_speed_mbps": self.metrics.compression_speed,
                "total_files_processed": self.metrics.files_processed,
                "total_processing_time": self.metrics.processing_time
            }


# Plugin metadata for registration
PLUGIN_METADATA = {
    "plugin_id": "compression_zstd",
    "version": "1.0.0",
    "category": "compression",
    "description": "ZSTD compression with streaming and configurable levels",
    "dependencies": [],
    "performance_profile": {
        "compression_ratio": "HIGH",
        "speed": "HIGH",
        "memory_usage": "MEDIUM",
        "cpu_usage": "MEDIUM_TO_HIGH"
    }
}