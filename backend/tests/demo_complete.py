#!/usr/bin/env python3
"""
AutoTest 完整功能演示脚本
展示Web自动化测试工具的所有功能
"""

import requests
import time
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"

def print_header(title):
    """打印标题"""
    print("\n" + "="*60)
    print(f"🎯 {title}")
    print("="*60)

def print_section(title):
    """打印章节标题"""
    print(f"\n📋 {title}")
    print("-" * 40)

def demo_health_check():
    """演示健康检查"""
    print_section("健康检查")
    
    response = requests.get(f"{BASE_URL}/health")
    if response.status_code == 200:
        health = response.json()
        print(f"✅ 服务状态: {health['status']}")
        print(f"🕒 时间戳: {health['timestamp']}")
        return True
    else:
        print(f"❌ 服务不可用: {response.status_code}")
        return False

def demo_test_case_management():
    """演示测试用例管理"""
    print_section("测试用例管理")
    
    # 1. 获取现有测试用例
    print("1. 获取现有测试用例:")
    response = requests.get(f"{BASE_URL}/test-cases")
    if response.status_code == 200:
        test_cases = response.json()
        print(f"   现有测试用例数量: {len(test_cases)}")
        for case in test_cases:
            print(f"   - {case['id']}: {case['name']} ({case['status']})")
    
    # 2. 创建新测试用例
    print("\n2. 创建新测试用例:")
    new_test_case = {
        "name": "GitHub搜索演示",
        "description": "演示GitHub搜索功能",
        "task_content": """
# GitHub搜索演示
打开 https://github.com
搜索"Python FastAPI"
验证搜索结果包含相关项目
        """,
        "status": "active",
        "priority": "medium",
        "category": "搜索功能",
        "tags": ["github", "search", "demo"],
        "expected_result": "能够正常搜索并显示Python FastAPI相关项目"
    }
    
    response = requests.post(f"{BASE_URL}/test-cases", json=new_test_case)
    if response.status_code == 200:
        created_case = response.json()
        print(f"   ✅ 创建成功: {created_case['id']} - {created_case['name']}")
        return created_case['id']
    else:
        print(f"   ❌ 创建失败: {response.text}")
        return None

def demo_test_execution(test_case_id):
    """演示测试执行"""
    print_section("测试执行")
    
    # 1. 启动测试执行
    print("1. 启动测试执行:")
    execution_data = {
        "test_case_id": test_case_id,
        "headless": True
    }
    
    response = requests.post(f"{BASE_URL}/test-executions", json=execution_data)
    if response.status_code == 200:
        execution = response.json()
        execution_id = execution['id']
        print(f"   ✅ 执行启动成功: {execution_id}")
        print(f"   📊 执行状态: {execution['status']}")
    else:
        print(f"   ❌ 执行启动失败: {response.text}")
        return None
    
    # 2. 监控执行进度
    print("\n2. 监控执行进度:")
    max_wait = 90  # 最大等待90秒
    wait_count = 0
    
    while wait_count < max_wait:
        response = requests.get(f"{BASE_URL}/test-executions/{execution_id}")
        if response.status_code == 200:
            execution = response.json()
            status = execution['status']
            
            if status in ["passed", "failed", "error"]:
                print(f"   ✅ 执行完成: {status}")
                print(f"   📈 整体状态: {execution.get('overall_status', 'N/A')}")
                print(f"   📊 步骤统计: {execution.get('passed_steps', 0)}通过 / {execution.get('failed_steps', 0)}失败")
                print(f"   ⏱️  总耗时: {execution.get('total_duration', 0):.2f}秒")
                
                if execution.get('summary'):
                    print(f"   📝 测试总结: {execution['summary']}")
                
                return execution_id
            else:
                print(f"   ⏳ 执行中... ({wait_count}秒)")
        
        time.sleep(3)
        wait_count += 3
    
    print("   ⏰ 等待超时")
    return execution_id

def demo_execution_details(execution_id):
    """演示执行详情"""
    print_section("执行详情")
    
    # 1. 获取执行记录
    print("1. 执行记录:")
    response = requests.get(f"{BASE_URL}/test-executions/{execution_id}")
    if response.status_code == 200:
        execution = response.json()
        print(f"   📋 执行名称: {execution['execution_name']}")
        print(f"   🕒 开始时间: {execution['started_at']}")
        print(f"   🕒 完成时间: {execution['completed_at']}")
        print(f"   📊 总步骤数: {execution['total_steps']}")
        print(f"   ✅ 通过步骤: {execution['passed_steps']}")
        print(f"   ❌ 失败步骤: {execution['failed_steps']}")
        print(f"   ⏭️  跳过步骤: {execution['skipped_steps']}")
    
    # 2. 获取步骤详情
    print("\n2. 步骤详情:")
    response = requests.get(f"{BASE_URL}/test-executions/{execution_id}/steps")
    if response.status_code == 200:
        steps = response.json()
        print(f"   📋 步骤数量: {len(steps)}")
        for step in steps:
            status_emoji = "✅" if step['status'] == "PASSED" else "❌" if step['status'] == "FAILED" else "⏭️"
            print(f"   {status_emoji} {step['step_order']}: {step['step_name']}")
            print(f"      📝 描述: {step['description']}")
            if step.get('duration_seconds'):
                print(f"      ⏱️  耗时: {step['duration_seconds']:.2f}秒")
            if step.get('error_message'):
                print(f"      ❌ 错误: {step['error_message']}")

def demo_batch_execution():
    """演示批量执行"""
    print_section("批量执行")
    
    # 1. 获取测试用例列表
    response = requests.get(f"{BASE_URL}/test-cases")
    if response.status_code == 200:
        test_cases = response.json()
        active_cases = [case for case in test_cases if case['status'] == 'active']
        
        if len(active_cases) >= 2:
            # 选择前两个活跃的测试用例
            test_case_ids = [active_cases[0]['id'], active_cases[1]['id']]
            
            print(f"1. 选择测试用例: {test_case_ids}")
            for case_id in test_case_ids:
                case = next(c for c in test_cases if c['id'] == case_id)
                print(f"   - {case_id}: {case['name']}")
            
            # 2. 启动批量执行
            print("\n2. 启动批量执行:")
            batch_data = {
                "test_case_ids": test_case_ids,
                "headless": True
            }
            
            response = requests.post(f"{BASE_URL}/test-executions/batch", json=batch_data)
            if response.status_code == 200:
                result = response.json()
                print(f"   ✅ 批量执行启动成功")
                print(f"   📊 总数量: {result['total_count']}")
                print(f"   ⏳ 执行中...")
            else:
                print(f"   ❌ 批量执行启动失败: {response.text}")
        else:
            print("   ⚠️  活跃测试用例不足，跳过批量执行演示")

def demo_statistics():
    """演示统计信息"""
    print_section("统计信息")
    
    response = requests.get(f"{BASE_URL}/statistics")
    if response.status_code == 200:
        stats = response.json()
        print("📊 测试统计概览:")
        print(f"   🧪 总测试用例: {stats['total_test_cases']}")
        print(f"   ✅ 活跃测试用例: {stats['active_test_cases']}")
        print(f"   🚀 总执行次数: {stats['total_executions']}")
        print(f"   ✅ 成功执行: {stats['passed_executions']}")
        print(f"   ❌ 失败执行: {stats['failed_executions']}")
        print(f"   📈 成功率: {stats['success_rate']}%")
        
        # 计算成功率
        if stats['total_executions'] > 0:
            success_rate = (stats['passed_executions'] / stats['total_executions']) * 100
            print(f"   🎯 实际成功率: {success_rate:.1f}%")

def demo_api_documentation():
    """演示API文档"""
    print_section("API文档")
    
    print("📖 API文档地址:")
    print(f"   🔗 Swagger UI: {BASE_URL}/docs")
    print(f"   🔗 ReDoc: {BASE_URL}/redoc")
    print(f"   🔗 OpenAPI JSON: {BASE_URL}/openapi.json")
    
    # 测试OpenAPI文档
    response = requests.get(f"{BASE_URL}/openapi.json")
    if response.status_code == 200:
        openapi = response.json()
        print(f"\n📋 API信息:")
        print(f"   📝 标题: {openapi.get('info', {}).get('title', 'N/A')}")
        print(f"   📄 描述: {openapi.get('info', {}).get('description', 'N/A')}")
        print(f"   🔢 版本: {openapi.get('info', {}).get('version', 'N/A')}")
        print(f"   🛣️  路径数量: {len(openapi.get('paths', {}))}")

def main():
    """主演示函数"""
    print_header("AutoTest Web自动化测试工具 - 完整功能演示")
    print(f"🕒 演示开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 1. 健康检查
    if not demo_health_check():
        print("❌ 服务不可用，演示终止")
        return
    
    # 2. 测试用例管理
    test_case_id = demo_test_case_management()
    
    if test_case_id:
        # 3. 测试执行
        execution_id = demo_test_execution(test_case_id)
        
        if execution_id:
            # 4. 执行详情
            demo_execution_details(execution_id)
    
    # 5. 批量执行
    demo_batch_execution()
    
    # 6. 统计信息
    demo_statistics()
    
    # 7. API文档
    demo_api_documentation()
    
    print_header("演示完成")
    print(f"🕒 演示结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("🎉 感谢使用AutoTest Web自动化测试工具！")
    print("\n💡 提示:")
    print("   - 访问 http://localhost:8000/docs 查看完整API文档")
    print("   - 使用API创建和管理更多测试用例")
    print("   - 支持批量执行和实时监控")

if __name__ == "__main__":
    main() 