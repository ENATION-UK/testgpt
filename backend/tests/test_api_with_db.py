#!/usr/bin/env python3
"""
包含数据库功能的API测试脚本
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_health():
    """测试健康检查端点"""
    print("🔍 测试健康检查...")
    response = requests.get(f"{BASE_URL}/health")
    print(f"状态码: {response.status_code}")
    print(f"响应: {response.json()}")
    print()

def test_test_cases_crud():
    """测试测试用例的CRUD操作"""
    print("🔍 测试测试用例CRUD操作...")
    
    # 1. 获取所有测试用例
    print("1. 获取所有测试用例:")
    response = requests.get(f"{BASE_URL}/test-cases")
    print(f"状态码: {response.status_code}")
    test_cases = response.json()
    print(f"测试用例数量: {len(test_cases)}")
    for case in test_cases[:3]:  # 显示前3个
        print(f"   - ID: {case['id']}, 名称: {case['name']}, 状态: {case['status']}")
    print()
    
    # 2. 创建新测试用例
    print("2. 创建新测试用例:")
    new_case = {
        "name": "API集成测试",
        "description": "测试API与数据库的集成功能",
        "status": "active"
    }
    response = requests.post(f"{BASE_URL}/test-cases", json=new_case)
    print(f"状态码: {response.status_code}")
    created_case = response.json()
    print(f"创建的测试用例: {json.dumps(created_case, indent=2, ensure_ascii=False)}")
    case_id = created_case["id"]
    print()
    
    # 3. 获取特定测试用例
    print("3. 获取特定测试用例:")
    response = requests.get(f"{BASE_URL}/test-cases/{case_id}")
    print(f"状态码: {response.status_code}")
    case = response.json()
    print(f"测试用例详情: {json.dumps(case, indent=2, ensure_ascii=False)}")
    print()
    
    # 4. 更新测试用例
    print("4. 更新测试用例:")
    update_data = {
        "name": "更新后的API集成测试",
        "status": "inactive"
    }
    response = requests.put(f"{BASE_URL}/test-cases/{case_id}", json=update_data)
    print(f"状态码: {response.status_code}")
    updated_case = response.json()
    print(f"更新后的测试用例: {json.dumps(updated_case, indent=2, ensure_ascii=False)}")
    print()
    
    # 5. 按状态查询
    print("5. 按状态查询测试用例:")
    response = requests.get(f"{BASE_URL}/test-cases/status/inactive")
    print(f"状态码: {response.status_code}")
    inactive_cases = response.json()
    print(f"非活跃状态的测试用例: {len(inactive_cases)} 个")
    for case in inactive_cases:
        print(f"   - ID: {case['id']}, 名称: {case['name']}")
    print()
    
    # 6. 删除测试用例
    print("6. 删除测试用例:")
    response = requests.delete(f"{BASE_URL}/test-cases/{case_id}")
    print(f"状态码: {response.status_code}")
    print(f"删除结果: {response.json()}")
    print()
    
    # 7. 验证删除
    print("7. 验证删除:")
    response = requests.get(f"{BASE_URL}/test-cases/{case_id}")
    print(f"状态码: {response.status_code}")
    if response.status_code == 404:
        print("✅ 测试用例已成功删除")
    else:
        print("❌ 测试用例删除失败")
    print()

def test_items_api():
    """测试原有的商品API（确保兼容性）"""
    print("🔍 测试原有商品API...")
    
    # 创建商品
    new_item = {
        "name": "测试商品",
        "description": "这是一个测试商品",
        "price": 99.99
    }
    response = requests.post(f"{BASE_URL}/items", json=new_item)
    print(f"创建商品状态码: {response.status_code}")
    
    # 获取商品列表
    response = requests.get(f"{BASE_URL}/items")
    print(f"获取商品列表状态码: {response.status_code}")
    items = response.json()
    print(f"商品数量: {len(items)}")
    print()

def main():
    """主测试函数"""
    print("🚀 开始API与数据库集成测试...")
    print("=" * 50)
    
    try:
        test_health()
        test_test_cases_crud()
        test_items_api()
        
        print("✅ 所有测试完成！")
        print("📖 你可以在浏览器中访问 http://localhost:8000/docs 查看API文档")
        
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到API服务器，请确保应用正在运行")
        print("💡 运行命令: python run.py")
    except Exception as e:
        print(f"❌ 测试过程中出现错误: {e}")

if __name__ == "__main__":
    main() 