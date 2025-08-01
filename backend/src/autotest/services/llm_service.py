"""
LLM服务模块
"""

import json
import os
import re
import pandas as pd
from typing import List, Dict, Any

from browser_use.llm.deepseek.chat import ChatDeepSeek
from browser_use.llm.messages import SystemMessage, UserMessage, ContentPartTextParam

from ..config_manager import ConfigManager
from .excel_utils import convert_excel_to_test_cases

class LLMService:
    """LLM服务类"""
    
    @staticmethod
    def _load_model_config() -> dict:
        """加载模型配置"""
        try:
            config_manager = ConfigManager()
            config_path = config_manager.get_model_config_path()
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
            # 加载模型配置
            config = LLMService._load_model_config()
            
            # 检查配置有效性
            if not config.get("api_key"):
                print("警告: 模型配置中缺少API密钥，使用备用转换逻辑")
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

            # 根据模型类型创建相应的聊天实例
            if config.get("model_type") == "deepseek":
                # 创建DeepSeek聊天实例
                chat_config = {
                    'base_url': config.get('base_url', 'https://api.deepseek.com/v1'),
                    'model': config.get('model', 'deepseek-chat'),
                    'api_key': config.get('api_key'),
                }
                
                # 添加可选参数
                if config.get('temperature') is not None:
                    chat_config['temperature'] = config.get('temperature')
                if config.get('max_tokens') is not None:
                    chat_config['max_tokens'] = config.get('max_tokens')
                
                deepseek_chat = ChatDeepSeek(**chat_config)
                
                messages = [
                    SystemMessage(content=[ContentPartTextParam(text="你是一个测试用例分析专家")]),
                    UserMessage(content=prompt)
                ]
                
                print("🚀 调用大模型...")
                response = await deepseek_chat.ainvoke(messages)
                llm_response = response.completion
                
            else:
                raise Exception(f"暂不支持的模型类型: {config.get('model_type')}")
            
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