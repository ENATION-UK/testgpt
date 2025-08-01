"""
配置管理服务
"""

import json
import os
from typing import Dict, Any

from ..config_manager import ConfigManager
from ..models import ModelConfig, ModelConfigResponse, PromptConfig, PromptConfigResponse
from ..browser_agent import BrowserAgent

class ConfigService:
    """配置管理服务类"""
    
    @staticmethod
    async def get_model_config() -> ModelConfigResponse:
        """获取当前模型配置"""
        try:
            config_manager = ConfigManager()
            config_path = config_manager.get_model_config_path()
            if config_path.exists():
                with open(config_path, "r", encoding="utf-8") as f:
                    config = json.load(f)
            else:
                # 默认配置
                config = {
                    "model_type": "deepseek",
                    "api_key": os.getenv("DEEPSEEK_API_KEY", ""),
                    "base_url": "https://api.deepseek.com/v1",
                    "model": "deepseek-chat",
                    "temperature": 0.7,
                    "max_tokens": None
                }
            
            # 验证配置有效性
            is_valid = bool(config.get("api_key"))
            
            return ModelConfigResponse(
                **config,
                is_valid=is_valid
            )
        except Exception as e:
            raise Exception(f"获取模型配置失败: {str(e)}")

    @staticmethod
    async def update_model_config(config: ModelConfig) -> ModelConfigResponse:
        """更新模型配置"""
        try:
            config_manager = ConfigManager()
            config_path = config_manager.get_model_config_path()
            
            # 保存配置到文件
            config_data = config.dict()
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(config_data, f, ensure_ascii=False, indent=2)
            
            # 验证配置有效性
            is_valid = bool(config.api_key)
            
            return ModelConfigResponse(
                **config_data,
                is_valid=is_valid
            )
        except Exception as e:
            raise Exception(f"更新模型配置失败: {str(e)}")

    @staticmethod
    async def test_model_config(config: ModelConfig) -> Dict[str, Any]:
        """测试模型配置"""
        try:
            # 创建临时代理测试配置
            agent = BrowserAgent(
                model_type=config.model_type,
                api_key=config.api_key,
                base_url=config.base_url,
                model=config.model
            )
            
            # 尝试初始化LLM
            llm = agent._init_llm()
            
            return {
                "success": True,
                "message": "模型配置测试成功"
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"模型配置测试失败: {str(e)}"
            }

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