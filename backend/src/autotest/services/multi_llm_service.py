"""
多模型LLM服务模块
支持多个API key轮询机制，增加并发限制
"""

import json
import os
import asyncio
import logging
from typing import List, Dict, Any, Optional
from threading import Lock
import time

from browser_use.llm.deepseek.chat import ChatDeepSeek
from browser_use.llm.openai.chat import ChatOpenAI
from browser_use.llm.messages import SystemMessage, UserMessage, ContentPartTextParam

from ..config_manager import ConfigManager
from ..models import MultiModelConfig, ModelProviderConfig, LLMRequestConfig, MultiModelConfigResponse

class MultiLLMService:
    """多模型LLM服务类"""
    
    def __init__(self):
        self.config_manager = ConfigManager()
        self.logger = logging.getLogger(__name__)
        self._lock = Lock()
        self._request_counters: Dict[str, int] = {}  # 记录每个账号的请求次数
        self._last_request_time: Dict[str, float] = {}  # 记录每个账号的最后请求时间
        
    def _get_multi_model_config_path(self) -> str:
        """获取多模型配置文件路径"""
        config_dir = self.config_manager.config_dir
        return os.path.join(config_dir, "multi_model_config.json")
    
    def _load_multi_model_config(self) -> MultiModelConfig:
        """加载多模型配置"""
        try:
            config_path = self._get_multi_model_config_path()
            if os.path.exists(config_path):
                with open(config_path, "r", encoding="utf-8") as f:
                    config_data = json.load(f)
                    return MultiModelConfig(**config_data)
            else:
                # 返回默认配置
                return self._get_default_config()
        except Exception as e:
            self.logger.error(f"加载多模型配置失败: {e}")
            return self._get_default_config()
    
    def _get_default_config(self) -> MultiModelConfig:
        """获取默认配置"""
        return MultiModelConfig(
            providers=[
                ModelProviderConfig(
                    provider_id="deepseek_default",
                    provider_name="DeepSeek默认配置",
                    model_type="deepseek",
                    base_url="https://api.deepseek.com/v1",
                    model="deepseek-chat",
                    temperature=0.7,
                    max_tokens=None,
                    api_keys=[os.getenv("DEEPSEEK_API_KEY", "")],
                    rate_limit=2,
                    is_active=True,
                    current_key_index=0
                )
            ],
            current_provider_index=0
        )
    
    def _save_multi_model_config(self, config: MultiModelConfig):
        """保存多模型配置"""
        try:
            config_path = self._get_multi_model_config_path()
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(config.model_dump(), f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.logger.error(f"保存多模型配置失败: {e}")
            raise
    
    def _get_next_available_config(self, config: MultiModelConfig) -> Optional[LLMRequestConfig]:
        """获取下一个可用的配置（轮询机制）"""
        with self._lock:
            active_providers = [provider for provider in config.providers if provider.is_active]
            if not active_providers:
                return None
            
            # 尝试找到可用的提供商和API key
            for attempt in range(len(active_providers) * 10):  # 最多尝试10轮
                provider = active_providers[config.current_provider_index % len(active_providers)]
                provider_key = f"{provider.provider_id}_{config.current_provider_index}"
                
                # 检查限流
                current_time = time.time()
                last_request = self._last_request_time.get(provider_key, 0)
                request_count = self._request_counters.get(provider_key, 0)
                
                # 如果距离上次请求超过1秒，重置计数器
                if current_time - last_request > 1:
                    self._request_counters[provider_key] = 0
                    request_count = 0
                
                # 检查是否超过限流
                if request_count < provider.rate_limit:
                    # 获取当前API key
                    if provider.api_keys:
                        api_key = provider.api_keys[provider.current_key_index % len(provider.api_keys)]
                        
                        if api_key:  # 确保API key不为空
                            # 更新计数器和时间
                            self._request_counters[provider_key] = request_count + 1
                            self._last_request_time[provider_key] = current_time
                            
                            # 更新配置中的索引
                            provider.current_key_index = (provider.current_key_index + 1) % len(provider.api_keys)
                            if provider.current_key_index == 0:
                                config.current_provider_index = (config.current_provider_index + 1) % len(active_providers)
                            
                            # 保存配置
                            self._save_multi_model_config(config)
                            
                            return LLMRequestConfig(
                                provider_id=provider.provider_id,
                                model_type=provider.model_type,
                                api_key=api_key,
                                base_url=provider.base_url,
                                model=provider.model,
                                temperature=provider.temperature,
                                max_tokens=provider.max_tokens
                            )
                
                # 移动到下一个提供商
                config.current_provider_index = (config.current_provider_index + 1) % len(active_providers)
                provider.current_key_index = 0
            
            return None
    
    def _create_llm_instance(self, request_config: LLMRequestConfig):
        """创建LLM实例"""
        if request_config.model_type == "deepseek":
            return ChatDeepSeek(
                base_url=request_config.base_url,
                model=request_config.model,
                api_key=request_config.api_key,
                temperature=request_config.temperature,
                max_tokens=request_config.max_tokens
            )
        elif request_config.model_type == "openai":
            return ChatOpenAI(
                model=request_config.model,
                api_key=request_config.api_key,
                temperature=request_config.temperature
            )
        else:
            raise ValueError(f"不支持的模型类型: {request_config.model_type}")
    
    async def chat_completion(self, messages: List, max_retries: int = 3) -> str:
        """聊天完成接口"""
        config = self._load_multi_model_config()
        
        for attempt in range(max_retries):
            try:
                # 获取下一个可用的配置
                request_config = self._get_next_available_config(config)
                if not request_config:
                    raise Exception("没有可用的API key配置")
                
                # 创建LLM实例
                llm = self._create_llm_instance(request_config)
                
                # 发送请求
                self.logger.info(f"使用账号: {request_config.api_key[:8]}... 进行第{attempt + 1}次尝试")
                response = await llm.ainvoke(messages)
                return response.completion
                
            except Exception as e:
                self.logger.warning(f"第{attempt + 1}次请求失败: {e}")
                if attempt == max_retries - 1:
                    raise Exception(f"所有API key都请求失败: {e}")
                await asyncio.sleep(1)  # 等待1秒后重试
    
    async def get_multi_model_config(self) -> MultiModelConfigResponse:
        """获取多模型配置"""
        config = self._load_multi_model_config()
        
        total_providers = len([provider for provider in config.providers if provider.is_active])
        total_api_keys = sum(len(provider.api_keys) for provider in config.providers if provider.is_active)
        
        return MultiModelConfigResponse(
            providers=config.providers,
            current_provider_index=config.current_provider_index,
            total_providers=total_providers,
            total_api_keys=total_api_keys,
            is_valid=total_providers > 0 and total_api_keys > 0
        )
    
    async def update_multi_model_config(self, config: MultiModelConfig) -> MultiModelConfigResponse:
        """更新多模型配置"""
        try:
            # 验证配置
            if not config.providers:
                raise ValueError("至少需要配置一个模型提供商")
            
            active_providers = [provider for provider in config.providers if provider.is_active]
            if not active_providers:
                raise ValueError("至少需要有一个启用的模型提供商")
            
            total_api_keys = sum(len(provider.api_keys) for provider in active_providers)
            if total_api_keys == 0:
                raise ValueError("至少需要配置一个API key")
            
            # 验证每个提供商的配置
            for provider in config.providers:
                if not provider.provider_id:
                    raise ValueError("提供商ID不能为空")
                if not provider.provider_name:
                    raise ValueError("提供商名称不能为空")
                if provider.is_active and not provider.api_keys:
                    raise ValueError(f"启用的提供商 {provider.provider_name} 必须配置至少一个API key")
            
            # 保存配置
            self._save_multi_model_config(config)
            
            # 重置计数器
            with self._lock:
                self._request_counters.clear()
                self._last_request_time.clear()
            
            return await self.get_multi_model_config()
            
        except Exception as e:
            self.logger.error(f"更新多模型配置失败: {e}")
            raise
    
    def get_config_status(self) -> Dict[str, Any]:
        """获取配置状态信息"""
        config = self._load_multi_model_config()
        active_providers = [provider for provider in config.providers if provider.is_active]
        
        status = {
            "total_providers": len(active_providers),
            "total_api_keys": sum(len(provider.api_keys) for provider in active_providers),
            "current_provider_index": config.current_provider_index,
            "provider_details": []
        }
        
        for i, provider in enumerate(active_providers):
            provider_key = f"{provider.provider_id}_{i}"
            request_count = self._request_counters.get(provider_key, 0)
            last_request = self._last_request_time.get(provider_key, 0)
            
            status["provider_details"].append({
                "provider_id": provider.provider_id,
                "provider_name": provider.provider_name,
                "model_type": provider.model_type,
                "api_key_count": len(provider.api_keys),
                "rate_limit": provider.rate_limit,
                "current_requests": request_count,
                "last_request_time": last_request,
                "is_available": request_count < provider.rate_limit
            })
        
        return status 