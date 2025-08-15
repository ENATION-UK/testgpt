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
        self.data_dir = self.get_data_directory()
        self.ensure_data_directory()
        self.ensure_data_subdirectories()
    
    def is_docker_environment(self) -> bool:
        """检测是否为Docker环境"""
        # 检查多个Docker环境标识
        docker_indicators = [
            os.getenv("DOCKER_ENV"),
            os.getenv("KUBERNETES_SERVICE_HOST"),
            os.path.exists("/.dockerenv"),
            os.path.exists("/proc/1/cgroup") and "docker" in open("/proc/1/cgroup").read()
        ]
        return any(indicator for indicator in docker_indicators)
    
    def get_config_directory(self) -> Path:
        """获取配置目录路径（本地环境使用）"""
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
        if self.is_docker_environment():
            # Docker环境使用/app/data
            data_dir = Path("/app/data")
        else:
            # 本地环境使用配置目录下的data子目录
            data_dir = self.get_config_directory() / "data"
        
        return data_dir
    
    def ensure_data_directory(self):
        """确保数据目录存在"""
        try:
            self.data_dir.mkdir(parents=True, exist_ok=True)
            
            # 在Docker环境中，确保目录可写
            if self.is_docker_environment():
                try:
                    # 尝试设置目录权限为755
                    self.data_dir.chmod(0o755)
                except Exception:
                    pass  # 忽略权限设置错误
        except (OSError, PermissionError) as e:
            # 如果无法创建目录（比如权限问题），记录错误但不中断程序
            print(f"警告: 无法创建数据目录 {self.data_dir}: {e}")
            # 尝试使用备用目录
            if self.is_docker_environment():
                # Docker环境下使用当前工作目录
                self.data_dir = Path.cwd() / "data"
                self.data_dir.mkdir(parents=True, exist_ok=True)
            else:
                # 本地环境下使用临时目录
                import tempfile
                self.data_dir = Path(tempfile.gettempdir()) / f"{self.app_name}_data"
                self.data_dir.mkdir(parents=True, exist_ok=True)
    
    def ensure_data_subdirectories(self):
        """确保数据子目录存在"""
        # 创建history缓存目录
        self.get_history_directory()
        
        # 创建screenshots目录
        self.get_screenshots_directory()
        
        # 创建test_history_cache目录
        self.get_test_history_cache_directory()
    
    def get_database_path(self) -> Path:
        """获取数据库文件路径"""
        return self.data_dir / "autotest.db"
    
    def get_multi_model_config_path(self) -> Path:
        """获取多模型配置文件路径"""
        return self.data_dir / "multi_model_config.json"
    
    def get_prompt_config_path(self) -> Path:
        """获取提示词配置文件路径"""
        return self.data_dir / "prompt_config.json"
    
    def get_history_directory(self) -> Path:
        """获取history缓存目录路径"""
        history_dir = self.data_dir / "history"
        history_dir.mkdir(parents=True, exist_ok=True)
        return history_dir
    
    def get_screenshots_directory(self) -> Path:
        """获取截图目录路径"""
        screenshots_dir = self.data_dir / "test_screenshots"
        screenshots_dir.mkdir(parents=True, exist_ok=True)
        return screenshots_dir
    
    def get_test_history_cache_directory(self) -> Path:
        """获取测试历史缓存目录路径"""
        cache_dir = self.data_dir / "test_history_cache"
        cache_dir.mkdir(parents=True, exist_ok=True)
        return cache_dir
    
    def get_directory_structure_info(self) -> Dict[str, str]:
        """获取目录结构信息"""
        return {
            "data_directory": str(self.data_dir),
            "database_file": str(self.get_database_path()),
            "multi_model_config": str(self.get_multi_model_config_path()),
            "prompt_config": str(self.get_prompt_config_path()),
            "history_directory": str(self.get_history_directory()),
            "screenshots_directory": str(self.get_screenshots_directory()),
            "test_history_cache": str(self.get_test_history_cache_directory()),
            "is_docker": str(self.is_docker_environment())
        }
    
    def print_directory_structure(self):
        """打印目录结构信息"""
        info = self.get_directory_structure_info()
        print(f"配置管理器目录结构:")
        print(f"数据目录: {info['data_directory']}")
        print(f"数据库文件: {info['database_file']}")
        print(f"多模型配置: {info['multi_model_config']}")
        print(f"提示词配置: {info['prompt_config']}")
        print(f"历史缓存目录: {info['history_directory']}")
        print(f"截图目录: {info['screenshots_directory']}")
        print(f"测试历史缓存: {info['test_history_cache']}")
        print(f"Docker环境: {info['is_docker']}")
