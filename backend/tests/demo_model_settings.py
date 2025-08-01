#!/usr/bin/env python3
"""
模型设置功能演示脚本
"""

import requests
import json
import time

# API基础URL
BASE_URL = "http://localhost:8000"

def demo_model_settings():
    """演示模型设置功能"""
    print("🎭 模型设置功能演示")
    print("=" * 50)
    
    # 1. 获取当前配置
    print("\n1️⃣ 获取当前模型配置...")
    try:
        response = requests.get(f"{BASE_URL}/model-config")
        if response.status_code == 200:
            config = response.json()
            print(f"✅ 当前配置:")
            print(f"   模型类型: {config['model_type']}")
            print(f"   模型名称: {config['model']}")
            print(f"   基础URL: {config['base_url']}")
            print(f"   温度参数: {config['temperature']}")
            print(f"   最大Token: {config['max_tokens']}")
            print(f"   配置有效: {'是' if config['is_valid'] else '否'}")
        else:
            print(f"❌ 获取配置失败: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ 获取配置异常: {e}")
        return
    
    # 2. 演示DeepSeek配置
    print("\n2️⃣ 配置DeepSeek模型...")
    deepseek_config = {
        "model_type": "deepseek",
        "api_key": "sk-demo-deepseek-key",
        "base_url": "https://api.deepseek.com/v1",
        "model": "deepseek-chat",
        "temperature": 0.7,
        "max_tokens": 1500
    }
    
    try:
        response = requests.put(f"{BASE_URL}/model-config", json=deepseek_config)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ DeepSeek配置保存成功")
            print(f"   配置有效: {'是' if result['is_valid'] else '否'}")
        else:
            print(f"❌ DeepSeek配置保存失败: {response.status_code}")
    except Exception as e:
        print(f"❌ DeepSeek配置保存异常: {e}")
    
    # 3. 演示OpenAI配置
    print("\n3️⃣ 配置OpenAI模型...")
    openai_config = {
        "model_type": "openai",
        "api_key": "sk-demo-openai-key",
        "base_url": "https://api.openai.com/v1",
        "model": "gpt-4o",
        "temperature": 0.8,
        "max_tokens": 2000
    }
    
    try:
        response = requests.put(f"{BASE_URL}/model-config", json=openai_config)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ OpenAI配置保存成功")
            print(f"   配置有效: {'是' if result['is_valid'] else '否'}")
        else:
            print(f"❌ OpenAI配置保存失败: {response.status_code}")
    except Exception as e:
        print(f"❌ OpenAI配置保存异常: {e}")
    
    # 4. 测试配置
    print("\n4️⃣ 测试模型配置...")
    test_config = {
        "model_type": "deepseek",
        "api_key": "sk-test-key",
        "base_url": "https://api.deepseek.com/v1",
        "model": "deepseek-chat",
        "temperature": 0.7,
        "max_tokens": 1000
    }
    
    try:
        response = requests.post(f"{BASE_URL}/model-config/test", json=test_config)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 配置测试结果: {result['message']}")
        else:
            print(f"❌ 配置测试失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 配置测试异常: {e}")
    
    # 5. 显示配置文件内容
    print("\n5️⃣ 查看配置文件...")
    try:
        # 使用ConfigManager获取配置文件路径
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__), "backend", "src"))
        from autotest.config_manager import ConfigManager
        
        config_manager = ConfigManager()
        config_path = config_manager.get_model_config_path()
        
        if config_path.exists():
            with open(config_path, "r", encoding="utf-8") as f:
                config_content = json.load(f)
            print(f"✅ 配置文件内容:")
            print(json.dumps(config_content, indent=2, ensure_ascii=False))
        else:
            print("⚠️  配置文件不存在，使用默认配置")
    except Exception as e:
        print(f"❌ 读取配置文件失败: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 演示完成！")
    print("\n📝 使用说明:")
    print("1. 访问 http://localhost:3000 打开前端界面")
    print("2. 点击导航栏的'模型设置'选项")
    print("3. 在界面中配置你的模型参数")
    print("4. 点击'测试配置'验证设置")
    print("5. 点击'保存配置'应用设置")
    print("\n🔧 API接口:")
    print(f"   GET  {BASE_URL}/model-config     - 获取配置")
    print(f"   PUT  {BASE_URL}/model-config     - 更新配置")
    print(f"   POST {BASE_URL}/model-config/test - 测试配置")

def show_api_docs():
    """显示API文档"""
    print("\n📚 API文档")
    print("=" * 50)
    
    print("\n🔍 GET /model-config")
    print("获取当前模型配置")
    print("响应示例:")
    print(json.dumps({
        "model_type": "deepseek",
        "api_key": "sk-***",
        "base_url": "https://api.deepseek.com/v1",
        "model": "deepseek-chat",
        "temperature": 0.7,
        "max_tokens": 2000,
        "is_valid": True
    }, indent=2, ensure_ascii=False))
    
    print("\n✏️  PUT /model-config")
    print("更新模型配置")
    print("请求体示例:")
    print(json.dumps({
        "model_type": "deepseek",
        "api_key": "sk-your-api-key",
        "base_url": "https://api.deepseek.com/v1",
        "model": "deepseek-chat",
        "temperature": 0.7,
        "max_tokens": 2000
    }, indent=2, ensure_ascii=False))
    
    print("\n🧪 POST /model-config/test")
    print("测试模型配置")
    print("响应示例:")
    print(json.dumps({
        "success": True,
        "message": "模型配置测试成功"
    }, indent=2, ensure_ascii=False))

def main():
    """主函数"""
    print("🚀 AutoTest 模型设置功能演示")
    print("=" * 50)
    
    # 检查服务是否运行
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            print("✅ 后端服务运行正常")
        else:
            print("❌ 后端服务异常")
            return
    except Exception as e:
        print(f"❌ 无法连接到后端服务: {e}")
        print("请确保后端服务已启动: cd backend && python3 run.py")
        return
    
    # 运行演示
    demo_model_settings()
    
    # 显示API文档
    show_api_docs()

if __name__ == "__main__":
    main() 