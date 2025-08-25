#!/usr/bin/env python3
"""
测试执行功能验证脚本
"""

import requests
import time
import json

BASE_URL = "http://localhost:8000"

def test_simple_execution():
    """测试简单的测试执行"""
    print("🧪 测试简单执行功能...")
    
    # 1. 创建一个简单的测试用例
    test_case = {
        "name": "简单页面访问测试",
        "task_content": """
# 简单页面访问测试
打开 https://www.baidu.com
验证页面标题包含"百度"
        """,
        "status": "active",
        "priority": "low",
        "category": "页面访问",
        "expected_result": "能够正常访问百度首页"
    }
    
    # 创建测试用例
    response = requests.post(f"{BASE_URL}/test-cases", json=test_case)
    if response.status_code != 200:
        print(f"❌ 创建测试用例失败: {response.text}")
        return
    
    test_case_id = response.json()["id"]
    print(f"✅ 创建测试用例成功，ID: {test_case_id}")
    
    # 2. 执行测试用例
    execution_data = {
        "test_case_id": test_case_id,
        "headless": True  # 无头模式
    }
    
    response = requests.post(f"{BASE_URL}/test-executions", json=execution_data)
    if response.status_code != 200:
        print(f"❌ 启动测试执行失败: {response.text}")
        return
    
    execution_id = response.json()["id"]
    print(f"✅ 启动测试执行成功，执行ID: {execution_id}")
    
    # 3. 监控执行状态
    print("⏳ 监控执行状态...")
    max_wait = 60  # 最大等待60秒
    wait_count = 0
    
    while wait_count < max_wait:
        response = requests.get(f"{BASE_URL}/test-executions/{execution_id}")
        if response.status_code == 200:
            execution = response.json()
            status = execution["status"]
            print(f"   状态: {status}")
            
            if status in ["passed", "failed", "error"]:
                print(f"✅ 测试执行完成，最终状态: {status}")
                print(f"   整体状态: {execution.get('overall_status', 'N/A')}")
                print(f"   总步骤数: {execution.get('total_steps', 0)}")
                print(f"   通过步骤: {execution.get('passed_steps', 0)}")
                print(f"   失败步骤: {execution.get('failed_steps', 0)}")
                print(f"   总耗时: {execution.get('total_duration', 0)}秒")
                
                if execution.get("summary"):
                    print(f"   测试总结: {execution['summary']}")
                
                # 获取步骤详情
                steps_response = requests.get(f"{BASE_URL}/test-executions/{execution_id}/steps")
                if steps_response.status_code == 200:
                    steps = steps_response.json()
                    print(f"   步骤详情:")
                    for step in steps:
                        print(f"     - {step['step_order']}: {step['step_name']} ({step['status']})")
                        if step.get('error_message'):
                            print(f"       错误: {step['error_message']}")
                
                return
            elif status == "running":
                print(f"   ⏳ 仍在执行中... ({wait_count}秒)")
            else:
                print(f"   ❓ 未知状态: {status}")
        else:
            print(f"❌ 获取执行状态失败: {response.text}")
            return
        
        time.sleep(2)
        wait_count += 2
    
    print("⏰ 等待超时，测试执行可能仍在进行中")

def test_statistics():
    """测试统计信息"""
    print("\n📊 测试统计信息...")
    
    response = requests.get(f"{BASE_URL}/statistics")
    if response.status_code == 200:
        stats = response.json()
        print(f"✅ 统计信息获取成功:")
        print(f"   总测试用例: {stats['total_test_cases']}")
        print(f"   活跃测试用例: {stats['active_test_cases']}")
        print(f"   总执行次数: {stats['total_executions']}")
        print(f"   成功执行: {stats['passed_executions']}")
        print(f"   失败执行: {stats['failed_executions']}")
        print(f"   成功率: {stats['success_rate']}%")
    else:
        print(f"❌ 获取统计信息失败: {response.text}")

def main():
    """主函数"""
    print("🚀 开始测试执行功能验证...")
    
    # 检查服务健康状态
    response = requests.get(f"{BASE_URL}/health")
    if response.status_code != 200:
        print("❌ API服务不可用")
        return
    
    print("✅ API服务正常")
    
    # 测试执行功能
    test_simple_execution()
    
    # 测试统计信息
    test_statistics()
    
    print("\n✅ 测试执行功能验证完成!")

if __name__ == "__main__":
    main() 