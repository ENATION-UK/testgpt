#!/usr/bin/env python3
"""
完整功能测试脚本
测试所有集成的功能
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_basic_api():
    """测试基础API"""
    print("🔍 测试基础API...")
    
    # 健康检查
    response = requests.get(f"{BASE_URL}/health")
    print(f"健康检查: {response.status_code} - {response.json()}")
    
    # 根路径
    response = requests.get(f"{BASE_URL}/")
    print(f"根路径: {response.status_code} - {response.json()}")
    
    print()

def test_database_api():
    """测试数据库API"""
    print("🔍 测试数据库API...")
    
    # 获取测试用例
    response = requests.get(f"{BASE_URL}/test-cases")
    print(f"获取测试用例: {response.status_code}")
    if response.status_code == 200:
        cases = response.json()
        print(f"测试用例数量: {len(cases)}")
    
    # 创建测试用例
    new_case = {
        "name": "Browser Use集成测试",
        "description": "测试Browser Use功能集成",
        "status": "active"
    }
    response = requests.post(f"{BASE_URL}/test-cases", json=new_case)
    print(f"创建测试用例: {response.status_code}")
    
    print()

def test_browser_api():
    """测试浏览器API"""
    print("🔍 测试浏览器API...")
    
    # 测试浏览器任务
    task_data = {
        "task": "打开百度首页",
        "model_type": "deepseek",
        "api_key": "",
        "headless": True,
        "use_vision": False
    }
    
    response = requests.post(f"{BASE_URL}/browser/task", json=task_data)
    print(f"浏览器任务: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"任务结果: {result['success']} - {result['result']}")
    
    print()

def test_api_documentation():
    """测试API文档"""
    print("🔍 测试API文档...")
    
    # 检查Swagger文档
    response = requests.get(f"{BASE_URL}/docs")
    print(f"Swagger文档: {response.status_code}")
    
    # 检查OpenAPI规范
    response = requests.get(f"{BASE_URL}/openapi.json")
    print(f"OpenAPI规范: {response.status_code}")
    
    print()

def main():
    """主测试函数"""
    print("🚀 开始完整功能测试...")
    print("=" * 50)
    
    try:
        # 测试基础API
        test_basic_api()
        
        # 测试数据库API
        test_database_api()
        
        # 测试浏览器API
        test_browser_api()
        
        # 测试API文档
        test_api_documentation()
        
        print("✅ 所有功能测试完成！")
        print("📖 API文档地址: http://localhost:8000/docs")
        print("🔧 项目功能:")
        print("   - FastAPI REST API")
        print("   - SQLAlchemy ORM (SQLite/MySQL)")
        print("   - Browser Use 浏览器自动化")
        print("   - 完整的CRUD操作")
        print("   - 自动API文档生成")
        
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到API服务器，请确保应用正在运行")
        print("💡 运行命令: python run.py")
    except Exception as e:
        print(f"❌ 测试过程中出现错误: {e}")

if __name__ == "__main__":
    main() 