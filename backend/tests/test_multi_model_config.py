"""
测试多模型配置功能
"""

import asyncio
import json
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from testgpt.services.multi_llm_service import MultiLLMService
from testgpt.models import MultiModelConfig, ModelProviderConfig

async def test_multi_model_config():
    """测试多模型配置功能"""
    print("🧪 开始测试多模型配置功能...")
    
    # 创建多模型服务实例
    service = MultiLLMService()
    
    # 测试1: 获取默认配置
    print("\n1. 测试获取默认配置...")
    config = service._load_multi_model_config()
    print(f"默认配置: {json.dumps(config.model_dump(), indent=2, ensure_ascii=False)}")
    
    # 测试2: 创建自定义配置
    print("\n2. 测试创建自定义配置...")
    custom_config = MultiModelConfig(
        providers=[
            ModelProviderConfig(
                provider_id="openai_provider_1",
                provider_name="OpenAI提供商1",
                model_type="openai",
                base_url="https://api.openai.com/v1",
                model="gpt-4o",
                temperature=0.7,
                max_tokens=None,
                api_keys=["sk-test-key-1", "sk-test-key-2"],
                rate_limit=2,
                is_active=True,
                current_key_index=0
            ),
            ModelProviderConfig(
                provider_id="openai_provider_2",
                provider_name="OpenAI提供商2",
                model_type="openai",
                base_url="https://api.openai.com/v1",
                model="gpt-4o",
                temperature=0.7,
                max_tokens=None,
                api_keys=["sk-test-key-3", "sk-test-key-4"],
                rate_limit=2,
                is_active=True,
                current_key_index=0
            ),
            ModelProviderConfig(
                provider_id="deepseek_provider_1",
                provider_name="DeepSeek提供商1",
                model_type="deepseek",
                base_url="https://api.deepseek.com/v1",
                model="deepseek-chat",
                temperature=0.7,
                max_tokens=None,
                api_keys=["sk-test-key-5", "sk-test-key-6"],
                rate_limit=2,
                is_active=True,
                current_key_index=0
            ),
            ModelProviderConfig(
                provider_id="deepseek_provider_2",
                provider_name="DeepSeek提供商2",
                model_type="deepseek",
                base_url="https://api.deepseek.com/v1",
                model="deepseek-chat",
                temperature=0.7,
                max_tokens=None,
                api_keys=["sk-test-key-7", "sk-test-key-8"],
                rate_limit=2,
                is_active=True,
                current_key_index=0
            )
        ],
        current_provider_index=0
    )
    
    # 保存配置
    service._save_multi_model_config(custom_config)
    print("自定义配置已保存")
    
    # 测试3: 重新加载配置
    print("\n3. 测试重新加载配置...")
    loaded_config = service._load_multi_model_config()
    print(f"加载的配置: {json.dumps(loaded_config.model_dump(), indent=2, ensure_ascii=False)}")
    
    # 测试4: 测试轮询机制
    print("\n4. 测试轮询机制...")
    for i in range(10):
        request_config = service._get_next_available_config(loaded_config)

        if request_config:
            print(f"第{i+1}次请求: 使用API key:{request_config.model_type}-- {request_config.api_key}")
        else:
            print(f"第{i+1}次请求: 没有可用的配置")
    
    # 测试5: 获取配置状态
    print("\n5. 测试获取配置状态...")
    status = service.get_config_status()
    print(f"配置状态: {json.dumps(status, indent=2, ensure_ascii=False)}")
    
    # 测试6: 测试API接口
    print("\n6. 测试API接口...")
    try:
        config_response = await service.get_multi_model_config()
        print(f"API配置响应: {json.dumps(config_response.model_dump(), indent=2, ensure_ascii=False)}")
    except Exception as e:
        print(f"API测试失败: {e}")
    
    print("\n✅ 多模型配置功能测试完成!")

async def test_llm_integration():
    """测试LLM集成"""
    print("\n🧪 开始测试LLM集成...")
    
    service = MultiLLMService()
    
    # 创建测试消息
    from browser_use.llm.messages import SystemMessage, UserMessage, ContentPartTextParam
    
    messages = [
        SystemMessage(content=[ContentPartTextParam(text="你是一个测试助手")]),
        UserMessage(content="请回复'测试成功'")
    ]
    
    try:
        # 注意：这里需要真实的API key才能测试
        print("注意：需要真实的API key才能进行完整测试")
        print("跳过实际的LLM调用测试")
        
        # 测试配置获取
        config = service._load_multi_model_config()
        request_config = service._get_next_available_config(config)
        if request_config:
            print(f"成功获取请求配置: {request_config.model_type}")
        else:
            print("无法获取请求配置")
            
    except Exception as e:
        print(f"LLM集成测试失败: {e}")
    
    print("✅ LLM集成测试完成!")

if __name__ == "__main__":
    # 运行测试
    asyncio.run(test_multi_model_config())
    asyncio.run(test_llm_integration()) 