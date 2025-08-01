#!/usr/bin/env python3
"""
测试模型配置功能
"""

import requests
import json
import time

# API基础URL
BASE_URL = "http://localhost:8000"

def test_model_config_api():
    """测试模型配置API"""
    print("🧪 测试模型配置API...")
    
    # 1. 获取当前配置
    print("\n1. 获取当前配置...")
    try:
        response = requests.get(f"{BASE_URL}/model-config")
        if response.status_code == 200:
            config = response.json()
            print(f"✅ 当前配置: {json.dumps(config, indent=2, ensure_ascii=False)}")
        else:
            print(f"❌ 获取配置失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 获取配置异常: {e}")
        return False
    
    # 2. 更新配置
    print("\n2. 更新配置...")
    new_config = {
        "model_type": "deepseek",
        "api_key": "test-api-key",
        "base_url": "https://api.deepseek.com/v1",
        "model": "deepseek-chat",
        "temperature": 0.8,
        "max_tokens": 2000
    }
    
    try:
        response = requests.put(f"{BASE_URL}/model-config", json=new_config)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 配置更新成功: {json.dumps(result, indent=2, ensure_ascii=False)}")
        else:
            print(f"❌ 配置更新失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 配置更新异常: {e}")
        return False
    
    # 3. 测试配置
    print("\n3. 测试配置...")
    try:
        response = requests.post(f"{BASE_URL}/model-config/test", json=new_config)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 配置测试结果: {json.dumps(result, indent=2, ensure_ascii=False)}")
        else:
            print(f"❌ 配置测试失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 配置测试异常: {e}")
        return False
    
    return True

def test_browser_agent_with_config():
    """测试BrowserAgent使用配置文件"""
    print("\n🧪 测试BrowserAgent使用配置文件...")
    
    try:
        from backend.src.autotest.browser_agent import BrowserAgent
        
        # 创建代理实例（会自动读取配置文件）
        agent = BrowserAgent()
        
        print(f"✅ BrowserAgent初始化成功")
        print(f"   模型类型: {agent.model_type}")
        print(f"   模型名称: {agent.model}")
        print(f"   基础URL: {agent.base_url}")
        print(f"   温度参数: {agent.temperature}")
        print(f"   最大Token: {agent.max_tokens}")
        
        return True
    except Exception as e:
        print(f"❌ BrowserAgent测试失败: {e}")
        return False

def test_test_executor_with_config():
    """测试TestExecutor使用配置文件"""
    print("\n🧪 测试TestExecutor使用配置文件...")
    
    try:
        from backend.src.autotest.test_executor import TestExecutor
        
        # 创建执行器实例（会自动读取配置文件）
        executor = TestExecutor()
        
        print(f"✅ TestExecutor初始化成功")
        print(f"   模型类型: {executor.model_type}")
        print(f"   模型名称: {executor.model}")
        print(f"   基础URL: {executor.base_url}")
        print(f"   温度参数: {executor.temperature}")
        print(f"   最大Token: {executor.max_tokens}")
        
        return True
    except Exception as e:
        print(f"❌ TestExecutor测试失败: {e}")
        return False

def main():
    """主函数"""
    print("🚀 开始测试模型配置功能...")
    
    # 测试API
    api_success = test_model_config_api()
    
    # 测试BrowserAgent
    agent_success = test_browser_agent_with_config()
    
    # 测试TestExecutor
    executor_success = test_test_executor_with_config()
    
    # 总结
    print("\n" + "="*50)
    print("📊 测试结果总结:")
    print(f"   API测试: {'✅ 通过' if api_success else '❌ 失败'}")
    print(f"   BrowserAgent测试: {'✅ 通过' if agent_success else '❌ 失败'}")
    print(f"   TestExecutor测试: {'✅ 通过' if executor_success else '❌ 失败'}")
    
    if all([api_success, agent_success, executor_success]):
        print("\n🎉 所有测试通过！模型配置功能正常工作。")
    else:
        print("\n⚠️  部分测试失败，请检查配置。")

if __name__ == "__main__":
    main() 