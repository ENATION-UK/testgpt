"""
配置管理路由
"""

from fastapi import APIRouter, HTTPException
from sqlalchemy.orm import Session

from ..models import ModelConfig, ModelConfigResponse, PromptConfig, PromptConfigResponse
from ..services.config_service import ConfigService

router = APIRouter(tags=["配置管理"])

# 模型配置路由
@router.get("/model-config", response_model=ModelConfigResponse)
async def get_model_config():
    """获取当前模型配置"""
    return await ConfigService.get_model_config()

@router.put("/model-config", response_model=ModelConfigResponse)
async def update_model_config(config: ModelConfig):
    """更新模型配置"""
    return await ConfigService.update_model_config(config)

@router.post("/model-config/test")
async def test_model_config(config: ModelConfig):
    """测试模型配置"""
    return await ConfigService.test_model_config(config)

# 提示词配置路由
@router.get("/prompt-config", response_model=PromptConfigResponse)
async def get_prompt_config():
    """获取当前提示词配置"""
    return await ConfigService.get_prompt_config()

@router.put("/prompt-config", response_model=PromptConfigResponse)
async def update_prompt_config(config: PromptConfig):
    """更新提示词配置"""
    return await ConfigService.update_prompt_config(config) 