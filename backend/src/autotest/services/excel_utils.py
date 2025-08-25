"""
Excel工具模块
"""

import pandas as pd
from typing import List, Dict, Any

def convert_excel_to_test_cases(df: pd.DataFrame, import_options: dict) -> List[dict]:
    """智能的Excel到测试用例转换逻辑"""
    test_cases = []
    
    for _, row in df.iterrows():
        # 智能识别列名并提取信息
        name = str(row.get('标题', row.get('name', row.get('名称', row.get('Name', f'测试用例_{len(test_cases) + 1}')))))
        task_content = str(row.get('步骤描述', row.get('task_content', row.get('任务内容', row.get('Task', row.get('内容', ''))))))
        expected_result = str(row.get('预期结果', row.get('expected_result', row.get('期望结果', row.get('Expected Result', '')))))
        
        # 根据内容智能判断分类
        category = import_options.get('defaultCategory', '导入')
        if '组合商品' in name or '组合商品' in task_content:
            category = '组合商品功能'
        elif '会员' in name or '会员' in task_content:
            category = '会员管理'
        elif '首页' in name or '首页' in task_content:
            category = '首页功能'
        elif '分类' in name or '分类' in task_content:
            category = '分类管理'
        
        # 根据内容智能判断优先级
        priority = import_options.get('defaultPriority', 'medium')
        if any(keyword in name.lower() for keyword in ['紧急', '重要', '核心', 'critical']):
            priority = 'critical'
        elif any(keyword in name.lower() for keyword in ['高', 'high']):
            priority = 'high'
        elif any(keyword in name.lower() for keyword in ['低', 'low']):
            priority = 'low'
        
        # 根据内容智能判断状态
        status = import_options.get('defaultStatus', 'active')
        if any(keyword in name.lower() for keyword in ['草稿', 'draft']):
            status = 'draft'
        elif any(keyword in name.lower() for keyword in ['非激活', 'inactive']):
            status = 'inactive'
        
        # 生成标签
        tags = []
        if '登录' in task_content:
            tags.append('登录功能')
        if '搜索' in task_content:
            tags.append('搜索功能')
        if '审核' in task_content:
            tags.append('审核功能')
        if '发布' in task_content:
            tags.append('发布功能')
        if '编辑' in task_content:
            tags.append('编辑功能')
        if '删除' in task_content:
            tags.append('删除功能')
        
        test_case = {
            "name": name,
            "task_content": task_content,
            "status": status,
            "priority": priority,
            "category": category,
            "tags": tags,
            "expected_result": expected_result
        }
        
        test_cases.append(test_case)
    
    return test_cases 