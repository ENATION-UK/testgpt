#!/usr/bin/env python3
"""
API测试脚本
用于测试AutoTest API的各个功能
"""

import requests
import json
import time
from typing import Dict, Any

# API基础URL
BASE_URL = "http://localhost:8000"

def test_health_check():
    """测试健康检查"""
    print("🔍 测试健康检查...")
    response = requests.get(f"{BASE_URL}/health")
    print(f"状态码: {response.status_code}")
    print(f"响应: {response.json()}")
    return response.status_code == 200

def test_get_test_cases():
    """测试获取测试用例列表"""
    print("\n🔍 测试获取测试用例列表...")
    response = requests.get(f"{BASE_URL}/test-cases")
    print(f"状态码: {response.status_code}")
    if response.status_code == 200:
        test_cases = response.json()
        print(f"测试用例数量: {len(test_cases)}")
        for case in test_cases:
            print(f"  - {case['id']}: {case['name']} ({case['status']})")
    else:
        print(f"错误: {response.text}")
    return response.status_code == 200

def test_create_test_case():
    """测试创建测试用例"""
    print("\n🔍 测试创建测试用例...")
    
    test_case_data = {
        "name": "API测试用例",
        "description": "通过API创建的测试用例",
        "task_content": """
# API测试用例
打开 https://www.baidu.com
搜索"Python自动化测试"
验证搜索结果包含Python相关内容
        """,
        "status": "active",
        "priority": "medium",
        "category": "API测试",
        "tags": ["api", "test"],
        "expected_result": "能够正常搜索并显示Python相关内容"
    }
    
    response = requests.post(
        f"{BASE_URL}/test-cases",
        json=test_case_data,
        headers={"Content-Type": "application/json"}
    )
    print(f"状态码: {response.status_code}")
    if response.status_code == 200:
        created_case = response.json()
        print(f"创建的测试用例: {created_case['id']}: {created_case['name']}")
        return created_case['id']
    else:
        print(f"错误: {response.text}")
        return None

def test_execute_test_case(test_case_id: int):
    """测试执行测试用例"""
    print(f"\n🔍 测试执行测试用例 (ID: {test_case_id})...")
    
    execution_data = {
        "test_case_id": test_case_id,
        "headless": True  # 无头模式执行
    }
    
    response = requests.post(
        f"{BASE_URL}/test-executions",
        json=execution_data,
        headers={"Content-Type": "application/json"}
    )
    print(f"状态码: {response.status_code}")
    if response.status_code == 200:
        execution = response.json()
        print(f"执行记录ID: {execution['id']}")
        print(f"执行状态: {execution['status']}")
        return execution['id']
    else:
        print(f"错误: {response.text}")
        return None

def test_get_execution_status(execution_id: int):
    """测试获取执行状态"""
    print(f"\n🔍 测试获取执行状态 (ID: {execution_id})...")
    
    # 等待一段时间让测试执行
    print("等待测试执行...")
    time.sleep(5)
    
    response = requests.get(f"{BASE_URL}/test-executions/{execution_id}")
    print(f"状态码: {response.status_code}")
    if response.status_code == 200:
        execution = response.json()
        print(f"执行状态: {execution['status']}")
        print(f"整体状态: {execution['overall_status']}")
        print(f"总步骤数: {execution['total_steps']}")
        print(f"通过步骤: {execution['passed_steps']}")
        print(f"失败步骤: {execution['failed_steps']}")
        print(f"总耗时: {execution['total_duration']}秒")
        if execution['summary']:
            print(f"测试总结: {execution['summary']}")
        return execution['status'] != 'running'
    else:
        print(f"错误: {response.text}")
        return False

def test_get_execution_steps(execution_id: int):
    """测试获取执行步骤详情"""
    print(f"\n🔍 测试获取执行步骤详情 (ID: {execution_id})...")
    
    response = requests.get(f"{BASE_URL}/test-executions/{execution_id}/steps")
    print(f"状态码: {response.status_code}")
    if response.status_code == 200:
        steps = response.json()
        print(f"步骤数量: {len(steps)}")
        for step in steps:
            print(f"  - {step['step_order']}: {step['step_name']} ({step['status']})")
            if step['error_message']:
                print(f"    错误: {step['error_message']}")
    else:
        print(f"错误: {response.text}")

def test_get_statistics():
    """测试获取统计信息"""
    print("\n🔍 测试获取统计信息...")
    
    response = requests.get(f"{BASE_URL}/statistics")
    print(f"状态码: {response.status_code}")
    if response.status_code == 200:
        stats = response.json()
        print(f"总测试用例: {stats['total_test_cases']}")
        print(f"活跃测试用例: {stats['active_test_cases']}")
        print(f"总执行次数: {stats['total_executions']}")
        print(f"成功执行: {stats['passed_executions']}")
        print(f"失败执行: {stats['failed_executions']}")
        print(f"成功率: {stats['success_rate']}%")
    else:
        print(f"错误: {response.text}")

def test_batch_execution():
    """测试批量执行"""
    print("\n🔍 测试批量执行...")
    
    # 先获取所有测试用例
    response = requests.get(f"{BASE_URL}/test-cases")
    if response.status_code == 200:
        test_cases = response.json()
        if len(test_cases) >= 2:
            test_case_ids = [test_cases[0]['id'], test_cases[1]['id']]
            
            batch_data = {
                "test_case_ids": test_case_ids,
                "headless": True
            }
            
            response = requests.post(
                f"{BASE_URL}/test-executions/batch",
                json=batch_data,
                headers={"Content-Type": "application/json"}
            )
            print(f"状态码: {response.status_code}")
            if response.status_code == 200:
                result = response.json()
                print(f"批量执行结果: {result}")
            else:
                print(f"错误: {response.text}")
        else:
            print("测试用例数量不足，跳过批量执行测试")
    else:
        print("获取测试用例失败，跳过批量执行测试")

def main():
    """主测试函数"""
    print("🚀 开始API测试...")
    
    # 测试健康检查
    if not test_health_check():
        print("❌ 健康检查失败，停止测试")
        return
    
    # 测试获取测试用例
    test_get_test_cases()
    
    # 测试创建测试用例
    new_case_id = test_create_test_case()
    
    if new_case_id:
        # 测试执行测试用例
        execution_id = test_execute_test_case(new_case_id)
        
        if execution_id:
            # 等待测试完成
            max_wait = 30  # 最大等待30秒
            wait_count = 0
            while wait_count < max_wait:
                if test_get_execution_status(execution_id):
                    break
                time.sleep(2)
                wait_count += 2
            
            # 获取执行步骤详情
            test_get_execution_steps(execution_id)
    
    # 测试批量执行
    test_batch_execution()
    
    # 测试统计信息
    test_get_statistics()
    
    print("\n✅ API测试完成!")

if __name__ == "__main__":
    main() 