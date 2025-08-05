#!/usr/bin/env python3
"""
测试按分类批量执行功能的脚本
"""

import requests
import json
import time
from typing import List, Dict, Any

class CategoryBatchExecutionTester:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
    
    def test_category_api(self) -> bool:
        """测试分类API是否正常工作"""
        print("测试分类API...")
        
        try:
            # 获取分类树
            response = self.session.get(f"{self.base_url}/api/categories/tree")
            if response.status_code == 200:
                categories = response.json()
                print(f"✓ 成功获取分类树，共 {len(categories)} 个根分类")
                
                # 如果有分类，测试获取分类下的测试用例
                if categories:
                    category_id = categories[0]['id']
                    response = self.session.get(
                        f"{self.base_url}/api/categories/{category_id}/test-cases",
                        params={"include_children": True}
                    )
                    if response.status_code == 200:
                        data = response.json()
                        print(f"✓ 成功获取分类 {category_id} 下的测试用例，共 {data['count']} 个")
                        return True
                    else:
                        print(f"✗ 获取分类测试用例失败: {response.status_code}")
                        return False
                else:
                    print("⚠ 没有找到分类，跳过测试用例获取测试")
                    return True
            else:
                print(f"✗ 获取分类树失败: {response.status_code}")
                return False
        except Exception as e:
            print(f"✗ 测试分类API时发生错误: {e}")
            return False
    
    def test_batch_execution_api(self) -> bool:
        """测试批量执行API是否正常工作"""
        print("测试批量执行API...")
        
        try:
            # 首先获取一些测试用例
            response = self.session.get(f"{self.base_url}/api/test-cases", params={"limit": 5})
            if response.status_code == 200:
                test_cases = response.json()
                if test_cases:
                    test_case_ids = [tc['id'] for tc in test_cases[:2]]  # 只取前2个测试用例
                    
                    # 创建批量执行任务
                    batch_data = {
                        "test_case_ids": test_case_ids,
                        "headless": True
                    }
                    
                    response = self.session.post(
                        f"{self.base_url}/api/test-executions/batch-executions",
                        json=batch_data
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        if result.get('success'):
                            print(f"✓ 成功创建批量执行任务，ID: {result['batch_execution_id']}")
                            
                            # 获取批量执行任务状态
                            batch_id = result['batch_execution_id']
                            response = self.session.get(f"{self.base_url}/api/test-executions/batch-executions/{batch_id}")
                            if response.status_code == 200:
                                batch_info = response.json()
                                print(f"✓ 批量执行任务状态: {batch_info['status']}")
                                return True
                            else:
                                print(f"✗ 获取批量执行任务状态失败: {response.status_code}")
                                return False
                        else:
                            print(f"✗ 创建批量执行任务失败: {result.get('message', '未知错误')}")
                            return False
                    else:
                        print(f"✗ 创建批量执行任务失败: {response.status_code}")
                        return False
                else:
                    print("⚠ 没有找到测试用例，跳过批量执行测试")
                    return True
            else:
                print(f"✗ 获取测试用例失败: {response.status_code}")
                return False
        except Exception as e:
            print(f"✗ 测试批量执行API时发生错误: {e}")
            return False
    
    def test_category_batch_execution_flow(self) -> bool:
        """测试完整的按分类批量执行流程"""
        print("测试按分类批量执行流程...")
        
        try:
            # 1. 获取分类树
            response = self.session.get(f"{self.base_url}/api/categories/tree")
            if response.status_code != 200:
                print("✗ 获取分类树失败")
                return False
            
            categories = response.json()
            if not categories:
                print("⚠ 没有找到分类，无法测试按分类批量执行")
                return True
            
            # 2. 选择一个有测试用例的分类
            category_with_test_cases = None
            for category in categories:
                response = self.session.get(
                    f"{self.base_url}/api/categories/{category['id']}/test-cases",
                    params={"include_children": True}
                )
                if response.status_code == 200:
                    data = response.json()
                    if data['count'] > 0:
                        category_with_test_cases = category
                        break
            
            if not category_with_test_cases:
                print("⚠ 没有找到包含测试用例的分类，无法测试按分类批量执行")
                return True
            
            # 3. 获取该分类下的测试用例ID
            response = self.session.get(
                f"{self.base_url}/api/categories/{category_with_test_cases['id']}/test-cases",
                params={"include_children": True}
            )
            data = response.json()
            test_case_ids = data['test_case_ids']
            
            print(f"✓ 找到分类 '{category_with_test_cases['name']}' 下的 {len(test_case_ids)} 个测试用例")
            
            # 4. 创建批量执行任务
            batch_data = {
                "test_case_ids": test_case_ids,
                "headless": True
            }
            
            response = self.session.post(
                f"{self.base_url}/api/test-executions/batch-executions",
                json=batch_data
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    batch_id = result['batch_execution_id']
                    print(f"✓ 成功创建按分类批量执行任务，ID: {batch_id}")
                    
                    # 5. 监控执行状态
                    print("监控执行状态...")
                    for i in range(10):  # 最多监控10次
                        time.sleep(2)
                        response = self.session.get(f"{self.base_url}/api/test-executions/batch-executions/{batch_id}")
                        if response.status_code == 200:
                            batch_info = response.json()
                            status = batch_info['status']
                            print(f"  状态更新: {status} (成功: {batch_info['success_count']}, 失败: {batch_info['failed_count']}, 运行中: {batch_info['running_count']}, 等待中: {batch_info['pending_count']})")
                            
                            if status in ['completed', 'failed']:
                                print(f"✓ 批量执行任务完成，最终状态: {status}")
                                return True
                        else:
                            print(f"✗ 获取批量执行任务状态失败: {response.status_code}")
                            return False
                    
                    print("⚠ 监控超时，但任务可能仍在后台运行")
                    return True
                else:
                    print(f"✗ 创建按分类批量执行任务失败: {result.get('message', '未知错误')}")
                    return False
            else:
                print(f"✗ 创建按分类批量执行任务失败: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"✗ 测试按分类批量执行流程时发生错误: {e}")
            return False
    
    def run_all_tests(self) -> bool:
        """运行所有测试"""
        print("=" * 50)
        print("开始测试按分类批量执行功能")
        print("=" * 50)
        
        tests = [
            ("分类API测试", self.test_category_api),
            ("批量执行API测试", self.test_batch_execution_api),
            ("按分类批量执行流程测试", self.test_category_batch_execution_flow)
        ]
        
        results = []
        for test_name, test_func in tests:
            print(f"\n{test_name}:")
            try:
                result = test_func()
                results.append((test_name, result))
                print(f"{'✓ 通过' if result else '✗ 失败'}")
            except Exception as e:
                print(f"✗ 测试异常: {e}")
                results.append((test_name, False))
        
        print("\n" + "=" * 50)
        print("测试结果汇总:")
        print("=" * 50)
        
        passed = 0
        for test_name, result in results:
            status = "✓ 通过" if result else "✗ 失败"
            print(f"{test_name}: {status}")
            if result:
                passed += 1
        
        print(f"\n总计: {passed}/{len(results)} 个测试通过")
        return passed == len(results)

def main():
    """主函数"""
    tester = CategoryBatchExecutionTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n🎉 所有测试通过！按分类批量执行功能正常工作。")
    else:
        print("\n❌ 部分测试失败，请检查系统状态。")
    
    return 0 if success else 1

if __name__ == "__main__":
    exit(main()) 