"""
重构后的测试执行服务
负责执行测试用例并记录结果
"""

from typing import Dict, Any, List, Optional

# 导入重构后的模块
from .executors.test_executor import TestExecutor
from .executors.batch_executor import BatchTestExecutor
from .executors.executor_manager import BatchExecutorManager
from .core.task_context import task_context
from .services.history_service import HistoryService

# 导入核心模块
from .core.time_utils import beijing_now, ensure_timezone_aware
from .core.models import TestStepResult, ControllerTestResult, TestResult
from .constants.prompts import TEST_SYSTEM_PROMPT

# 便捷函数
async def execute_single_test(test_case_id: int, headless: bool = False, execution_id: Optional[int] = None) -> Dict[str, Any]:
    """执行单个测试用例的便捷函数"""
    executor = TestExecutor()
    return await executor.execute_test_case(test_case_id, headless, execution_id=execution_id)

async def execute_multiple_tests(test_case_ids: List[int], headless: bool = False) -> Dict[str, Any]:
    """批量执行测试用例的便捷函数"""
    executor = TestExecutor()
    return await executor.execute_test_suite(test_case_ids, headless)

async def execute_batch_tests(test_case_ids: List[int], headless: bool = False, batch_name: str = "批量执行任务") -> Dict[str, Any]:
    """批量执行测试用例的便捷函数"""
    batch_executor = BatchTestExecutor(max_concurrent=5)
    return await batch_executor.execute_batch_test(test_case_ids, headless, batch_name)

# 全局实例
batch_executor_manager = BatchExecutorManager()
