"""
多模型配置路由
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any

from ..models import MultiModelConfig, MultiModelConfigResponse
from ..services.multi_llm_service import MultiLLMService

router = APIRouter(prefix="/api/multi-model", tags=["多模型配置"])

@router.get("/config", response_model=MultiModelConfigResponse)
async def get_multi_model_config():
    """获取多模型配置"""
    try:
        service = MultiLLMService()
        return await service.get_multi_model_config()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取多模型配置失败: {str(e)}")

@router.put("/config", response_model=MultiModelConfigResponse)
async def update_multi_model_config(config: MultiModelConfig):
    """更新多模型配置"""
    try:
        service = MultiLLMService()
        return await service.update_multi_model_config(config)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新多模型配置失败: {str(e)}")

@router.get("/status")
async def get_config_status() -> Dict[str, Any]:
    """获取配置状态信息"""
    try:
        service = MultiLLMService()
        return service.get_config_status()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取配置状态失败: {str(e)}")

@router.post("/test")
async def test_multi_model_config():
    """测试多模型配置"""
    try:
        service = MultiLLMService()
        
        # 创建测试消息
        from browser_use.llm.messages import SystemMessage, UserMessage, ContentPartTextParam
        messages = [
            SystemMessage(content=[ContentPartTextParam(text="你是一个测试助手")]),
            UserMessage(content="请回复'测试成功'")
        ]
        
        # 发送测试请求
        response = await service.chat_completion(messages)
        
        return {
            "success": True,
            "message": "多模型配置测试成功",
            "response": response
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"多模型配置测试失败: {str(e)}") 