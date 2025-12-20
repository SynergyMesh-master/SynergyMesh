"""
MachineNativeOps Security Framework
安全框架 - 認證、授權、加密
"""

import hashlib
import logging
import os
import secrets
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Optional

logger = logging.getLogger(__name__)

# 密碼哈希安全參數
PBKDF2_SALT_LENGTH = 32  # bytes
PBKDF2_ITERATIONS = 100000  # OWASP recommended minimum
DEFAULT_PASSWORD_LENGTH = 24  # characters for token_urlsafe

class Permission(Enum):
    """權限枚舉"""
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    EXECUTE = "execute"
    ADMIN = "admin"

@dataclass
class User:
    """用戶定義"""
    id: str
    username: str
    email: str
    created_at: datetime
    is_active: bool = True
    password_hash: str = ""

class SecurityManager:
    """安全管理器主類"""
    
    def __init__(self):
        self.users: dict[str, User] = {}
        self.is_initialized = False
        self.security_events: list = []
    
    @staticmethod
    def _hash_password(password: str) -> str:
        """使用 PBKDF2 對密碼進行哈希處理"""
        salt = secrets.token_bytes(PBKDF2_SALT_LENGTH)
        pwdhash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, PBKDF2_ITERATIONS)
        return salt.hex() + ':' + pwdhash.hex()
    
    @staticmethod
    def _verify_password(stored_password: str, provided_password: str) -> bool:
        """驗證密碼"""
        try:
            salt_hex, pwdhash_hex = stored_password.split(':')
            salt = bytes.fromhex(salt_hex)
            stored_hash = bytes.fromhex(pwdhash_hex)
            pwdhash = hashlib.pbkdf2_hmac('sha256', provided_password.encode('utf-8'), salt, PBKDF2_ITERATIONS)
            return pwdhash == stored_hash
        except (ValueError, AttributeError):
            return False
    
    async def initialize(self):
        """初始化安全管理器"""
        if self.is_initialized:
            return
        
        logger.info("🔒 初始化安全管理器")
        
        # 創建默認管理員用戶
        await self._create_default_admin()
        
        self.is_initialized = True
        logger.info("✅ 安全管理器初始化完成")
    
    async def authenticate_user(self, username: str, password: str) -> Optional[str]:
        """認證用戶"""
        user = None
        for u in self.users.values():
            if u.username == username and u.is_active:
                user = u
                break
        
        if not user:
            logger.warning(f"⚠️ 用戶不存在: {username}")
            return None
        
        # 驗證密碼哈希格式並進行驗證
        if user.password_hash and ':' in user.password_hash and self._verify_password(user.password_hash, password):
            token = f"token_{secrets.token_hex(16)}"
            await self._log_security_event("user_authenticated", {
                "username": username,
                "token": token[:10]
            })
            return token
        
        logger.warning(f"⚠️ 密碼驗證失敗: {username}")
        return None
    
    async def _create_default_admin(self):
        """創建默認管理員"""
        if not self.users:
            # 優先從環境變量讀取密碼，否則生成隨機密碼
            default_password = os.environ.get('ADMIN_DEFAULT_PASSWORD')
            password_from_env = default_password is not None
            
            if not default_password:
                default_password = secrets.token_urlsafe(DEFAULT_PASSWORD_LENGTH)
            
            admin_user = User(
                id="admin_001",
                username="admin",
                email="admin@mynativeops.ai",
                created_at=datetime.now(),
                password_hash=self._hash_password(default_password)
            )
            self.users[admin_user.id] = admin_user
            logger.info("👑 創建默認管理員用戶")
            
            if password_from_env:
                logger.info("✅ 使用環境變量 ADMIN_DEFAULT_PASSWORD 設置的管理員密碼")
            else:
                # 將密碼輸出到標準輸出供部署者記錄（僅在首次創建時）
                print(f"\n{'='*60}")
                print(f"🔐 默認管理員密碼已生成")
                print(f"用戶名: admin")
                print(f"密碼: {default_password}")
                print(f"⚠️  請立即保存此密碼並在首次登入後修改！")
                print(f"{'='*60}\n")
                
                logger.warning("⚠️ 默認管理員密碼已生成並輸出到控制台，請妥善保管並立即修改")
                # 記錄密碼生成事件但不包含密碼本身
                await self._log_security_event("admin_password_generated", {
                    "username": "admin",
                    "timestamp": datetime.now().isoformat(),
                    "source": "environment_variable" if password_from_env else "auto_generated",
                    "warning": "請立即修改此密碼"
                })
    
    async def _log_security_event(self, event_type: str, details: dict[str, Any]):
        """記錄安全事件"""
        event = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "details": details
        }
        
        self.security_events.append(event)
        logger.info(f"🛡️ 安全事件: {event_type}")

# 全局安全管理器實例
security_manager = SecurityManager()