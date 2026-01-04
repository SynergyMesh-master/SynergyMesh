"""
MachineNativeOps Auto-Monitor - 儲存管理 (Storage Management)

管理指標數據的持久化儲存。
Manages persistent storage of metric data.
Storage Module (儲存模組)
數據儲存模組

Handles metric and alert data storage.
處理指標和告警數據的儲存。
"""

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import logging
import json
import sqlite3
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass


@dataclass
class MetricRecord:
    """表示一條指標記錄 / Represents a metric record."""
    name: str
    value: float
    timestamp: datetime
    labels: Dict[str, str]
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典 / Convert to dictionary."""
        return {
            'name': self.name,
            'value': self.value,
            'timestamp': self.timestamp.isoformat(),
            'labels': self.labels
        }


class TimeSeriesStorage:
    """
    時間序列指標儲存 / Time-series metrics storage.
    使用 SQLite 作為後端 / Uses SQLite as backend.
    """
    
    def __init__(self, db_path: str):
        """
        初始化時間序列儲存 / Initialize time-series storage.
        
        Args:
            db_path: 數據庫文件路徑 / Database file path
        """
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        self.connection: Optional[sqlite3.Connection] = None
        
        self._initialize_database()
    
    def _initialize_database(self):
        """初始化數據庫架構 / Initialize database schema."""
        try:
            # 確保目錄存在 / Ensure directory exists
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
            
            # 連接數據庫 / Connect to database
            self.connection = sqlite3.connect(self.db_path)
            cursor = self.connection.cursor()
            
            # 創建指標表 / Create metrics table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    value REAL NOT NULL,
                    timestamp DATETIME NOT NULL,
                    labels TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 創建索引以提高查詢效能 / Create indexes for query performance
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_metrics_name 
                ON metrics(name)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_metrics_timestamp 
                ON metrics(timestamp)
            """)
            
            self.connection.commit()
            self.logger.info(f"Database initialized at: {self.db_path}")
        
        except Exception as e:
            self.logger.error(f"Error initializing database: {e}")
            raise
    
    def store_metric(self, name: str, value: float, 
                    timestamp: Optional[datetime] = None,
                    labels: Optional[Dict[str, str]] = None):
        """
        儲存單個指標 / Store a single metric.
        
        Args:
            name: 指標名稱 / Metric name
            value: 指標值 / Metric value
            timestamp: 時間戳（可選）/ Timestamp (optional)
            labels: 標籤（可選）/ Labels (optional)
        """
        if timestamp is None:
            timestamp = datetime.now()
        
        if labels is None:
            labels = {}
        
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                """
                INSERT INTO metrics (name, value, timestamp, labels)
                VALUES (?, ?, ?, ?)
                """,
                (name, value, timestamp, json.dumps(labels))
            )
            self.connection.commit()
        
        except Exception as e:
            self.logger.error(f"Error storing metric {name}: {e}")
    
    def store_metrics(self, metrics: Dict[str, float],
                     timestamp: Optional[datetime] = None):
        """
        批量儲存指標 / Store multiple metrics in batch.
        
        Args:
            metrics: 指標字典（名稱 -> 值）/ Metrics dictionary (name -> value)
            timestamp: 時間戳（可選）/ Timestamp (optional)
        """
        if timestamp is None:
            timestamp = datetime.now()
        
        try:
            cursor = self.connection.cursor()
            
            # 準備批量插入數據 / Prepare batch insert data
            data = [
                (name, value, timestamp, json.dumps({}))
                for name, value in metrics.items()
            ]
            
            cursor.executemany(
                """
                INSERT INTO metrics (name, value, timestamp, labels)
                VALUES (?, ?, ?, ?)
                """,
                data
            )
            
            self.connection.commit()
            self.logger.debug(f"Stored {len(metrics)} metrics")
        
        except Exception as e:
            self.logger.error(f"Error storing metrics batch: {e}")
    
    def query_metrics(self, name: str,
                     start_time: Optional[datetime] = None,
                     end_time: Optional[datetime] = None,
                     limit: int = 1000) -> List[MetricRecord]:
        """
        查詢指標數據 / Query metric data.
        
        Args:
            name: 指標名稱 / Metric name
            start_time: 開始時間（可選）/ Start time (optional)
            end_time: 結束時間（可選）/ End time (optional)
            limit: 最大返回數量 / Maximum number of results
            
        Returns:
            指標記錄列表 / List of metric records
        """
        try:
            cursor = self.connection.cursor()
            
            query = "SELECT name, value, timestamp, labels FROM metrics WHERE name = ?"
            params = [name]
            
            if start_time:
                query += " AND timestamp >= ?"
                params.append(start_time)
            
            if end_time:
                query += " AND timestamp <= ?"
                params.append(end_time)
            
            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            # 轉換為 MetricRecord 物件 / Convert to MetricRecord objects
            records = []
            for row in rows:
                records.append(MetricRecord(
                    name=row[0],
                    value=row[1],
                    timestamp=datetime.fromisoformat(row[2]),
                    labels=json.loads(row[3]) if row[3] else {}
                ))
            
            return records
        
        except Exception as e:
            self.logger.error(f"Error querying metrics: {e}")
            return []
    
    def cleanup_old_data(self, retention_days: int = 30):
        """
        清理過期數據 / Clean up old data.
        
        Args:
            retention_days: 保留天數 / Number of days to retain
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=retention_days)
            
            cursor = self.connection.cursor()
            cursor.execute(
                "DELETE FROM metrics WHERE timestamp < ?",
                (cutoff_date,)
            )
            
            deleted_count = cursor.rowcount
            self.connection.commit()
            
            self.logger.info(f"Cleaned up {deleted_count} old metric records")
        
        except Exception as e:
            self.logger.error(f"Error cleaning up old data: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        獲取儲存統計信息 / Get storage statistics.
        
        Returns:
            統計信息字典 / Statistics dictionary
        """
        try:
            cursor = self.connection.cursor()
            
            # 總記錄數 / Total records
            cursor.execute("SELECT COUNT(*) FROM metrics")
            total_records = cursor.fetchone()[0]
            
            # 不同指標數量 / Distinct metrics count
            cursor.execute("SELECT COUNT(DISTINCT name) FROM metrics")
            distinct_metrics = cursor.fetchone()[0]
            
            # 最舊和最新的記錄時間 / Oldest and newest record times
            cursor.execute("SELECT MIN(timestamp), MAX(timestamp) FROM metrics")
            oldest, newest = cursor.fetchone()
            
            return {
                'total_records': total_records,
                'distinct_metrics': distinct_metrics,
                'oldest_record': oldest,
                'newest_record': newest,
                'db_path': self.db_path
            }
        
        except Exception as e:
            self.logger.error(f"Error getting storage stats: {e}")
            return {}
    
    def close(self):
        """關閉數據庫連接 / Close database connection."""
        if self.connection:
            self.connection.close()
            self.logger.info("Database connection closed")


class StorageManager:
    """
    儲存管理器 / Storage manager.
    統一管理不同類型的儲存後端 / Manages different storage backends.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化儲存管理器 / Initialize storage manager.
        
        Args:
            config: 儲存配置 / Storage configuration
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.enabled = config.get('enabled', True)
        
        # 初始化儲存後端 / Initialize storage backend
        backend_type = config.get('backend', 'timeseries')
        
        if backend_type == 'timeseries':
            db_path = config.get('path', '/var/lib/machinenativeops/metrics/metrics.db')
            self.backend = TimeSeriesStorage(db_path)
        else:
            raise ValueError(f"Unsupported storage backend: {backend_type}")
        
        # 設置數據保留策略 / Set data retention policy
        self.retention_days = config.get('retention_days', 30)
    
    def store_metrics(self, metrics: Dict[str, float]):
        """
        儲存指標 / Store metrics.
        
        Args:
            metrics: 指標字典 / Metrics dictionary
        """
        if not self.enabled:
            return
        
        try:
            self.backend.store_metrics(metrics)
        except Exception as e:
            self.logger.error(f"Error storing metrics: {e}")
    
    def query_metrics(self, name: str, **kwargs) -> List[MetricRecord]:
        """
        查詢指標 / Query metrics.
        
        Args:
            name: 指標名稱 / Metric name
            **kwargs: 其他查詢參數 / Additional query parameters
            
        Returns:
            指標記錄列表 / List of metric records
        """
        return self.backend.query_metrics(name, **kwargs)
    
    def cleanup(self):
        """執行數據清理 / Perform data cleanup."""
        if not self.enabled:
            return
        
        self.backend.cleanup_old_data(self.retention_days)
    
    def get_stats(self) -> Dict[str, Any]:
        """
        獲取儲存統計信息 / Get storage statistics.
        
        Returns:
            統計信息字典 / Statistics dictionary
        """
        if not self.enabled:
            return {'enabled': False}
        
        stats = self.backend.get_stats()
        stats['enabled'] = True
        stats['retention_days'] = self.retention_days
        return stats
    
    def close(self):
        """關閉儲存管理器 / Close storage manager."""
        if self.enabled and self.backend:
            self.backend.close()
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from abc import ABC, abstractmethod
from collections import deque

logger = logging.getLogger(__name__)


class MetricStorage:
    """Base class for metric storage"""
    
    def store_metric(self, metric_name: str, value: Any, timestamp: datetime = None):
        """Store a metric value"""
        raise NotImplementedError
    
    def retrieve_metrics(
        self,
        metric_name: str,
        start_time: datetime = None,
        end_time: datetime = None
    ) -> List[Dict[str, Any]]:
        """Retrieve metric values"""
        raise NotImplementedError
    
    def delete_old_metrics(self, older_than: datetime):
        """Delete metrics older than specified time"""
        raise NotImplementedError


class MemoryStorage(MetricStorage):
    """In-memory metric storage (for development/testing)"""
    
    def __init__(self, max_size: int = 10000):
        """Initialize memory storage"""
        self.metrics: Dict[str, List[Dict[str, Any]]] = {}
        self.max_size = max_size
    
    def store_metric(self, metric_name: str, value: Any, timestamp: datetime = None):
        """Store a metric value in memory"""
        if timestamp is None:
            timestamp = datetime.utcnow()
        
        if metric_name not in self.metrics:
            self.metrics[metric_name] = []
        
        self.metrics[metric_name].append({
            "value": value,
            "timestamp": timestamp.isoformat()
        })
        
        # Trim if exceeds max size
        if len(self.metrics[metric_name]) > self.max_size:
            self.metrics[metric_name] = self.metrics[metric_name][-self.max_size:]
        
        logger.debug(f"Stored metric {metric_name} = {value}")
    
    def retrieve_metrics(
        self,
        metric_name: str,
        start_time: datetime = None,
        end_time: datetime = None
    ) -> List[Dict[str, Any]]:
        """Retrieve metric values from memory"""
        if metric_name not in self.metrics:
            return []
        
        metrics = self.metrics[metric_name]
        
        if start_time or end_time:
            filtered_metrics = []
            for metric in metrics:
                metric_time = datetime.fromisoformat(metric["timestamp"])
                
                if start_time and metric_time < start_time:
                    continue
                if end_time and metric_time > end_time:
                    continue
                
                filtered_metrics.append(metric)
            
            return filtered_metrics
        
        return metrics.copy()
    
    def delete_old_metrics(self, older_than: datetime):
        """Delete metrics older than specified time"""
        deleted_count = 0
        
        for metric_name in list(self.metrics.keys()):
            original_count = len(self.metrics[metric_name])
            
            self.metrics[metric_name] = [
                m for m in self.metrics[metric_name]
                if datetime.fromisoformat(m["timestamp"]) >= older_than
            ]
            
            deleted = original_count - len(self.metrics[metric_name])
            deleted_count += deleted
            
            # Remove empty metric lists
            if not self.metrics[metric_name]:
                del self.metrics[metric_name]
        
        logger.info(f"Deleted {deleted_count} old metrics")
        return deleted_count


class FileStorage(MetricStorage):
    """File-based metric storage"""
    
    def __init__(self, storage_dir: Path = Path("/var/lib/machinenativeops/metrics")):
        """Initialize file storage"""
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Initialized file storage at {self.storage_dir}")
    
    def _get_metric_file(self, metric_name: str, date: datetime = None) -> Path:
        """Get file path for a metric"""
        if date is None:
            date = datetime.utcnow()
        
        # Store metrics by date (one file per metric per day)
        date_str = date.strftime("%Y-%m-%d")
        return self.storage_dir / f"{metric_name}_{date_str}.json"
    
    def store_metric(self, metric_name: str, value: Any, timestamp: datetime = None):
        """Store a metric value to file"""
        if timestamp is None:
            timestamp = datetime.utcnow()
        
        metric_file = self._get_metric_file(metric_name, timestamp)
        
        try:
            # Load existing metrics
            if metric_file.exists():
                with open(metric_file, 'r') as f:
                    metrics = json.load(f)
            else:
                metrics = []
            
            # Append new metric
            metrics.append({
                "value": value,
                "timestamp": timestamp.isoformat()
            })
            
            # Save back to file
            with open(metric_file, 'w') as f:
                json.dump(metrics, f, indent=2)
            
            logger.debug(f"Stored metric {metric_name} to {metric_file}")
        
        except Exception as e:
            logger.error(f"Error storing metric to file: {e}")
    
    def retrieve_metrics(
        self,
        metric_name: str,
        start_time: datetime = None,
        end_time: datetime = None
    ) -> List[Dict[str, Any]]:
        """Retrieve metric values from files"""
        all_metrics = []
        
        # Determine date range
        if start_time is None:
            start_time = datetime.utcnow() - timedelta(days=7)
        if end_time is None:
            end_time = datetime.utcnow()
        
        # Read metrics from each day in range
        current_date = start_time.date()
        end_date = end_time.date()
        
        while current_date <= end_date:
            metric_file = self._get_metric_file(
                metric_name,
                datetime.combine(current_date, datetime.min.time())
            )
            
            if metric_file.exists():
                try:
                    with open(metric_file, 'r') as f:
                        daily_metrics = json.load(f)
                    
                    # Filter by time range
                    for metric in daily_metrics:
                        metric_time = datetime.fromisoformat(metric["timestamp"])
                        
                        if start_time <= metric_time <= end_time:
                            all_metrics.append(metric)
                
                except Exception as e:
                    logger.error(f"Error reading metric file {metric_file}: {e}")
            
            current_date += timedelta(days=1)
        
        return all_metrics
    
    def delete_old_metrics(self, older_than: datetime):
        """Delete metric files older than specified time"""
        deleted_count = 0
        cutoff_date = older_than.date()
        
        for metric_file in self.storage_dir.glob("*.json"):
            try:
                # Extract date from filename
                # Format: metric_name_YYYY-MM-DD.json
                date_str = metric_file.stem.split('_')[-1]
                file_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                
                if file_date < cutoff_date:
                    metric_file.unlink()
                    deleted_count += 1
                    logger.debug(f"Deleted old metric file: {metric_file}")
            
            except Exception as e:
                logger.error(f"Error deleting metric file {metric_file}: {e}")
        
        logger.info(f"Deleted {deleted_count} old metric files")
        return deleted_count


def create_storage(storage_type: str = "memory", **kwargs) -> MetricStorage:
    """
    Factory function to create storage instance
    
    Args:
        storage_type: Type of storage ('memory' or 'file')
        **kwargs: Additional arguments for storage initialization
    
    Returns:
        MetricStorage instance
    """
    if storage_type == "memory":
        return MemoryStorage(**kwargs)
    elif storage_type == "file":
        return FileStorage(**kwargs)
    else:
        logger.warning(f"Unknown storage type: {storage_type}, using memory")
        return MemoryStorage()
class StorageBackend(ABC):
    """Abstract base class for storage backends."""
    
    @abstractmethod
    def store_metrics(self, metrics: Dict):
        """Store metrics data."""
        pass
    
    @abstractmethod
    def store_logs(self, logs: List):
        """Store log entries."""
        pass
    
    @abstractmethod
    def store_events(self, events: List):
        """Store events."""
        pass
    
    @abstractmethod
    def store_alert(self, alert):
        """Store an alert."""
        pass
    
    @abstractmethod
    def get_metrics(self, start_time: Optional[datetime] = None, 
                    end_time: Optional[datetime] = None) -> List[Dict]:
        """Retrieve metrics within time range."""
        pass
    
    @abstractmethod
    def get_metrics_count(self) -> int:
        """Get total count of stored metrics."""
        pass
    
    @abstractmethod
    def get_logs_count(self) -> int:
        """Get total count of stored logs."""
        pass
    
    @abstractmethod
    def get_events_count(self) -> int:
        """Get total count of stored events."""
        pass


class InMemoryStorage(StorageBackend):
    """In-memory storage backend using deque for efficiency."""
    
    def __init__(self, max_items: int = 10000):
        self.max_items = max_items
        self.metrics = deque(maxlen=max_items)
        self.logs = deque(maxlen=max_items)
        self.events = deque(maxlen=max_items)
        self.alerts = deque(maxlen=max_items)
        logger.info(f"✅ Initialized InMemoryStorage (max_items={max_items})")
    
    def store_metrics(self, metrics: Dict):
        """Store metrics in memory."""
        metrics['_stored_at'] = datetime.now().isoformat()
        self.metrics.append(metrics)
    
    def store_logs(self, logs: List):
        """Store logs in memory."""
        for log in logs:
            if hasattr(log, 'to_dict'):
                log_dict = log.to_dict()
            else:
                log_dict = log
            log_dict['_stored_at'] = datetime.now().isoformat()
            self.logs.append(log_dict)
    
    def store_events(self, events: List):
        """Store events in memory."""
        for event in events:
            if hasattr(event, 'to_dict'):
                event_dict = event.to_dict()
            else:
                event_dict = event
            event_dict['_stored_at'] = datetime.now().isoformat()
            self.events.append(event_dict)
    
    def store_alert(self, alert):
        """Store alert in memory."""
        if hasattr(alert, 'to_dict'):
            alert_dict = alert.to_dict()
        else:
            alert_dict = alert
        alert_dict['_stored_at'] = datetime.now().isoformat()
        self.alerts.append(alert_dict)
    
    def get_metrics(self, start_time: Optional[datetime] = None, 
                    end_time: Optional[datetime] = None) -> List[Dict]:
        """Retrieve metrics within time range."""
        if start_time is None and end_time is None:
            return list(self.metrics)
        
        filtered = []
        for metric in self.metrics:
            timestamp = datetime.fromisoformat(metric.get('timestamp', ''))
            if start_time and timestamp < start_time:
                continue
            if end_time and timestamp > end_time:
                continue
            filtered.append(metric)
        
        return filtered
    
    def get_metrics_count(self) -> int:
        """Get total count of stored metrics."""
        return len(self.metrics)
    
    def get_logs_count(self) -> int:
        """Get total count of stored logs."""
        return len(self.logs)
    
    def get_events_count(self) -> int:
        """Get total count of stored events."""
        return len(self.events)
    
    def get_alerts_count(self) -> int:
        """Get total count of stored alerts."""
        return len(self.alerts)


class FileStorage(StorageBackend):
    """File-based storage backend using JSON files."""
    
    def __init__(self, storage_path: Path, retention_days: int = 7):
        self.storage_path = Path(storage_path)
        self.retention_days = retention_days
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories
        (self.storage_path / 'metrics').mkdir(exist_ok=True)
        (self.storage_path / 'logs').mkdir(exist_ok=True)
        (self.storage_path / 'events').mkdir(exist_ok=True)
        (self.storage_path / 'alerts').mkdir(exist_ok=True)
        
        logger.info(f"✅ Initialized FileStorage at {self.storage_path}")
    
    def _get_daily_file(self, data_type: str, date: datetime = None) -> Path:
        """Get file path for a specific date."""
        if date is None:
            date = datetime.now()
        filename = f"{date.strftime('%Y-%m-%d')}.jsonl"
        return self.storage_path / data_type / filename
    
    def _append_to_file(self, file_path: Path, data: Dict):
        """Append data to JSONL file."""
        try:
            with open(file_path, 'a', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False)
                f.write('\n')
        except Exception as e:
            logger.error(f"Error writing to file {file_path}: {e}")
    
    def store_metrics(self, metrics: Dict):
        """Store metrics to file."""
        metrics['_stored_at'] = datetime.now().isoformat()
        file_path = self._get_daily_file('metrics')
        self._append_to_file(file_path, metrics)
    
    def store_logs(self, logs: List):
        """Store logs to file."""
        file_path = self._get_daily_file('logs')
        for log in logs:
            if hasattr(log, 'to_dict'):
                log_dict = log.to_dict()
            else:
                log_dict = log
            log_dict['_stored_at'] = datetime.now().isoformat()
            self._append_to_file(file_path, log_dict)
    
    def store_events(self, events: List):
        """Store events to file."""
        file_path = self._get_daily_file('events')
        for event in events:
            if hasattr(event, 'to_dict'):
                event_dict = event.to_dict()
            else:
                event_dict = event
            event_dict['_stored_at'] = datetime.now().isoformat()
            self._append_to_file(file_path, event_dict)
    
    def store_alert(self, alert):
        """Store alert to file."""
        if hasattr(alert, 'to_dict'):
            alert_dict = alert.to_dict()
        else:
            alert_dict = alert
        alert_dict['_stored_at'] = datetime.now().isoformat()
        file_path = self._get_daily_file('alerts')
        self._append_to_file(file_path, alert_dict)
    
    def get_metrics(self, start_time: Optional[datetime] = None, 
                    end_time: Optional[datetime] = None) -> List[Dict]:
        """Retrieve metrics from files."""
        # Simplified implementation - read from today's file
        file_path = self._get_daily_file('metrics')
        if not file_path.exists():
            return []
        
        metrics = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    metrics.append(json.loads(line))
        except Exception as e:
            logger.error(f"Error reading metrics: {e}")
        
        return metrics
    
    def get_metrics_count(self) -> int:
        """Get approximate count of stored metrics."""
        return len(self.get_metrics())
    
    def get_logs_count(self) -> int:
        """Get approximate count of stored logs."""
        file_path = self._get_daily_file('logs')
        if not file_path.exists():
            return 0
        return sum(1 for _ in open(file_path, 'r', encoding='utf-8'))
    
    def get_events_count(self) -> int:
        """Get approximate count of stored events."""
        file_path = self._get_daily_file('events')
        if not file_path.exists():
            return 0
        return sum(1 for _ in open(file_path, 'r', encoding='utf-8'))
    
    def cleanup_old_files(self):
        """Remove files older than retention period."""
        cutoff_date = datetime.now() - timedelta(days=self.retention_days)
        
        for data_type in ['metrics', 'logs', 'events', 'alerts']:
            data_dir = self.storage_path / data_type
            for file_path in data_dir.glob('*.jsonl'):
                try:
                    # Extract date from filename
                    date_str = file_path.stem
                    file_date = datetime.strptime(date_str, '%Y-%m-%d')
                    
                    if file_date < cutoff_date:
                        file_path.unlink()
                        logger.info(f"🗑️  Removed old file: {file_path}")
                except Exception as e:
                    logger.error(f"Error cleaning up {file_path}: {e}")
