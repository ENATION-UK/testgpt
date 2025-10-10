"""
配置管理路由
"""

from fastapi import APIRouter, HTTPException

from ..models import PromptConfig, PromptConfigResponse
from ..services.config_service import ConfigService

router = APIRouter(tags=["配置管理"])

# 提示词配置路由
@router.get("/prompt-config", response_model=PromptConfigResponse)
async def get_prompt_config():
    """获取当前提示词配置"""
    return await ConfigService.get_prompt_config()

@router.put("/prompt-config", response_model=PromptConfigResponse)
async def update_prompt_config(config: PromptConfig):
    """更新提示词配置"""
    return await ConfigService.update_prompt_config(config) 