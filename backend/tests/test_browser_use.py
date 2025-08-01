#!/usr/bin/env python3
"""
Browser Use 功能测试脚本
"""

import asyncio
import requests
import json
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

BASE_URL = "http://localhost:8000"

def test_browser_task_api():
    """测试浏览器任务API"""
    print("🔍 测试浏览器任务API...")
    
    # 测试数据
    task_data = {
        "task": "打开百度，搜索Python教程",
        "model_type": "deepseek",
        "api_key": "",  # 使用你提供的API密钥
        "headless": False,
        "use_vision": False
    }
    
    try:
        # 测试 /browser/task 端点
        print("1. 测试 /browser/task 端点:")
        response = requests.post(f"{BASE_URL}/browser/task", json=task_data)
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"响应: {json.dumps(result, indent=2, ensure_ascii=False)}")
        else:
            print(f"错误: {response.text}")
        
        print()
        
        # 测试 /browser/agent 端点
        print("2. 测试 /browser/agent 端点:")
        response = requests.post(f"{BASE_URL}/browser/agent", json=task_data)
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"响应: {json.dumps(result, indent=2, ensure_ascii=False)}")
        else:
            print(f"错误: {response.text}")
        
        print()
        
    except Exception as e:
        print(f"❌ API测试失败: {e}")

def test_browser_agent_direct():
    """直接测试Browser Agent"""
    print("🔍 直接测试Browser Agent...")
    
    async def run_test():
        try:
            from src.autotest.browser_agent import BrowserAgent
            
            # 创建浏览器代理
            agent = BrowserAgent(
                model_type="deepseek",
                api_key=""
            )
            
            # 启动浏览器
            print("启动浏览器...")
            await agent.start_browser(headless=False)
            
            # 执行简单任务
            print("执行任务...")
            result = await agent.run_task(
                task="打开百度首页",
                use_vision=False,
                save_conversation_path='/tmp/test_browser.log'
            )
            
            print(f"任务结果: {json.dumps(result, indent=2, ensure_ascii=False)}")
            
            # 关闭浏览器
            await agent.stop_browser()
            
        except Exception as e:
            print(f"❌ 直接测试失败: {e}")
    
    # 运行异步测试
    asyncio.run(run_test())

def test_health_check():
    """测试健康检查"""
    print("🔍 测试健康检查...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.json()}")
        print()
    except Exception as e:
        print(f"❌ 健康检查失败: {e}")

def main():
    """主测试函数"""
    print("🚀 开始Browser Use功能测试...")
    print("=" * 50)
    
    # 检查环境变量
    print("📋 环境检查:")
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if api_key:
        print("✅ DEEPSEEK_API_KEY 已设置")
    else:
        print("⚠️  DEEPSEEK_API_KEY 未设置，将使用代码中的默认值")
    print()
    
    # 测试健康检查
    test_health_check()
    
    # 测试API端点
    test_browser_task_api()
    
    # 直接测试Browser Agent
    test_browser_agent_direct()
    
    print("✅ Browser Use功能测试完成！")
    print("💡 注意：浏览器自动化测试需要图形界面支持")

if __name__ == "__main__":
    main() 