"""
配置管理服务
"""

import json
from typing import Dict, Any

from ..config_manager import ConfigManager
from ..models import PromptConfig, PromptConfigResponse

class ConfigService:
    """配置管理服务类"""
    
    @staticmethod
    async def get_prompt_config() -> PromptConfigResponse:
        """获取当前提示词配置"""
        try:
            config_manager = ConfigManager()
            config_path = config_manager.get_prompt_config_path()
            if config_path.exists():
                with open(config_path, "r", encoding="utf-8") as f:
                    config = json.load(f)
            else:
                # 默认配置
                config = {
                    "custom_prompt": ""
                }
            
            # 验证配置有效性
            is_valid = True  # 提示词可以为空
            
            return PromptConfigResponse(
                **config,
                is_valid=is_valid
            )
        except Exception as e:
            raise Exception(f"获取提示词配置失败: {str(e)}")

    @staticmethod
    async def update_prompt_config(config: PromptConfig) -> PromptConfigResponse:
        """更新提示词配置"""
        try:
            config_manager = ConfigManager()
            config_path = config_manager.get_prompt_config_path()
            
            # 保存配置到文件
            config_data = config.dict()
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(config_data, f, ensure_ascii=False, indent=2)
            
            # 验证配置有效性
            is_valid = True  # 提示词可以为空
            
            return PromptConfigResponse(
                **config_data,
                is_valid=is_valid
            )
        except Exception as e:
            raise Exception(f"更新提示词配置失败: {str(e)}") 