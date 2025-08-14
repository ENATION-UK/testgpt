"""
LLM服务模块
"""

import json
import os
import re
import pandas as pd
from typing import List, Dict, Any

from browser_use.llm.messages import SystemMessage, UserMessage, ContentPartTextParam

from ..config_manager import ConfigManager
from .excel_utils import convert_excel_to_test_cases
from .multi_llm_service import MultiLLMService

class LLMService:
    """LLM服务类"""
    
    @staticmethod
    def _load_model_config() -> dict:
        """加载模型配置"""
        try:
            config_manager = ConfigManager()
            config_path = config_manager.get_multi_model_config_path()
            if config_path.exists():
                with open(config_path, "r", encoding="utf-8") as f:
                    config = json.load(f)
            else:
                # 默认配置
                config = {
                    "model_type": "deepseek",
                    "api_key": os.getenv("DEEPSEEK_API_KEY", ""),
                    "base_url": "https://api.deepseek.com/v1",
                    "model": "deepseek-chat",
                    "temperature": 0.7,
                    "max_tokens": None
                }
            return config
        except Exception as e:
            print(f"加载模型配置失败: {e}")
            # 返回默认配置
            return {
                "model_type": "deepseek",
                "api_key": os.getenv("DEEPSEEK_API_KEY", ""),
                "base_url": "https://api.deepseek.com/v1",
                "model": "deepseek-chat",
                "temperature": 0.7,
                "max_tokens": None
            }

    @staticmethod
    async def analyze_excel_with_llm(df: pd.DataFrame, import_options: dict) -> List[dict]:
        """使用大模型分析Excel内容并转换为测试用例格式"""
        try:
            # 使用多模型服务
            multi_llm_service = MultiLLMService()
            
            # 检查配置有效性
            config_response = await multi_llm_service.get_multi_model_config()
            if not config_response.is_valid:
                print("警告: 多模型配置无效，使用备用转换逻辑")
                return convert_excel_to_test_cases(df, import_options)

            # 将DataFrame转换为字符串格式
            excel_content = df.to_string(index=False)
            
            # 构建提示词
            prompt = f"""
请分析以下Excel表格内容，并将其转换为测试用例格式。

Excel内容：
{excel_content}

导入选项：
- 默认状态: {import_options.get('defaultStatus', 'active')}
- 默认优先级: {import_options.get('defaultPriority', 'medium')}
- 默认分类: {import_options.get('defaultCategory', '导入')}

请将Excel中的每一行转换为一个测试用例，格式如下：
{{
    "name": "测试用例名称",
    "description": "测试用例描述",
    "task_content": "具体的测试任务内容",
    "status": "active/inactive/draft",
    "priority": "low/medium/high/critical",
    "category": "分类名称",
    "tags": ["标签1", "标签2"],
    "expected_result": "期望结果"
}}

请返回JSON格式的测试用例列表，每个测试用例包含上述所有字段。
如果Excel中没有某些字段，请使用导入选项中的默认值。
"""
            print("即将发送给大模型的提示词如下：")
            print(prompt)

            # 创建消息
            messages = [
                SystemMessage(content=[ContentPartTextParam(text="你是一个测试用例分析专家")]),
                UserMessage(content=prompt)
            ]
            
            print("🚀 调用多模型服务...")
            llm_response = await multi_llm_service.chat_completion(messages)
            
            # 解析响应
            try:
                # 尝试从响应中提取JSON
                json_match = re.search(r'\[.*\]', llm_response, re.DOTALL)
                if json_match:
                    test_cases = json.loads(json_match.group())
                else:
                    # 如果无法解析JSON，使用简单的转换逻辑
                    test_cases = convert_excel_to_test_cases(df, import_options)
            except Exception as e:
                print(f"JSON解析失败: {e}")
                # 如果JSON解析失败，使用简单的转换逻辑
                test_cases = convert_excel_to_test_cases(df, import_options)
            
            return test_cases
            
        except Exception as e:
            print(f"大模型分析失败: {e}")
            # 如果大模型分析失败，使用简单的转换逻辑
            return convert_excel_to_test_cases(df, import_options) 