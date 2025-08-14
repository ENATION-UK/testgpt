import os
import json
import platform
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime


class ConfigManager:
    """配置管理器，统一管理配置文件的存储位置"""
    
    def __init__(self, app_name: str = "autotest"):
        self.app_name = app_name
        self.config_dir = self.get_config_directory()
        self.data_dir = self.get_data_directory()
        self.ensure_config_directory()
        self.ensure_data_directory()
    
    def get_config_directory(self) -> Path:
        """获取配置目录路径"""
        system = platform.system().lower()
        
        if system == "darwin":  # macOS
            config_dir = Path.home() / "Library" / "Application Support" / self.app_name
        elif system == "linux":
            config_dir = Path.home() / ".config" / self.app_name
        elif system == "windows":
            config_dir = Path(os.environ.get("APPDATA", "")) / self.app_name
        else:
            # 默认使用用户主目录
            config_dir = Path.home() / f".{self.app_name}"
        
        return config_dir
    
    def get_data_directory(self) -> Path:
        """获取数据目录路径"""
        # 优先使用环境变量配置的数据目录（Docker环境）
        if os.getenv("DATA_DIR"):
            data_dir = Path(os.getenv("DATA_DIR"))
        elif os.getenv("DOCKER_ENV"):
            # Docker环境默认使用/app/data
            data_dir = Path("/app/data")
        else:
            # 本地环境使用配置目录下的data子目录
            data_dir = self.config_dir / "data"
        
        return data_dir
    
    def ensure_config_directory(self):
        """确保配置目录存在"""
        self.config_dir.mkdir(parents=True, exist_ok=True)
    
    def ensure_data_directory(self):
        """确保数据目录存在"""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        # 在Docker环境中，确保目录可写
        if os.getenv("DOCKER_ENV"):
            try:
                # 尝试设置目录权限为755
                self.data_dir.chmod(0o755)
            except Exception:
                pass  # 忽略权限设置错误
    
    def get_model_config_path(self) -> Path:
        """获取模型配置文件路径"""
        return self.config_dir / "model_config.json"
    
    def get_prompt_config_path(self) -> Path:
        """获取提示词配置文件路径"""
        return self.config_dir / "prompt_config.json"
    
    def get_history_directory(self) -> Path:
        """获取 history 缓存目录路径"""
        history_dir = self.data_dir / "history"
        history_dir.mkdir(parents=True, exist_ok=True)
        return history_dir
    
    def get_database_directory(self) -> Path:
        """获取数据库目录路径"""
        return self.data_dir
    
    def get_screenshots_directory(self) -> Path:
        """获取截图目录路径"""
        screenshots_dir = self.data_dir / "screenshots"
        screenshots_dir.mkdir(parents=True, exist_ok=True)
        return screenshots_dir
    
    def get_test_history_cache_directory(self) -> Path:
        """获取测试历史缓存目录路径"""
        cache_dir = self.data_dir / "test_history_cache"
        cache_dir.mkdir(parents=True, exist_ok=True)
        return cache_dir
