"""
结果解析服务模块
"""
import logging
from typing import Dict, Any

from ..core.models import TestResult

class ResultParserService:
    """结果解析服务"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def parse_test_result(self, history) -> Dict[str, Any]:
        """解析测试结果"""
        test_result_data = {}
        
        # 输出history对象的JSON格式
        import json
        try:
            history_json = json.dumps(history, default=str, indent=2, ensure_ascii=False)
            self.logger.info(f"🔍 History对象JSON: {history_json}")
        except Exception as e:
            self.logger.info(f"🔍 History对象无法转换为JSON: {e}")
            self.logger.info(f"🔍 History对象类型: {type(history)}")
            self.logger.info(f"🔍 History对象内容: {history}")
        
        final_result = history.final_result() if hasattr(history, 'final_result') else None
        self.logger.info(f"🔍 最终结果: {final_result}")
        
        # 如果final_result()返回None，尝试从history列表中获取最后一个步骤的结果
        if not final_result and isinstance(history, list) and len(history) > 0:
            last_step = history[-1]
            self.logger.info(f"🔍 最后一步: {last_step}")
            
            # 检查最后一步是否包含extracted_content
            if hasattr(last_step, 'extracted_content') and last_step.extracted_content:
                try:
                    # 尝试解析extracted_content中的JSON
                    extracted_json = json.loads(last_step.extracted_content)
                    if isinstance(extracted_json, dict) and 'test_name' in extracted_json:
                        final_result = last_step.extracted_content
                        self.logger.info(f"🔍 从最后一步提取到结果: {final_result}")
                except (json.JSONDecodeError, AttributeError) as e:
                    self.logger.info(f"🔍 最后一步extracted_content不是有效JSON: {e}")
        
        if final_result:
            try:
                # 解析测试结果
                test_result = TestResult.model_validate_json(final_result)
                self.logger.info("✅ 成功解析测试结果:")
                self.logger.info(f"  测试名称: {test_result.test_name}")
                self.logger.info(f"  整体状态: {test_result.overall_status}")
                self.logger.info(f"  总步骤数: {test_result.total_steps}")
                self.logger.info(f"  通过步骤: {test_result.passed_steps}")
                self.logger.info(f"  失败步骤: {test_result.failed_steps}")
                self.logger.info(f"  跳过步骤: {test_result.skipped_steps}")
                self.logger.info(f"  总执行时间: {test_result.total_duration}秒")
                self.logger.info(f"  测试总结: {test_result.summary}")
                self.logger.info(f"  改进建议: {test_result.recommendations}")
                
                # 根据解析后的test_result对象判断测试结果
                test_result_data = {
                    "success": test_result.overall_status == "PASSED",
                    "overall_status": test_result.overall_status,
                    "total_steps": test_result.total_steps,
                    "passed_steps": test_result.passed_steps,
                    "failed_steps": test_result.failed_steps,
                    "skipped_steps": test_result.skipped_steps,
                    "total_duration": test_result.total_duration,
                    "summary": test_result.summary,
                    "recommendations": test_result.recommendations
                }
                
            except Exception as e:
                self.logger.error(f"❌ 解析测试结果失败: {e}")
                self.logger.info("📋 原始结果:")
                self.logger.info(final_result)
                # 使用默认的测试结果数据
                test_result_data = self._get_default_failed_result(f"解析测试结果失败: {str(e)}")
        else:
            self.logger.warning("❌ 没有获得测试结果")
            # 检查是否有详细的分析信息可以输出
            if hasattr(history, 'action_names'):
                self.logger.info("📋 执行的动作:")
                for action in history.action_names():
                    self.logger.info(f"  - {action}")
            
            if hasattr(history, 'errors') and history.errors():
                self.logger.info("🚨 执行错误:")
                for error in history.errors():
                    if error:
                        self.logger.info(f"  - {error}")
            
            # 使用默认的测试结果数据
            test_result_data = self._get_default_failed_result("没有获得测试结果")
        
        return test_result_data
    
    def _get_default_failed_result(self, summary: str) -> Dict[str, Any]:
        """获取默认的失败结果"""
        return {
            "success": False,
            "overall_status": "FAILED",
            "total_steps": 0,
            "passed_steps": 0,
            "failed_steps": 0,
            "skipped_steps": 0,
            "total_duration": 0,
            "summary": summary,
            "recommendations": None
        }
