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
        self.ensure_config_directory()
    
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
    
    def ensure_config_directory(self):
        """确保配置目录存在"""
        self.config_dir.mkdir(parents=True, exist_ok=True)
    
    def get_model_config_path(self) -> Path:
        """获取模型配置文件路径"""
        return self.config_dir / "model_config.json"
    
    def get_prompt_config_path(self) -> Path:
        """获取提示词配置文件路径"""
        return self.config_dir / "prompt_config.json"
    
    def get_history_directory(self) -> Path:
        """获取 history 缓存目录路径"""
        history_dir = self.config_dir / "history"
        history_dir.mkdir(parents=True, exist_ok=True)
        return history_dir
