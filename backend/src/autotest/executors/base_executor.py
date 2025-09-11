"""
基础执行器模块
"""
import logging
from typing import Dict, Any, Optional

from ..services.multi_llm_service import MultiLLMService
from ..config_manager import ConfigManager

class BaseExecutor:
    """基础执行器"""
    
    def __init__(self):
        self.multi_llm_service = MultiLLMService()
        self.logger = logging.getLogger(__name__)
        self.config_manager = ConfigManager()
    
    def _load_config(self) -> dict:
        """从配置文件加载模型配置"""
        try:
            config_path = self.config_manager.get_multi_model_config_path()
            if config_path.exists():
                import json
                with open(config_path, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception as e:
            self.logger.warning(f"加载配置文件失败: {e}")
        return {}
    
    def _load_custom_prompt(self) -> str:
        """加载自定义提示词"""
        try:
            config_path = self.config_manager.get_prompt_config_path()
            if config_path.exists():
                import json
                with open(config_path, "r", encoding="utf-8") as f:
                    config = json.load(f)
                    return config.get("custom_prompt", "")
            return ""
        except Exception as e:
            self.logger.warning(f"加载自定义提示词失败: {e}")
            return ""
