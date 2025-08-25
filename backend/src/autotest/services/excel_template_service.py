"""
Excel模版服务
提供标准Excel模版生成和解析功能
"""

import pandas as pd
import tempfile
from pathlib import Path
from typing import List, Dict, Any
from fastapi import HTTPException
from fastapi.responses import FileResponse

class ExcelTemplateService:
    """Excel模版服务类"""
    
    # 标准模版字段定义
    STANDARD_TEMPLATE_COLUMNS = [
        "测试用例名称",
        "测试步骤",
        "预期结果",
        "优先级",
        "分类",
        "标签",
        "状态"
    ]
    
    # 字段说明
    COLUMN_DESCRIPTIONS = {
        "测试用例名称": "必填，测试用例的名称标题",
        "测试步骤": "必填，具体的测试执行步骤",
        "预期结果": "必填，期望的测试结果",
        "优先级": "可选，支持：low/medium/high/critical，默认medium",
        "分类": "可选，测试用例分类，默认'导入'",
        "标签": "可选，多个标签用逗号分隔，如：登录功能,核心流程",
        "状态": "可选，支持：active/inactive/draft，默认active"
    }
    
    # 示例数据
    SAMPLE_DATA = [
        {
            "测试用例名称": "用户登录功能测试",
            "测试步骤": "1. 打开登录页面\n2. 输入正确的用户名和密码\n3. 点击登录按钮\n4. 验证跳转到首页",
            "预期结果": "用户成功登录并跳转到系统首页",
            "优先级": "high",
            "分类": "用户管理",
            "标签": "登录功能,用户验证",
            "状态": "active"
        },
        {
            "测试用例名称": "商品搜索功能测试",
            "测试步骤": "1. 在搜索框输入商品关键词\n2. 点击搜索按钮\n3. 查看搜索结果",
            "预期结果": "显示包含关键词的相关商品列表",
            "优先级": "medium",
            "分类": "商品管理",
            "标签": "搜索功能,商品查询",
            "状态": "active"
        },
        {
            "测试用例名称": "订单创建功能测试",
            "测试步骤": "1. 选择商品加入购物车\n2. 进入结算页面\n3. 填写收货信息\n4. 选择支付方式\n5. 提交订单",
            "预期结果": "订单创建成功，生成订单号",
            "优先级": "critical",
            "分类": "订单管理",
            "标签": "订单创建,支付流程",
            "状态": "active"
        }
    ]
    
    @classmethod
    def generate_template_file(cls) -> str:
        """生成标准Excel模版文件"""
        try:
            # 创建临时文件
            temp_dir = Path(tempfile.gettempdir()) / "autotest_templates"
            temp_dir.mkdir(exist_ok=True)
            template_path = temp_dir / "测试用例导入标准模版.xlsx"
            
            # 创建Excel工作簿
            with pd.ExcelWriter(template_path, engine='openpyxl') as writer:
                # 第一个工作表：模版说明
                instructions_data = []
                instructions_data.append(["AutoTest 测试用例导入标准模版", ""])
                instructions_data.append(["", ""])
                instructions_data.append(["使用说明：", ""])
                instructions_data.append(["1. 请在'测试用例数据'工作表中填写您的测试用例", ""])
                instructions_data.append(["2. 红色标记的列为必填项，其他为可选项", ""])
                instructions_data.append(["3. 请参考示例数据的格式进行填写", ""])
                instructions_data.append(["4. 保存后上传此文件即可导入", ""])
                instructions_data.append(["", ""])
                instructions_data.append(["字段说明：", ""])
                
                for col, desc in cls.COLUMN_DESCRIPTIONS.items():
                    instructions_data.append([col, desc])
                
                instructions_df = pd.DataFrame(instructions_data, columns=["项目", "说明"])
                instructions_df.to_excel(writer, sheet_name="使用说明", index=False)
                
                # 第二个工作表：标准模版（空白）
                template_df = pd.DataFrame(columns=cls.STANDARD_TEMPLATE_COLUMNS)
                template_df.to_excel(writer, sheet_name="测试用例数据", index=False)
                
                # 第三个工作表：示例数据
                sample_df = pd.DataFrame(cls.SAMPLE_DATA)
                sample_df.to_excel(writer, sheet_name="示例数据", index=False)
            
            return str(template_path)
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"生成模版文件失败: {str(e)}")
    
    @classmethod
    def parse_standard_template(cls, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """解析标准模版Excel文件"""
        try:
            test_cases = []
            
            # 验证必要的列是否存在
            required_columns = ["测试用例名称", "测试步骤", "预期结果"]
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                raise ValueError(f"缺少必需的列: {', '.join(missing_columns)}")
            
            for index, row in df.iterrows():
                # 跳过空行
                if pd.isna(row["测试用例名称"]) or str(row["测试用例名称"]).strip() == "":
                    continue
                
                # 验证必填字段
                if pd.isna(row["测试步骤"]) or str(row["测试步骤"]).strip() == "":
                    raise ValueError(f"第{index + 2}行：测试步骤不能为空")
                
                if pd.isna(row["预期结果"]) or str(row["预期结果"]).strip() == "":
                    raise ValueError(f"第{index + 2}行：预期结果不能为空")
                
                # 处理标签（转换为列表）
                tags = []
                if not pd.isna(row.get("标签", "")):
                    tag_str = str(row["标签"]).strip()
                    if tag_str:
                        tags = [tag.strip() for tag in tag_str.split(",") if tag.strip()]
                
                # 处理优先级
                priority = str(row.get("优先级", "medium")).lower()
                if priority not in ["low", "medium", "high", "critical"]:
                    priority = "medium"
                
                # 处理状态
                status = str(row.get("状态", "active")).lower()
                if status not in ["active", "inactive", "draft"]:
                    status = "active"
                
                # 构建测试用例对象
                test_case = {
                    "name": str(row["测试用例名称"]).strip(),
                    "task_content": str(row["测试步骤"]).strip(),
                    "expected_result": str(row["预期结果"]).strip(),
                    "priority": priority,
                    "category": str(row.get("分类", "导入")).strip() if not pd.isna(row.get("分类")) else "导入",
                    "tags": tags,
                    "status": status
                }
                
                test_cases.append(test_case)
            
            if not test_cases:
                raise ValueError("没有找到有效的测试用例数据")
            
            return test_cases
            
        except Exception as e:
            raise ValueError(f"解析标准模版失败: {str(e)}")
    
    @classmethod
    def is_standard_template(cls, df: pd.DataFrame) -> bool:
        """检测是否为标准模版格式"""
        try:
            # 检查是否包含标准模版的关键列
            key_columns = ["测试用例名称", "测试步骤", "预期结果"]
            return all(col in df.columns for col in key_columns)
        except:
            return False