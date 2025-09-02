"""
测试执行服务
负责执行测试用例并记录结果
"""

import asyncio
import base64
import json
import logging
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional, Set
from pydantic import BaseModel, Field

# 设置时区为北京时间
BEIJING_TZ = timezone(timedelta(hours=8))

def beijing_now():
    """获取北京时间"""
    return datetime.now(BEIJING_TZ)

def ensure_timezone_aware(dt):
    """确保 datetime 对象有时区信息"""
    if dt is None:
        return None
    if dt.tzinfo is None:
        # 如果没有时区信息，假设是北京时间
        return dt.replace(tzinfo=BEIJING_TZ)
    return dt

# from browser_use.tools.service import Controller  # 新版本不再需要Controller
from browser_use.browser.profile import BrowserProfile
from .services.multi_llm_service import MultiLLMService
from playwright.async_api import async_playwright

from .database import TestCase, TestExecution, TestStep, SessionLocal, BatchExecution, BatchExecutionTestCase
from .websocket_manager import websocket_manager
from .browser_event_collector import event_manager, BrowserUseEventCollector

# 任务上下文管理类
class TaskContext:
    """任务上下文管理类，用于维护正在运行的任务和浏览器对象"""
    
    def __init__(self):
        # 批量任务ID -> 批量任务执行器实例
        self._batch_executors: Dict[int, 'BatchTestExecutor'] = {}
        # 批量任务ID -> 该任务下的所有测试用例ID集合
        self._batch_test_cases: Dict[int, Set[int]] = {}
        # 测试用例ID -> 浏览器对象
        self._test_case_browsers: Dict[int, Any] = {}
        # 测试用例ID -> 对应的任务
        self._test_case_tasks: Dict[int, asyncio.Task] = {}
        # 测试用例ID -> 所属的批量任务ID
        self._test_case_batch_mapping: Dict[int, int] = {}
        # 锁，用于保护并发访问
        self._lock = asyncio.Lock()
    
    async def register_batch_executor(self, batch_execution_id: int, executor: 'BatchTestExecutor'):
        """注册批量任务执行器"""
        async with self._lock:
            self._batch_executors[batch_execution_id] = executor
            self._batch_test_cases[batch_execution_id] = set()
            logging.info(f"注册批量任务执行器: {batch_execution_id}")
            logging.info(f"当前批量任务执行器: {list(self._batch_executors.keys())}")
            logging.info(f"当前批量任务测试用例映射: {self._batch_test_cases}")
    
    async def unregister_batch_executor(self, batch_execution_id: int):
        """注销批量任务执行器"""
        logging.info(f"=== 开始注销批量任务执行器: {batch_execution_id} ===")
        try:
            async with self._lock:
                logging.info(f"步骤1: 获取锁成功，开始注销批量任务执行器: {batch_execution_id}")
                logging.info(f"注销前状态:")
                logging.info(f"  - 批量任务 {batch_execution_id} 在执行器中: {batch_execution_id in self._batch_executors}")
                logging.info(f"  - 批量任务 {batch_execution_id} 在测试用例映射中: {batch_execution_id in self._batch_test_cases}")
                
                logging.info(f"步骤2: 从执行器上下文中移除批量任务: {batch_execution_id}")
                if batch_execution_id in self._batch_executors:
                    del self._batch_executors[batch_execution_id]
                    logging.info(f"步骤2完成: 已从执行器上下文中移除批量任务: {batch_execution_id}")
                else:
                    logging.info(f"步骤2完成: 批量任务 {batch_execution_id} 不在执行器上下文中")
                
                logging.info(f"步骤3: 从测试用例映射中移除批量任务: {batch_execution_id}")
                if batch_execution_id in self._batch_test_cases:
                    del self._batch_test_cases[batch_execution_id]
                    logging.info(f"步骤3完成: 已从测试用例映射中移除批量任务: {batch_execution_id}")
                else:
                    logging.info(f"步骤3完成: 批量任务 {batch_execution_id} 不在测试用例映射中")
                
                logging.info(f"步骤4: 注销批量任务执行器: {batch_execution_id} 完成")
                logging.info(f"注销后状态:")
                logging.info(f"  - 剩余批量任务执行器: {list(self._batch_executors.keys())}")
                logging.info(f"  - 剩余批量任务测试用例映射: {self._batch_test_cases}")
        except Exception as e:
            logging.error(f"注销批量任务执行器 {batch_execution_id} 时出错: {e}")
            logging.error(f"错误详情: {type(e).__name__}: {str(e)}")
            import traceback
            logging.error(f"错误堆栈: {traceback.format_exc()}")
            raise
        finally:
            logging.info(f"=== 注销批量任务执行器: {batch_execution_id} 结束 ===")
    
    async def register_test_case(self, batch_execution_id: int, test_case_id: int, browser: Any, task: asyncio.Task):
        """注册测试用例的执行上下文"""
        async with self._lock:
            self._batch_test_cases[batch_execution_id].add(test_case_id)
            self._test_case_browsers[test_case_id] = browser
            self._test_case_tasks[test_case_id] = task
            self._test_case_batch_mapping[test_case_id] = batch_execution_id
            logging.info(f"注册测试用例: {test_case_id} -> 批量任务: {batch_execution_id}")
            logging.info(f"当前任务上下文状态:")
            logging.info(f"  - 批量任务 {batch_execution_id} 下的测试用例: {self._batch_test_cases[batch_execution_id]}")
            logging.info(f"  - 所有测试用例浏览器: {list(self._test_case_browsers.keys())}")
            logging.info(f"  - 所有测试用例任务: {list(self._test_case_tasks.keys())}")
            logging.info(f"  - 测试用例到批量任务的映射: {self._test_case_batch_mapping}")
    
    async def unregister_test_case(self, test_case_id: int):
        """注销测试用例的执行上下文"""
        logging.info(f"=== 开始注销测试用例: {test_case_id} ===")
        try:
            async with self._lock:
                logging.info(f"步骤1: 获取锁成功，开始注销测试用例: {test_case_id}")
                logging.info(f"注销前状态:")
                logging.info(f"  - 测试用例 {test_case_id} 在浏览器中: {test_case_id in self._test_case_browsers}")
                logging.info(f"  - 测试用例 {test_case_id} 在任务中: {test_case_id in self._test_case_tasks}")
                logging.info(f"  - 测试用例 {test_case_id} 在批量任务映射中: {test_case_id in self._test_case_batch_mapping}")
                
                logging.info(f"步骤2: 从浏览器上下文中移除测试用例: {test_case_id}")
                if test_case_id in self._test_case_browsers:
                    del self._test_case_browsers[test_case_id]
                    logging.info(f"步骤2完成: 已从浏览器上下文中移除测试用例: {test_case_id}")
                else:
                    logging.info(f"步骤2完成: 测试用例 {test_case_id} 不在浏览器上下文中")
                
                logging.info(f"步骤3: 从任务上下文中移除测试用例: {test_case_id}")
                if test_case_id in self._test_case_tasks:
                    del self._test_case_tasks[test_case_id]
                    logging.info(f"步骤3完成: 已从任务上下文中移除测试用例: {test_case_id}")
                else:
                    logging.info(f"步骤3完成: 测试用例 {test_case_id} 不在任务上下文中")
                
                # 从批量任务中移除
                logging.info(f"步骤4: 从批量任务中移除测试用例: {test_case_id}")
                batch_execution_id = self._test_case_batch_mapping.get(test_case_id)
                logging.info(f"步骤4a: 获取到批量任务ID: {batch_execution_id}")
                if batch_execution_id and batch_execution_id in self._batch_test_cases:
                    self._batch_test_cases[batch_execution_id].discard(test_case_id)
                    logging.info(f"步骤4b: 已从批量任务 {batch_execution_id} 中移除测试用例: {test_case_id}")
                else:
                    logging.info(f"步骤4b: 批量任务 {batch_execution_id} 不在映射中或不存在")
                
                logging.info(f"步骤5: 移除测试用例 {test_case_id} 的批量任务映射")
                if test_case_id in self._test_case_batch_mapping:
                    del self._test_case_batch_mapping[test_case_id]
                    logging.info(f"步骤5完成: 已移除测试用例 {test_case_id} 的批量任务映射")
                else:
                    logging.info(f"步骤5完成: 测试用例 {test_case_id} 不在批量任务映射中")
                
                logging.info(f"步骤6: 注销测试用例: {test_case_id} 完成")
        except Exception as e:
            logging.error(f"注销测试用例 {test_case_id} 时出错: {e}")
            logging.error(f"错误详情: {type(e).__name__}: {str(e)}")
            import traceback
            logging.error(f"错误堆栈: {traceback.format_exc()}")
            raise
        finally:
            logging.info(f"=== 注销测试用例: {test_case_id} 结束 ===")
    
    async def cancel_batch_execution(self, batch_execution_id: int) -> bool:
        """取消批量执行任务"""
        # 先获取锁，收集需要处理的数据
        test_case_ids = []
        cancelled_count = 0
        
        async with self._lock:
            if batch_execution_id not in self._batch_executors:
                logging.warning(f"批量任务 {batch_execution_id} 不存在")
                return False
            
            logging.info(f"开始取消批量任务: {batch_execution_id}")
            
            # 获取该批量任务下的所有测试用例
            test_case_ids = self._batch_test_cases.get(batch_execution_id, set()).copy()
            logging.info(f"批量任务 {batch_execution_id} 下共有 {len(test_case_ids)} 个测试用例: {test_case_ids}")
        
        # 释放锁后，先取消所有相关的测试用例任务和关闭浏览器，但不立即注销
        for test_case_id in test_case_ids:
            logging.info(f"正在取消测试用例 {test_case_id}...")
            if await self._cancel_test_case_without_unregister(test_case_id):
                cancelled_count += 1
                logging.info(f"测试用例 {test_case_id} 取消成功")
            else:
                logging.warning(f"测试用例 {test_case_id} 取消失败")
        
        # 现在统一注销所有测试用例（这些方法会自己获取锁）
        logging.info(f"开始统一注销所有测试用例...")
        for test_case_id in test_case_ids:
            await self.unregister_test_case(test_case_id)
        
        # 注销批量任务执行器（这个方法会自己获取锁）
        await self.unregister_batch_executor(batch_execution_id)
        
        logging.info(f"批量任务 {batch_execution_id} 已取消，共取消 {cancelled_count} 个测试用例")
        return True
    
    async def _cancel_test_case(self, test_case_id: int) -> bool:
        """取消单个测试用例（包含注销）"""
        try:
            logging.info(f"开始取消测试用例 {test_case_id}...")
            logging.info(f"测试用例 {test_case_id} 的任务状态: {test_case_id in self._test_case_tasks}")
            logging.info(f"测试用例 {test_case_id} 的浏览器状态: {test_case_id in self._test_case_browsers}")
            
            # 取消任务
            if test_case_id in self._test_case_tasks:
                task = self._test_case_tasks[test_case_id]
                logging.info(f"测试用例 {test_case_id} 的任务状态: done={task.done()}, cancelled={task.cancelled()}")
                if not task.done():
                    task.cancel()
                    logging.info(f"已取消测试用例 {test_case_id} 的任务")
                else:
                    logging.info(f"测试用例 {test_case_id} 的任务已完成，无需取消")
            else:
                logging.warning(f"测试用例 {test_case_id} 的任务不在任务上下文中")
            
            # 关闭浏览器
            if test_case_id in self._test_case_browsers:
                browser = self._test_case_browsers[test_case_id]
                logging.info(f"正在关闭测试用例 {test_case_id} 的浏览器...")
                try:
                    await browser.close()
                    logging.info(f"已关闭测试用例 {test_case_id} 的浏览器")
                except Exception as e:
                    logging.warning(f"关闭测试用例 {test_case_id} 的浏览器时出错: {e}")
            else:
                logging.warning(f"测试用例 {test_case_id} 的浏览器不在任务上下文中")
            
            # 注销测试用例
            await self.unregister_test_case(test_case_id)
            logging.info(f"测试用例 {test_case_id} 已从任务上下文中注销")
            return True
            
        except Exception as e:
            logging.error(f"取消测试用例 {test_case_id} 时出错: {e}")
            return False
    
    async def _cancel_test_case_without_unregister(self, test_case_id: int) -> bool:
        """取消单个测试用例（不包含注销，仅取消任务和关闭浏览器）"""
        try:
            logging.info(f"开始取消测试用例 {test_case_id}（不注销）...")
            logging.info(f"测试用例 {test_case_id} 的任务状态: {test_case_id in self._test_case_tasks}")
            logging.info(f"测试用例 {test_case_id} 的浏览器状态: {test_case_id in self._test_case_browsers}")
            
            # 取消任务
            if test_case_id in self._test_case_tasks:
                task = self._test_case_tasks[test_case_id]
                logging.info(f"测试用例 {test_case_id} 的任务状态: done={task.done()}, cancelled={task.cancelled()}")
                if not task.done():
                    task.cancel()
                    logging.info(f"已取消测试用例 {test_case_id} 的任务")
                else:
                    logging.info(f"测试用例 {test_case_id} 的任务已完成，无需取消")
            else:
                logging.warning(f"测试用例 {test_case_id} 的任务不在任务上下文中")
            
            # 关闭浏览器
            if test_case_id in self._test_case_browsers:
                browser = self._test_case_browsers[test_case_id]
                logging.info(f"正在关闭测试用例 {test_case_id} 的浏览器...")
                try:
                    await browser.close()
                    logging.info(f"已关闭测试用例 {test_case_id} 的浏览器")
                except Exception as e:
                    logging.warning(f"关闭测试用例 {test_case_id} 的浏览器时出错: {e}")
            else:
                logging.warning(f"测试用例 {test_case_id} 的浏览器不在任务上下文中")
            
            logging.info(f"测试用例 {test_case_id} 取消完成（未注销）")
            return True
            
        except Exception as e:
            logging.error(f"取消测试用例 {test_case_id} 时出错: {e}")
            return False
    
    def get_batch_executor(self, batch_execution_id: int) -> Optional['BatchTestExecutor']:
        """获取批量任务执行器"""
        return self._batch_executors.get(batch_execution_id)
    
    def is_batch_registered(self, batch_execution_id: int) -> bool:
        """检查批量任务是否已注册"""
        return batch_execution_id in self._batch_executors
    
    def get_test_case_count(self, batch_execution_id: int) -> int:
        """获取批量任务下的测试用例数量"""
        return len(self._batch_test_cases.get(batch_execution_id, set()))
    
    def get_all_batch_ids(self) -> List[int]:
        """获取所有已注册的批量任务ID"""
        return list(self._batch_executors.keys())

# 全局任务上下文管理器
task_context = TaskContext()

# 测试结果模型
class TestStepResult(BaseModel):
    """单个测试步骤的结果"""
    step_name: str = Field(description="测试步骤名称")
    status: str = Field(description="测试状态: PASSED, FAILED, SKIPPED")
    description: str = Field(description="步骤描述")
    error_message: Optional[str] = Field(default=None, description="如果失败，错误信息")
    screenshot_path: Optional[str] = Field(default=None, description="相关截图路径")
    duration_seconds: Optional[float] = Field(default=None, description="执行时间")

# 为Controller创建的简化TestResult模型，不包含test_steps
class ControllerTestResult(BaseModel):
    """用于Controller的简化测试结果模型"""
    test_name: str = Field(description="测试名称")
    overall_status: str = Field(description="整体测试状态: PASSED, FAILED, PARTIAL")
    total_steps: int = Field(description="总步骤数")
    passed_steps: int = Field(description="通过的步骤数")
    failed_steps: int = Field(description="失败的步骤数")
    skipped_steps: int = Field(description="跳过的步骤数")
    total_duration: float = Field(description="总执行时间(秒)")
    summary: str = Field(description="测试总结")
    recommendations: Optional[str] = Field(default=None, description="改进建议")

class TestResult(BaseModel):
    """完整的测试结果"""
    test_name: str = Field(description="测试名称")
    overall_status: str = Field(description="整体测试状态: PASSED, FAILED, PARTIAL")
    total_steps: int = Field(description="总步骤数")
    passed_steps: int = Field(description="通过的步骤数")
    failed_steps: int = Field(description="失败的步骤数")
    skipped_steps: int = Field(description="跳过的步骤数")
    total_duration: float = Field(description="总执行时间(秒)")
    # 移除test_steps字段，因为我们现在使用事件机制收集步骤
    # test_steps: List[TestStepResult] = Field(description="详细的测试步骤")
    summary: str = Field(description="测试总结")
    recommendations: Optional[str] = Field(default=None, description="改进建议")

# 测试系统提示词
TEST_SYSTEM_PROMPT = """
你是一个专业的Web自动化测试专家。你的任务是执行Web测试并生成详细的测试报告。

## 测试执行规则：
1. 严格按照测试用例执行每个步骤
2. 每个步骤都要验证预期结果
3. 如果步骤失败，记录详细的错误信息
4. 为每个关键步骤截图作为证据
5. 记录每个步骤的执行时间

## 测试结果要求：
1. 必须明确标注每个步骤的PASSED/FAILED状态
2. 失败时必须提供具体的错误原因
3. 提供清晰的测试总结
4. 如果有失败，给出改进建议

## 故障处理指南：
重要: 如果你多次（连续 3 次及以上失败）未能成功执行同一操作，调用 done 并将 success 设置为 false，同时说明问题所在。
1.如果某个操作反复失败（出现相同的错误模式），不要无限重试。
2.对同一操作尝试 2 - 3 次失败后，考虑其他方法，或者调用 done 并将 success 设置为 false。
3.在 done 操作文本中记录你尝试了什么以及失败的原因。
4.如果你陷入循环或毫无进展，立即调用 done。

## 验证标准：
- 页面元素存在且可交互
- 功能按预期工作
- 页面状态正确
- 错误处理正常

记住：你的输出必须是结构化的测试报告，包含详细的成功/失败状态和原因分析。
"""

class TestExecutor:
    """测试执行器"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        初始化测试执行器
        
        Args:
            api_key: DeepSeek API密钥（已废弃，现在使用多模型服务）
        """
        # 初始化多模型服务
        self.multi_llm_service = MultiLLMService()
        
        # 初始化测试控制器（新版本使用 output_model_schema）
        self.test_controller = None  # 不再需要 Controller 对象
        
        # 设置日志
        self.logger = logging.getLogger(__name__)
        
        # 初始化配置管理器
        from .config_manager import ConfigManager
        self.config_manager = ConfigManager()
        
        # 设置 history 缓存目录
        self.history_cache_dir = self.config_manager.get_history_directory()
    
    def _load_config(self) -> dict:
        """从配置文件加载模型配置"""
        try:
            from .config_manager import ConfigManager
            config_manager = ConfigManager()
            config_path = config_manager.get_multi_model_config_path()
            if config_path.exists():
                with open(config_path, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception as e:
            self.logger.warning(f"加载配置文件失败: {e}")
        return {}

    async def execute_test_case(self, test_case_id: int, headless: bool = False, batch_execution_id: Optional[int] = None, execution_id: Optional[int] = None) -> Dict[str, Any]:
        """
        执行单个测试用例
        
        Args:
            test_case_id: 测试用例ID
            headless: 是否无头模式
            batch_execution_id: 批量执行任务ID（可选）
            execution_id: 已存在的执行记录ID（可选）
            
        Returns:
            执行结果
        """
        db = SessionLocal()
        try:
            # 获取测试用例
            test_case = db.query(TestCase).filter(
                TestCase.id == test_case_id,
                TestCase.is_deleted == False
            ).first()
            
            if not test_case:
                return {
                    "success": False,
                    "error_message": "测试用例不存在",
                    "execution_id": None
                }
            
            # 如果提供了execution_id，使用现有的执行记录
            if execution_id:
                execution = db.query(TestExecution).filter(TestExecution.id == execution_id).first()
                if not execution:
                    return {
                        "success": False,
                        "error_message": "执行记录不存在",
                        "execution_id": None
                    }
                
                                # 尝试缓存回放
                result = await self._try_cache_replay(test_case, execution, headless, db)
                if result:
                    # 缓存回放成功，更新执行记录并返回
                    execution.status = "passed" if result["success"] else "failed"
                    execution.overall_status = result.get("overall_status", "FAILED")
                    execution.total_duration = result.get("total_duration", 0)
                    execution.summary = result.get("summary", "")
                    execution.recommendations = result.get("recommendations", "")
                    execution.error_message = result.get("error_message", "")
                    execution.completed_at = beijing_now()
                    
                    # 更新统计信息
                    # 使用事件收集器的数据而不是test_steps

                    # 保存浏览器日志和截图
                    execution.browser_logs = result.get("browser_logs", [])
                    execution.screenshots = result.get("screenshots", [])
                    
                    db.commit()
                    
                    # 保存测试步骤
                    # 移除对test_steps的依赖，因为我们现在使用事件机制收集步骤
                    
                    db.commit()
                    
                    return {
                        "success": result["success"],
                        "execution_id": execution.id,
                        "overall_status": result.get("overall_status", "FAILED"),
                        "total_duration": result.get("total_duration", 0),
                        "summary": result.get("summary", ""),
                        "recommendations": result.get("recommendations", ""),
                        "error_message": result.get("error_message", ""),
                        # 移除test_steps，因为我们现在使用事件机制收集步骤
                        # "test_steps": result.get("test_steps", []),
                        "from_history": True
                    }
                
                # 更新执行记录状态为运行中
                execution.status = "running"
                execution.started_at = beijing_now()
                db.commit()
                db.refresh(execution)
            else:
                # 没有execution_id时，创建新的执行记录并尝试缓存回放
                execution = TestExecution(
                    test_case_id=test_case_id,
                    execution_name=f"{test_case.name}_{beijing_now().strftime('%Y%m%d_%H%M%S')}",
                    status="running",
                    started_at=beijing_now()
                )
                db.add(execution)
                db.commit()
                db.refresh(execution)
                
                # 尝试缓存回放
                result = await self._try_cache_replay(test_case, execution, headless, db)
                if result:
                    # 缓存回放成功，更新执行记录并返回
                    execution.status = "passed" if result["success"] else "failed"
                    execution.overall_status = result.get("overall_status", "FAILED")
                    execution.total_duration = result.get("total_duration", 0)
                    execution.summary = result.get("summary", "")
                    execution.recommendations = result.get("recommendations", "")
                    execution.error_message = result.get("error_message", "")
                    execution.completed_at = beijing_now()
                    
                    # 更新统计信息
                    # 使用事件收集器的数据而不是test_steps

                    # 保存浏览器日志和截图
                    execution.browser_logs = result.get("browser_logs", [])
                    execution.screenshots = result.get("screenshots", [])
                    
                    db.commit()
                    
                    # 保存测试步骤
                    # 移除对test_steps的依赖，因为我们现在使用事件机制收集步骤
                    
                    db.commit()
                    
                    return {
                        "success": result["success"],
                        "execution_id": execution.id,
                        "overall_status": result.get("overall_status", "FAILED"),
                        "total_duration": result.get("total_duration", 0),
                        "summary": result.get("summary", ""),
                        "recommendations": result.get("recommendations", ""),
                        "error_message": result.get("error_message", ""),
                        # 移除test_steps，因为我们现在使用事件机制收集步骤
                        # "test_steps": result.get("test_steps", []),
                        "from_history": True
                    }
                
                # 缓存回放失败或无效，继续正常执行
                self.logger.info(f"=== 测试用例 {test_case_id} 的缓存检查完成，开始正常执行 ===")
            
            # 执行浏览器测试
            result = await self._run_browser_test(test_case, execution, headless, batch_execution_id)
            
            # 更新执行记录
            execution.status = "passed" if result["success"] else "failed"
            execution.overall_status = result.get("overall_status", "FAILED")
            execution.total_duration = result.get("total_duration", 0)
            execution.summary = result.get("summary", "")
            execution.recommendations = result.get("recommendations", "")
            execution.error_message = result.get("error_message", "")
            execution.completed_at = beijing_now()
            
            # 更新统计信息
            # 使用事件收集器的数据而不是test_steps
            # 注意：这个event_collector只在_run_browser_test方法中可用
            # 在缓存回放的情况下，我们需要从result中获取统计信息
            if "total_steps" in result:
                execution.total_steps = result.get("total_steps", 0)
                execution.passed_steps = result.get("passed_steps", 0)
                execution.failed_steps = result.get("failed_steps", 0)
                execution.skipped_steps = result.get("skipped_steps", 0)
            else:
                # 默认值
                execution.total_steps = 0
                execution.passed_steps = 0
                execution.failed_steps = 0
                execution.skipped_steps = 0
            
            # 保存浏览器日志和截图
            execution.browser_logs = result.get("browser_logs", [])
            execution.screenshots = result.get("screenshots", [])
            
            db.commit()
            
            # 保存测试步骤到数据库
            # 移除对test_steps的依赖，因为我们现在使用事件机制收集步骤
            
            db.commit()
            
            # 保存 history 到缓存（如果执行成功且有 agent）
            history_path = ""
            if result.get("success") and result.get("agent"):
                history_path = self._save_history_to_cache(test_case_id, result["agent"], db)
            
            return {
                "success": result["success"],
                "execution_id": execution.id,
                "overall_status": result.get("overall_status", "FAILED"),
                "total_duration": result.get("total_duration", 0),
                "summary": result.get("summary", ""),
                "recommendations": result.get("recommendations", ""),
                "error_message": result.get("error_message", ""),
                # 移除test_steps，因为我们现在使用事件机制收集步骤
                # "test_steps": result.get("test_steps", []),
                "history_path": history_path
            }
            
        except Exception as e:
            self.logger.error(f"执行测试用例 {test_case_id} 失败: {e}")
            return {
                "success": False,
                "error_message": str(e),
                "execution_id": None
            }
        finally:
            db.close()
    
    async def execute_test_suite(self, test_case_ids: List[int], headless: bool = False) -> Dict[str, Any]:
        """
        批量执行测试用例
        
        Args:
            test_case_ids: 测试用例ID列表
            headless: 是否无头模式
            
        Returns:
            执行结果
        """
        results = []
        total_count = len(test_case_ids)
        passed_count = 0
        failed_count = 0
        
        for i, test_case_id in enumerate(test_case_ids, 1):
            self.logger.info(f"执行进度: {i}/{total_count} - 测试用例ID: {test_case_id}")
            
            result = await self.execute_test_case(test_case_id, headless)
            results.append(result)
            
            if result["success"]:
                passed_count += 1
            else:
                failed_count += 1
        
        return {
            "success": True,
            "total_count": total_count,
            "passed_count": passed_count,
            "failed_count": failed_count,
            "results": results
        }
    
    async def _run_browser_test(self, test_case: TestCase, execution: TestExecution, headless: bool, batch_execution_id: Optional[int] = None) -> Dict[str, Any]:
        """运行浏览器测试"""
        from playwright.async_api import async_playwright
        import asyncio
        
        # 创建 BrowserProfile 禁用默认扩展
        browser_profile = BrowserProfile(
            enable_default_extensions=False,
            headless=headless
        )
        
        async with async_playwright() as p:
            # 启动浏览器
            browser = await p.chromium.launch(
                headless=headless,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-accelerated-2d-canvas',
                    '--disable-extensions',
                    '--no-first-run',
                    '--no-zygote',
                    '--disable-gpu',
                    '--disable-features=VizDisplayCompositor',
                    '--disable-web-security',
                    '--disable-features=VizDisplayCompositor',
                ]
            )
            
            try:
                # 创建新页面
                page = await browser.new_page()
                
                # 加载自定义提示词
                custom_prompt = self._load_custom_prompt()
                
                # 合并默认提示词和自定义提示词
                final_prompt = TEST_SYSTEM_PROMPT
                if custom_prompt:
                    final_prompt = f"{TEST_SYSTEM_PROMPT}\n\n{custom_prompt}"
                
                # 使用Browser Use Agent
                from browser_use import Agent
                
                # 使用多模型服务创建LLM实例
                config = self.multi_llm_service._load_multi_model_config()
                request_config = await self.multi_llm_service._get_next_available_config_with_wait(config)
                print(f"使用API key:{request_config.model_type}-- {request_config.api_key}")
                
                llm = self.multi_llm_service._create_llm_instance(request_config)
                
                # 创建事件收集器
                event_collector = event_manager.create_collector(test_case.id, execution.id)
                
                agent = Agent(
                    task=f"# 操作步骤\n{test_case.task_content}\n\n# 预期结果:\n{test_case.expected_result}",
                    llm=llm,
                    page=page,
                    use_vision=True,
                    output_model_schema=ControllerTestResult,
                    extend_system_message=final_prompt,
                    browser_profile=browser_profile,
                    llm_timeout=120,    # LLM调用超时时间（秒）
                    step_timeout=300    # 每个步骤的超时时间（秒）
                )
                
                # 注册事件监听器
                agent.eventbus.on('CreateAgentStepEvent', event_collector.collect_step_event)
                agent.eventbus.on('UpdateAgentTaskEvent', event_collector.collect_task_completion)
                agent.eventbus.on('ErrorEvent', event_collector.collect_error_event)
                
                self.logger.info(f"开始执行任务: {test_case.task_content[:100]}...")
                
                start_time = beijing_now()
                
                # 如果是在批量执行中，注册到任务上下文
                if batch_execution_id:
                    # 创建agent执行任务
                    agent_task = asyncio.create_task(agent.run())
                    
                    # 注册到任务上下文
                    await task_context.register_test_case(batch_execution_id, test_case.id, browser, agent_task)
                    
                    try:
                        # 等待agent任务完成
                        history = await agent_task
                        # 添加调试代码：打印agent.run()的结果
                        self.logger.info(f"=== DEBUG: agent.run() 批量执行结果 ===")
                        self.logger.info(f"结果内容: {history}")

                        
                        # 新增代码：解析测试结果
                        test_result = None
                        test_result_data = {}
                        
                        # 获取最终结果
                        final_result = history.final_result() if hasattr(history, 'final_result') else None
                        self.logger.info(f"🔍 最终结果: {final_result}")
                        
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
                                test_result_data = {
                                    "success": False,
                                    "overall_status": "FAILED",
                                    "total_steps": 0,
                                    "passed_steps": 0,
                                    "failed_steps": 0,
                                    "skipped_steps": 0,
                                    "total_duration": 0,
                                    "summary": f"解析测试结果失败: {str(e)}",
                                    "recommendations": None
                                }
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
                            test_result_data = {
                                "success": False,
                                "overall_status": "FAILED",
                                "total_steps": 0,
                                "passed_steps": 0,
                                "failed_steps": 0,
                                "skipped_steps": 0,
                                "total_duration": 0,
                                "summary": "没有获得测试结果",
                                "recommendations": None
                            }
                    except asyncio.CancelledError:
                        self.logger.info(f"测试用例 {test_case.id} 被取消")
                        # 重新抛出取消异常，让上层知道任务被取消
                        raise
                    finally:
                        # 注意：不要在这里注销测试用例，让任务上下文管理浏览器生命周期
                        # 只有在批量任务完成或被取消时，才统一清理
                        pass
                else:
                    # 单个测试执行，直接运行
                    history = await agent.run()
                    # 添加调试代码：打印agent.run()的结果

                    self.logger.info(f"结果内容: {history}")

                    # 新增代码：解析测试结果
                    test_result = None
                    test_result_data = {}
                    
                    # 获取最终结果
                    final_result = history.final_result() if hasattr(history, 'final_result') else None
                    self.logger.info(f"🔍 最终结果: {final_result}")
                    
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
                            test_result_data = {
                                "success": False,
                                "overall_status": "FAILED",
                                "total_steps": 0,
                                "passed_steps": 0,
                                "failed_steps": 0,
                                "skipped_steps": 0,
                                "total_duration": 0,
                                "summary": f"解析测试结果失败: {str(e)}",
                                "recommendations": None
                            }
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
                        test_result_data = {
                            "success": False,
                            "overall_status": "FAILED",
                            "total_steps": 0,
                            "passed_steps": 0,
                            "failed_steps": 0,
                            "skipped_steps": 0,
                            "total_duration": 0,
                            "summary": "没有获得测试结果",
                            "recommendations": None
                        }
                
                end_time = beijing_now()
                total_duration = (end_time - start_time).total_seconds()
                
                # 使用事件收集器生成测试结果（如果之前没有成功解析）
                if not test_result_data.get("success"):
                    event_collector_result = event_collector.convert_to_test_result()
                    
                    # 从agent.run()的结果中获取测试成功状态
                    # 如果agent成功完成任务，则测试成功
                    agent_success = False
                    if hasattr(history, 'is_successful'):
                        agent_success = history.is_successful()
                        # is_successful()可能返回None（未完成），所以需要处理这种情况
                        if agent_success is None:
                            agent_success = False
                    
                    # 如果事件收集器没有获取到成功状态，则使用agent的结果
                    if "success" not in event_collector_result or not event_collector_result["success"]:
                        event_collector_result["success"] = agent_success
                    
                    # 合并结果数据
                    test_result_data = {**event_collector_result, **test_result_data}
                
                # 保存截图
                screenshots = self._save_screenshots(history, execution.id)
                
                # 保存 history 到缓存（如果执行成功且有 agent）
                history_path = ""
                if test_result_data.get("success") and agent:
                    history_path = self._save_history_to_cache(test_case.id, agent, SessionLocal())
                
                # 广播执行完成消息
                await websocket_manager.broadcast_execution_update(
                    execution.id,
                    {
                        "type": "execution_completed",
                        "execution_id": execution.id,
                        "test_case_id": test_case.id,
                        "status": "completed",
                        "success": test_result_data["success"],
                        "overall_status": test_result_data["overall_status"],
                        "total_duration": total_duration,
                        "summary": test_result_data["summary"]
                    }
                )
                
                return {
                    "success": test_result_data["success"],
                    "overall_status": test_result_data["overall_status"],
                    "total_duration": total_duration,
                    "summary": test_result_data["summary"],
                    "recommendations": test_result_data["recommendations"],
                    "screenshots": screenshots,
                    "browser_logs": history.action_names() if hasattr(history, 'action_names') else [],
                    "history": history,
                    "agent": agent,
                    "history_path": history_path
                }
                
            finally:
                # 确保浏览器被关闭
                try:
                    await browser.close()
                except Exception as e:
                    self.logger.warning(f"关闭浏览器时出错: {e}")
    
    def _load_custom_prompt(self) -> str:
        """加载自定义提示词"""
        try:
            from .config_manager import ConfigManager
            config_manager = ConfigManager()
            config_path = config_manager.get_prompt_config_path()
            
            if config_path.exists():
                with open(config_path, "r", encoding="utf-8") as f:
                    config = json.load(f)
                    return config.get("custom_prompt", "")
            return ""
        except Exception as e:
            self.logger.warning(f"加载自定义提示词失败: {e}")
            return ""

            return ""

    def _save_screenshots(self, history, execution_id: int) -> List[str]:
        """保存截图到指定目录"""
        # 处理 ActionResult 列表
        if isinstance(history, list):
            # 从所有 ActionResult 中收集截图
            all_screenshots = []
            for action in history:
                if hasattr(action, 'attachments') and action.attachments:
                    all_screenshots.extend(action.attachments)
                # 也可以从其他属性中提取截图信息
                if hasattr(action, 'extracted_content') and action.extracted_content:
                    # 这里可以解析 extracted_content 中的截图信息
                    pass
            screenshots = all_screenshots
        else:
            # 处理单个对象的情况
            screenshots = history.screenshots() if hasattr(history, 'screenshots') else []
        
        if not screenshots:
            return []
        
        # 创建输出目录
        output_dir = self.config_manager.get_screenshots_directory() / f"execution_{execution_id}"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        saved_paths = []
        timestamp = beijing_now().strftime("%Y%m%d_%H%M%S")
        
        for i, screenshot in enumerate(screenshots):
            if screenshot and isinstance(screenshot, str):
                try:
                    # 如果是base64编码的图片
                    if screenshot.startswith('data:image'):
                        # 提取base64数据
                        header, data = screenshot.split(',', 1)
                        image_data = base64.b64decode(data)
                        
                        # 确定文件扩展名
                        if 'png' in header:
                            ext = 'png'
                        elif 'jpeg' in header or 'jpg' in header:
                            ext = 'jpg'
                        else:
                            ext = 'png'
                        
                        filename = f"screenshot_{timestamp}_{i+1:03d}.{ext}"
                        filepath = output_dir / filename
                        
                        with open(filepath, 'wb') as f:
                            f.write(image_data)
                        
                        saved_paths.append(str(filepath))
                    
                    elif screenshot.startswith('/') or ':' in screenshot:
                        # 如果是文件路径，直接复制
                        source_path = Path(screenshot)
                        if source_path.exists():
                            filename = f"screenshot_{timestamp}_{i+1:03d}{source_path.suffix}"
                            dest_path = output_dir / filename
                            
                            import shutil
                            shutil.copy2(source_path, dest_path)
                            saved_paths.append(str(dest_path))
                
                except Exception as e:
                    self.logger.error(f"保存截图 {i+1} 失败: {e}")
                    continue
        
        return saved_paths

    def _get_history_path(self, test_case_id: int) -> Path:
        """获取测试用例的 history 文件路径"""
        return self.history_cache_dir / f"test_case_{test_case_id}_history.json"
    
    def _get_history_path_from_relative(self, relative_path: str) -> Optional[Path]:
        """根据相对路径获取完整的 history 文件路径"""
        self.logger.info(f"=== 开始解析 history 路径 ===")
        self.logger.info(f"输入的相对路径: {relative_path}")
        self.logger.info(f"配置根目录: {self.config_manager.data_dir}")
        
        if not relative_path:
            self.logger.warning("输入的相对路径为空")
            return None
        
        # 如果已经是绝对路径，直接返回
        if Path(relative_path).is_absolute():
            self.logger.info(f"输入路径已经是绝对路径: {relative_path}")
            return Path(relative_path)
        
        # 如果是相对路径，相对于配置根目录构建完整路径
        full_path = self.config_manager.data_dir / relative_path
        self.logger.info(f"构建的完整路径: {full_path}")
        self.logger.info(f"=== history 路径解析完成 ===")
        return full_path
    
    def _is_history_valid(self, test_case: TestCase) -> bool:
        """检查 history 是否有效"""
        self.logger.info(f"=== 开始验证测试用例 {test_case.id} 的 history 缓存 ===")
        self.logger.info(f"测试用例 {test_case.id} 的 history_path: {test_case.history_path}")
        self.logger.info(f"测试用例 {test_case.id} 的 history_updated_at: {test_case.history_updated_at}")
        
        if not test_case.history_path:
            self.logger.info(f"测试用例 {test_case.id} 没有 history_path，缓存无效")
            return False
        
        # 根据相对路径获取完整路径
        history_path = self._get_history_path_from_relative(test_case.history_path)
        self.logger.info(f"测试用例 {test_case.id} 的完整 history 路径: {history_path}")
        
        if not history_path or not history_path.exists():
            self.logger.warning(f"测试用例 {test_case.id} 的 history 文件不存在或路径无效: {history_path}")
            return False
        
        # 检查文件是否为空或损坏
        try:
            file_size = history_path.stat().st_size
            self.logger.info(f"测试用例 {test_case.id} 的 history 文件大小: {file_size} 字节")
            
            if file_size == 0:
                self.logger.warning(f"测试用例 {test_case.id} 的 history 文件为空")
                return False
            
            # 尝试解析 JSON 文件
            with open(history_path, 'r', encoding='utf-8') as f:
                content = f.read()
                json.loads(content)
                self.logger.info(f"测试用例 {test_case.id} 的 history 文件 JSON 格式验证通过")
            return True
        except Exception as e:
            self.logger.warning(f"测试用例 {test_case.id} 的 history 文件 {history_path} 无效: {e}")
            return False
        finally:
            self.logger.info(f"=== 测试用例 {test_case.id} 的 history 缓存验证完成 ===")
    
    def _should_use_history(self, test_case: TestCase) -> bool:
        """判断是否应该使用 history 缓存"""
        self.logger.info(f"=== 开始判断测试用例 {test_case.id} 是否应该使用 history 缓存 ===")
        
        # 如果没有 history 文件，直接返回 False
        if not self._is_history_valid(test_case):
            self.logger.info(f"测试用例 {test_case.id} 的 history 缓存无效，将重新执行")
            return False
        
        # 检查 history 是否过期（比如超过7天）
        if test_case.history_updated_at:
            from datetime import timedelta
            try:
                # 确保时区一致性
                history_time = ensure_timezone_aware(test_case.history_updated_at)
                current_time = beijing_now()
                time_diff = current_time - history_time
                days_diff = time_diff.days
                
                self.logger.info(f"测试用例 {test_case.id} 的 history 更新时间: {history_time}")
                self.logger.info(f"当前时间: {current_time}")
                self.logger.info(f"时间差: {time_diff} (共 {days_diff} 天)")
                
                if time_diff > timedelta(days=7):
                    self.logger.info(f"测试用例 {test_case.id} 的 history 已过期 ({days_diff} 天 > 7 天)，将重新执行")
                    return False
                else:
                    self.logger.info(f"测试用例 {test_case.id} 的 history 未过期 ({days_diff} 天 <= 7 天)，可以使用缓存")
            except Exception as e:
                self.logger.warning(f"测试用例 {test_case.id} 的 history 时间计算出错: {e}")
                return False
        else:
            self.logger.warning(f"测试用例 {test_case.id} 的 history_updated_at 为空，将重新执行")
            return False
        
        self.logger.info(f"=== 测试用例 {test_case.id} 可以使用 history 缓存 ===")
        return True
    
    async def _try_replay_from_history(self, test_case: TestCase, execution: TestExecution, headless: bool) -> Optional[Dict[str, Any]]:
        """尝试从 history 回放测试"""
        try:
            self.logger.info(f"=== 开始尝试从 history 回放测试用例 {test_case.id} ===")
            self.logger.info(f"测试用例 {test_case.id} 的 history_path: {test_case.history_path}")
            
            # 创建浏览器实例
            from playwright.async_api import async_playwright
            
            # 创建 BrowserProfile 禁用默认扩展
            browser_profile = BrowserProfile(
                enable_default_extensions=False,
                headless=headless
            )
            
            async with async_playwright() as p:
                self.logger.info(f"启动浏览器实例，headless: {headless}")
                browser = await p.chromium.launch(
                    headless=False,
                    args=[
                        '--no-sandbox',
                        '--disable-setuid-sandbox',
                        '--disable-dev-shm-usage',
                        '--disable-extensions',
                        '--disable-accelerated-2d-canvas',
                        '--no-first-run',
                        '--no-zygote',
                        '--disable-gpu',
                        '--disable-features=VizDisplayCompositor',
                        '--disable-web-security',
                        '--disable-background-timer-throttling',
                        '--disable-backgrounding-occluded-windows',
                        '--disable-renderer-backgrounding',
                        '--disable-features=TranslateUI',
                        '--disable-ipc-flooding-protection'
                    ]
                )
                
                try:
                    page = await browser.new_page()
                    self.logger.info("浏览器页面创建成功")
                    
                    # 使用多模型服务创建LLM实例
                    self.logger.info("开始创建LLM实例...")
                    config = self.multi_llm_service._load_multi_model_config()
                    request_config = await self.multi_llm_service._get_next_available_config_with_wait(config)
                    
                    llm = self.multi_llm_service._create_llm_instance(request_config)
                    self.logger.info("LLM实例创建成功")
                    
                    # 创建增强的 Agent 并尝试回放
                    self.logger.info("开始创建增强Agent实例...")
                    # from .enhanced_agent import create_enhanced_agent_with_collector  # 模块不存在，暂时注释
                    
                    # 创建带事件收集器的增强 Agent
                    # agent = create_enhanced_agent_with_collector(  # 模块不存在，暂时注释
                    #     test_case_id=test_case.id,
                    #     execution_id=execution.id,
                    #     task=f"# 操作步骤\n{test_case.task_content}\n\n# 预期结果:\n{test_case.expected_result}",
                    #     llm=llm,
                    #     page=page,
                    #     use_vision=True,
                    #     output_model_schema=ControllerTestResult,
                    #     extend_system_message=TEST_SYSTEM_PROMPT,
                    #     browser_profile=browser_profile,
                    # )
                    # self.logger.info("增强Agent实例创建成功")
                    
                    # 暂时跳过增强Agent功能，直接返回None
                    self.logger.warning("增强Agent模块不存在，跳过history回放功能")
                    return None
                    
                    start_time = beijing_now()
                    
                    # 尝试从 history 回放
                    try:
                        # 根据相对路径获取完整路径
                        self.logger.info(f"解析 history 文件路径...")
                        full_history_path = self._get_history_path_from_relative(test_case.history_path)
                        self.logger.info(f"解析后的完整 history 路径: {full_history_path}")
                        
                        if not full_history_path:
                            self.logger.warning(f"无法解析 history 路径: {test_case.history_path}")
                            return None
                        
                        if not full_history_path.exists():
                            self.logger.warning(f"History 文件不存在: {full_history_path}")
                            return None
                        
                        self.logger.info(f"开始调用增强的 agent.load_and_rerun_with_events() 进行回放...")
                        # 使用增强的 agent.load_and_rerun_with_events() 方法回放，支持事件监听
                        history_result = await agent.load_and_rerun_with_events(
                            str(full_history_path),
                            max_retries=3,
                            skip_failures=True,
                            delay_between_actions=2.0
                        )
                        self.logger.info(f"agent.load_and_rerun_with_events() 调用完成，返回结果类型: {type(history_result)}")
                        
                        if history_result:
                            self.logger.info(f"回放返回结果长度: {len(history_result) if isinstance(history_result, list) else 'N/A'}")
                        else:
                            self.logger.warning("回放返回结果为空")
                        
                        print("重放结果：")
                        print(history_result)
                        end_time = beijing_now()
                        total_duration = (end_time - start_time).total_seconds()
                        self.logger.info(f"回放总耗时: {total_duration} 秒")
                        
                        # 解析回放结果
                        if history_result and isinstance(history_result, list) and len(history_result) > 0:
                            try:
                                self.logger.info("开始解析回放结果...")
                                # 查找最后一个 ActionResult，它应该包含最终的测试结果
                                final_action = None
                                for action in reversed(history_result):
                                    if hasattr(action, 'is_done') and action.is_done:
                                        final_action = action
                                        break
                                
                                if final_action and final_action.extracted_content:
                                    self.logger.info("找到包含最终结果的 ActionResult")
                                    # 尝试解析 extracted_content 中的 JSON 数据
                                    try:
                                        # 查找 JSON 格式的测试结果
                                        import json
                                        import re
                                        
                                        # 使用正则表达式查找 JSON 数据
                                        json_match = re.search(r'\{.*\}', final_action.extracted_content, re.DOTALL)
                                        if json_match:
                                            json_str = json_match.group()
                                            self.logger.info(f"从 extracted_content 中提取到 JSON 数据: {json_str[:200]}...")
                                            test_result = TestResult.model_validate_json(json_str)
                                            
                                            # 保存截图
                                            screenshots = self._save_screenshots(history_result, execution.id)
                                            
                                            self.logger.info(f"✅ 从 history 回放测试用例 {test_case.id} 成功")
                                            
                                            return {
                                                "success": test_result.overall_status == "PASSED",
                                                "overall_status": test_result.overall_status,
                                                "total_duration": total_duration,
                                                "summary": test_result.summary,
                                                "recommendations": test_result.recommendations,
                                                "screenshots": screenshots,
                                                "browser_logs": [action.extracted_content for action in history_result if action.extracted_content],
                                                "from_history": True
                                            }
                                        else:
                                            self.logger.warning(f"在 extracted_content 中未找到 JSON 格式的测试结果")
                                            return None
                                            
                                    except Exception as e:
                                        self.logger.warning(f"解析 extracted_content 中的 JSON 失败: {e}")
                                        return None
                                else:
                                    self.logger.warning(f"未找到包含最终结果的 ActionResult")
                                    return None
                                    
                            except Exception as e:
                                self.logger.warning(f"解析回放结果失败: {e}")
                                return None
                        else:
                            self.logger.warning(f"回放没有返回有效结果")
                            return None
                            
                    except Exception as e:
                        self.logger.warning(f"从 history 回放失败: {e}")
                        import traceback
                        self.logger.warning(f"回放失败详细错误: {traceback.format_exc()}")
                        return None
                        
                finally:
                    # 确保浏览器被关闭
                    try:
                        await browser.close()
                    except Exception as e:
                        self.logger.warning(f"关闭浏览器时出错: {e}")
                        
        except Exception as e:
            self.logger.error(f"从 history 回放测试用例 {test_case.id} 失败: {e}")
            import traceback
            self.logger.error(f"回放失败详细错误: {traceback.format_exc()}")
            return None
        finally:
            self.logger.info(f"=== 测试用例 {test_case.id} 的 history 回放尝试完成 ===")
    
    async def _try_cache_replay(self, test_case: TestCase, execution: TestExecution, headless: bool, db) -> Optional[Dict[str, Any]]:
        """
        尝试缓存回放的抽象方法
        
        Args:
            test_case: 测试用例
            execution: 执行记录
            headless: 是否无头模式
            db: 数据库会话
            
        Returns:
            回放结果，如果失败返回None
        """
        self.logger.info(f"=== 开始检查测试用例 {test_case.id} 是否可以使用 history 缓存 ===")
        
        if not self._should_use_history(test_case):
            self.logger.info(f"❌ 测试用例 {test_case.id} 不能使用 history 缓存，将重新执行")
            return None
        
        self.logger.info(f"✅ 测试用例 {test_case.id} 使用 history 缓存")
        
        # 尝试从 history 回放
        self.logger.info(f"开始尝试从 history 回放测试用例 {test_case.id}")
        result = await self._try_replay_from_history(test_case, execution, headless)
        
        if result:
            self.logger.info(f"✅ 从 history 回放测试用例 {test_case.id} 成功")
            return result
        else:
            # 如果回放失败，使 history 失效
            self.logger.warning(f"❌ 从 history 回放失败，将重新执行测试用例 {test_case.id}")
            self._invalidate_history(test_case.id, db)
            return None
    
    def _save_history_to_cache(self, test_case_id: int, agent, db) -> str:
        """保存 history 到缓存并更新数据库"""
        try:
            self.logger.info(f"=== 开始保存测试用例 {test_case_id} 的 history 到缓存 ===")
            
            # 生成 history 文件路径
            history_path = self._get_history_path(test_case_id)
            self.logger.info(f"生成的 history 文件路径: {history_path}")
            
            # 使用 agent.save_history() 方法保存，这是正确的方式
            self.logger.info("开始调用 agent.save_history() 保存历史记录...")
            agent.save_history(str(history_path))
            self.logger.info("agent.save_history() 调用完成")
            
            # 将绝对路径转换为相对路径（相对于配置根目录）
            relative_path = f"history/test_case_{test_case_id}_history.json"
            self.logger.info(f"转换后的相对路径: {relative_path}")
            
            # 更新数据库中的 history 路径和时间
            test_case = db.query(TestCase).filter(TestCase.id == test_case_id).first()
            if test_case:
                test_case.history_path = relative_path
                test_case.history_updated_at = beijing_now()
                db.commit()
                self.logger.info(f"✅ 已保存测试用例 {test_case_id} 的 history 到 {relative_path}")
                self.logger.info(f"数据库更新时间: {test_case.history_updated_at}")
            else:
                self.logger.warning(f"未找到测试用例 {test_case_id}，无法更新数据库")
            
            self.logger.info(f"=== 测试用例 {test_case_id} 的 history 缓存保存完成 ===")
            return relative_path
        except Exception as e:
            self.logger.error(f"保存 history 失败: {e}")
            import traceback
            self.logger.error(f"保存 history 详细错误: {traceback.format_exc()}")
            return ""
    
    def _invalidate_history(self, test_case_id: int, db) -> None:
        """使 history 失效"""
        try:
            self.logger.info(f"=== 开始使测试用例 {test_case_id} 的 history 失效 ===")
            test_case = db.query(TestCase).filter(TestCase.id == test_case_id).first()
            if test_case:
                old_history_path = test_case.history_path
                old_updated_at = test_case.history_updated_at
                
                test_case.history_path = None
                test_case.history_updated_at = None
                db.commit()
                
                self.logger.info(f"✅ 已使测试用例 {test_case_id} 的 history 失效")
                self.logger.info(f"原 history_path: {old_history_path}")
                self.logger.info(f"原 history_updated_at: {old_updated_at}")
            else:
                self.logger.warning(f"未找到测试用例 {test_case_id}，无法使 history 失效")
        except Exception as e:
            self.logger.error(f"使 history 失效失败: {e}")
            import traceback
            self.logger.error(f"使 history 失效详细错误: {traceback.format_exc()}")
        finally:
            self.logger.info(f"=== 测试用例 {test_case_id} 的 history 失效操作完成 ===")
    
    def force_refresh_history(self, test_case_id: int) -> bool:
        """强制刷新指定测试用例的 history 缓存"""
        try:
            self.logger.info(f"=== 开始强制刷新测试用例 {test_case_id} 的 history 缓存 ===")
            db = SessionLocal()
            try:
                test_case = db.query(TestCase).filter(TestCase.id == test_case_id).first()
                if test_case:
                    self.logger.info(f"找到测试用例 {test_case_id}，当前 history_path: {test_case.history_path}")
                    self.logger.info(f"当前 history_updated_at: {test_case.history_updated_at}")
                    
                    self._invalidate_history(test_case_id, db)
                    self.logger.info(f"✅ 已强制刷新测试用例 {test_case_id} 的 history 缓存")
                    return True
                else:
                    self.logger.warning(f"测试用例 {test_case_id} 不存在")
                    return False
            finally:
                db.close()
        except Exception as e:
            self.logger.error(f"强制刷新 history 缓存失败: {e}")
            import traceback
            self.logger.error(f"强制刷新 history 缓存详细错误: {traceback.format_exc()}")
            return False
        finally:
            self.logger.info(f"=== 测试用例 {test_case_id} 的 history 缓存强制刷新操作完成 ===")
    
    def cleanup_expired_history(self, max_days: int = 30) -> int:
        """清理过期的 history 文件"""
        try:
            self.logger.info(f"=== 开始清理过期的 history 文件，最大保留天数: {max_days} ===")
            db = SessionLocal()
            try:
                from datetime import timedelta
                cutoff_date = beijing_now() - timedelta(days=max_days)
                self.logger.info(f"清理截止日期: {cutoff_date}")
                
                # 查找过期的测试用例
                expired_test_cases = db.query(TestCase).filter(
                    TestCase.history_path.isnot(None),
                    TestCase.history_updated_at < cutoff_date
                ).all()
                
                self.logger.info(f"找到 {len(expired_test_cases)} 个过期的测试用例")
                
                cleaned_count = 0
                for test_case in expired_test_cases:
                    try:
                        self.logger.info(f"清理测试用例 {test_case.id} 的过期 history")
                        self.logger.info(f"history_path: {test_case.history_path}")
                        self.logger.info(f"history_updated_at: {test_case.history_updated_at}")
                        
                        # 删除文件
                        full_history_path = self._get_history_path_from_relative(test_case.history_path)
                        if full_history_path and full_history_path.exists():
                            full_history_path.unlink()
                            self.logger.info(f"已删除过期文件: {full_history_path}")
                        
                        # 更新数据库
                        test_case.history_path = None
                        test_case.history_updated_at = None
                        cleaned_count += 1
                        
                        self.logger.info(f"✅ 已清理过期的 history 文件: {test_case.history_path}")
                    except Exception as e:
                        self.logger.warning(f"清理 history 文件失败 {test_case.history_path}: {e}")
                
                db.commit()
                self.logger.info(f"=== 过期 history 文件清理完成，共清理 {cleaned_count} 个 ===")
                return cleaned_count
                
            finally:
                db.close()
        except Exception as e:
            self.logger.error(f"清理过期的 history 文件失败: {e}")
            import traceback
            self.logger.error(f"清理过期 history 文件详细错误: {traceback.format_exc()}")
            return 0
    
    def get_history_stats(self) -> Dict[str, Any]:
        """获取 history 缓存统计信息"""
        try:
            db = SessionLocal()
            try:
                total_cases = db.query(TestCase).filter(TestCase.is_deleted == False).count()
                cached_cases = db.query(TestCase).filter(
                    TestCase.history_path.isnot(None),
                    TestCase.is_deleted == False
                ).count()
                
                # 获取缓存大小
                cache_size = 0
                if self.history_cache_dir.exists():
                    for file_path in self.history_cache_dir.glob("*.json"):
                        cache_size += file_path.stat().st_size
                
                return {
                    "total_cases": total_cases,
                    "cached_cases": cached_cases,
                    "cache_hit_rate": (cached_cases / total_cases * 100) if total_cases > 0 else 0,
                    "cache_size_bytes": cache_size,
                    "cache_size_mb": round(cache_size / (1024 * 1024), 2)
                }
            finally:
                db.close()
        except Exception as e:
            self.logger.error(f"获取 history 统计信息失败: {e}")
            return {}

class BatchTestExecutor:
    """批量测试执行器"""
    
    def __init__(self, api_key: Optional[str] = None, max_concurrent: int = 5):
        """
        初始化批量测试执行器
        
        Args:
            api_key: DeepSeek API密钥
            max_concurrent: 最大并发执行数量，默认为5
        """
        self.test_executor = TestExecutor(api_key)
        self.max_concurrent = max_concurrent
        self.logger = logging.getLogger(__name__)
        self.batch_execution_id = None  # 当前批量任务的ID
    
    async def register_to_context(self, batch_execution_id: int):
        """注册到任务上下文"""
        self.logger.info(f"开始注册批量执行器到任务上下文: {batch_execution_id}")
        self.batch_execution_id = batch_execution_id
        await task_context.register_batch_executor(batch_execution_id, self)
        self.logger.info(f"批量执行器已注册到任务上下文: {batch_execution_id}")
    
    async def unregister_from_context(self):
        """从任务上下文注销"""
        if self.batch_execution_id:
            self.logger.info(f"开始从任务上下文注销批量执行器: {self.batch_execution_id}")
            await task_context.unregister_batch_executor(self.batch_execution_id)
            self.batch_execution_id = None
            self.logger.info("批量执行器已从任务上下文注销")
        else:
            self.logger.warning("批量执行器未注册到任务上下文，无法注销")
    
    async def execute_batch_test(self, test_case_ids: List[int], headless: bool = False, batch_name: str = "批量执行任务", batch_execution_id: Optional[int] = None) -> Dict[str, Any]:
        """
        执行批量测试用例
        
        Args:
            test_case_ids: 测试用例ID列表
            headless: 是否无头模式
            batch_name: 批量执行任务名称
            batch_execution_id: 可选的批量执行任务ID，如果提供则使用现有的任务
            
        Returns:
            执行结果
        """
        db = SessionLocal()
        try:
            if batch_execution_id is not None:
                # 使用现有的批量执行任务
                batch_execution = db.query(BatchExecution).filter(BatchExecution.id == batch_execution_id).first()
                if not batch_execution:
                    raise ValueError(f"批量执行任务 {batch_execution_id} 不存在")
                
                # 检查是否已经有测试用例记录
                existing_test_cases = db.query(BatchExecutionTestCase).filter(
                    BatchExecutionTestCase.batch_execution_id == batch_execution_id
                ).all()
                
                if not existing_test_cases:
                    # 创建批量执行任务中的测试用例记录
                    batch_test_cases = []
                    for test_case_id in test_case_ids:
                        batch_test_case = BatchExecutionTestCase(
                            batch_execution_id=batch_execution.id,
                            test_case_id=test_case_id,
                            status="pending"
                        )
                        db.add(batch_test_case)
                        batch_test_cases.append(batch_test_case)
                    db.commit()
                else:
                    batch_test_cases = existing_test_cases
            else:
                # 创建新的批量执行任务记录
                batch_execution = BatchExecution(
                    name=batch_name,
                    status="running",
                    total_count=len(test_case_ids),
                    pending_count=len(test_case_ids),
                    started_at=beijing_now()
                )
                db.add(batch_execution)
                db.commit()
                db.refresh(batch_execution)
                
                # 创建批量执行任务中的测试用例记录
                batch_test_cases = []
                for test_case_id in test_case_ids:
                    batch_test_case = BatchExecutionTestCase(
                        batch_execution_id=batch_execution.id,
                        test_case_id=test_case_id,
                        status="pending"
                    )
                    db.add(batch_test_case)
                    batch_test_cases.append(batch_test_case)
                db.commit()
            
            self.logger.info(f"开始批量执行任务: {batch_execution.name} (ID: {batch_execution.id})，最大并发数: {self.max_concurrent}")
            self.logger.info(f"批量任务 {batch_execution.id} 下的测试用例数量: {len(batch_test_cases)}")
            
            # 注册到任务上下文
            self.logger.info(f"正在注册批量执行器 {batch_execution.id} 到任务上下文...")
            await self.register_to_context(batch_execution.id)
            self.logger.info(f"批量执行器 {batch_execution.id} 已成功注册到任务上下文")
            
            try:
                # 使用信号量控制并发执行测试用例
                semaphore = asyncio.Semaphore(self.max_concurrent)
                
                async def execute_with_semaphore(batch_test_case):
                    async with semaphore:
                        self.logger.info(f"开始执行测试用例 {batch_test_case.test_case_id} (当前并发数: {self.max_concurrent - semaphore._value})")
                        try:
                            result = await self._execute_single_test_in_batch(batch_test_case, headless, db)
                            self.logger.info(f"完成执行测试用例 {batch_test_case.test_case_id}")
                            return result
                        except asyncio.CancelledError:
                            self.logger.info(f"测试用例 {batch_test_case.test_case_id} 被取消")
                            # 重新抛出取消异常
                            raise
                        except Exception as e:
                            self.logger.error(f"执行测试用例 {batch_test_case.test_case_id} 时发生异常: {e}")
                            raise
                
                # 创建所有任务
                tasks = []
                self.logger.info(f"开始创建任务，测试用例数量: {len(batch_test_cases)}")
                for batch_test_case in batch_test_cases:
                    # 只为pending状态的用例创建任务
                    if batch_test_case.status != "pending":
                        continue
                    
                    self.logger.info(f"创建任务 for 测试用例 {batch_test_case.test_case_id}")
                    task = asyncio.create_task(execute_with_semaphore(batch_test_case))
                    tasks.append(task)
                
                self.logger.info(f"创建了 {len(tasks)} 个任务")
                
                # 等待所有任务完成
                if tasks:
                    try:
                        # 等待所有任务完成，包括被取消的任务
                        done, pending = await asyncio.wait(tasks, return_when=asyncio.ALL_COMPLETED)
                        
                        # 处理被取消的任务
                        for task in done:
                            try:
                                await task
                            except asyncio.CancelledError:
                                self.logger.info("检测到被取消的任务")
                            except Exception as e:
                                self.logger.error(f"任务执行异常: {e}")
                        
                    except Exception as e:
                        self.logger.error(f"批量执行任务 {batch_execution.id} 执行过程中发生异常: {e}")
                
                # 检查任务是否被取消（通过任务上下文检查）
                if not task_context.is_batch_registered(batch_execution.id):
                    self.logger.info(f"批量执行任务 {batch_execution.id} 已被取消")
                    # 更新任务状态为已取消
                    batch_execution.status = "cancelled"
                    batch_execution.completed_at = beijing_now()
                    batch_execution.updated_at = beijing_now()
                    db.commit()
                    
                    # 推送 WebSocket 更新
                    await websocket_manager.broadcast_batch_update(
                        batch_execution.id,
                        {
                            "status": batch_execution.status,
                            "success_count": batch_execution.success_count,
                            "failed_count": batch_execution.failed_count,
                            "running_count": batch_execution.running_count,
                            "pending_count": batch_execution.pending_count,
                            "total_count": batch_execution.total_count,
                            "completed_at": batch_execution.completed_at.isoformat() if batch_execution.completed_at else None,
                            "updated_at": batch_execution.updated_at.isoformat() if batch_execution.updated_at else None
                        }
                    )
                    
                    return {
                        "success": False,
                        "batch_execution_id": batch_execution.id,
                        "batch_name": batch_execution.name,
                        "status": "cancelled",
                        "message": "批量执行任务已被取消"
                    }
            finally:
                # 从任务上下文中注销
                await self.unregister_from_context()
            
            # 更新批量执行任务状态为完成
            batch_execution.status = "completed"
            batch_execution.completed_at = beijing_now()
            batch_execution.updated_at = beijing_now()
            
            # 统计执行结果
            success_count = db.query(BatchExecutionTestCase).filter(
                BatchExecutionTestCase.batch_execution_id == batch_execution.id,
                BatchExecutionTestCase.status == "completed"
            ).count()
            
            failed_count = db.query(BatchExecutionTestCase).filter(
                BatchExecutionTestCase.batch_execution_id == batch_execution.id,
                BatchExecutionTestCase.status == "failed"
            ).count()
            
            batch_execution.success_count = success_count
            batch_execution.failed_count = failed_count
            batch_execution.running_count = 0
            batch_execution.pending_count = 0
            
            db.commit()
            
            # 推送批量执行任务完成通知
            await websocket_manager.broadcast_batch_update(
                batch_execution.id,
                {
                    "status": batch_execution.status,
                    "success_count": batch_execution.success_count,
                    "failed_count": batch_execution.failed_count,
                    "running_count": batch_execution.running_count,
                    "pending_count": batch_execution.pending_count,
                    "total_count": batch_execution.total_count,
                    "completed_at": batch_execution.completed_at.isoformat() if batch_execution.completed_at else None,
                    "updated_at": batch_execution.updated_at.isoformat() if batch_execution.updated_at else None
                }
            )
            
            return {
                "success": True,
                "batch_execution_id": batch_execution.id,
                "batch_name": batch_execution.name,
                "total_count": batch_execution.total_count,
                "success_count": batch_execution.success_count,
                "failed_count": batch_execution.failed_count,
                "status": batch_execution.status,
                "started_at": batch_execution.started_at.isoformat(),
                "completed_at": batch_execution.completed_at.isoformat() if batch_execution.completed_at else None
            }
            
        except Exception as e:
            self.logger.error(f"批量执行任务失败: {e}")
            # 如果使用了现有的批量执行任务，更新其状态为失败
            if batch_execution_id is not None:
                batch_execution = db.query(BatchExecution).filter(BatchExecution.id == batch_execution_id).first()
                if batch_execution:
                    batch_execution.status = "failed"
                    batch_execution.completed_at = beijing_now()
                    batch_execution.updated_at = beijing_now()
            raise
        finally:
            db.close()
    
    async def _execute_single_test_in_batch(self, batch_test_case: BatchExecutionTestCase, headless: bool, db):
        """
        在批量执行中执行单个测试用例
        
        Args:
            batch_test_case: 批量执行任务中的测试用例记录
            headless: 是否无头模式
            db: 数据库会话
        """
        self.logger.info(f"🔍 [EXECUTION_DEBUG] 开始执行单个测试用例 {batch_test_case.test_case_id}，初始execution_id: {batch_test_case.execution_id}")
        try:
            # 检查任务是否被取消
            if batch_executor_manager.is_batch_cancelled(batch_test_case.batch_execution_id):
                self.logger.info(f"🔍 [EXECUTION_DEBUG] 批量执行任务 {batch_test_case.batch_execution_id} 已被取消，跳过测试用例 {batch_test_case.test_case_id}，execution_id: {batch_test_case.execution_id}")
                batch_test_case.status = "cancelled"
                batch_test_case.completed_at = beijing_now()
                batch_test_case.updated_at = beijing_now()
                db.commit()
                return
            
            # 更新状态为运行中
            batch_test_case.status = "running"
            batch_test_case.started_at = beijing_now()
            batch_test_case.updated_at = beijing_now()
            db.commit()
            self.logger.info(f"🔍 [EXECUTION_DEBUG] 测试用例 {batch_test_case.test_case_id} 已标记为运行中，execution_id: {batch_test_case.execution_id}")
            
            # 再次检查任务是否被取消（在开始执行前）
            if batch_executor_manager.is_batch_cancelled(batch_test_case.batch_execution_id):
                self.logger.info(f"🔍 [EXECUTION_DEBUG] 批量执行任务 {batch_test_case.batch_execution_id} 在执行前被取消，停止测试用例 {batch_test_case.test_case_id}，execution_id: {batch_test_case.execution_id}")
                batch_test_case.status = "cancelled"
                batch_test_case.completed_at = beijing_now()
                batch_test_case.updated_at = beijing_now()
                db.commit()
                return
            
            # 执行测试用例
            self.logger.info(f"🔍 [EXECUTION_DEBUG] 开始执行测试用例 {batch_test_case.test_case_id}，当前execution_id: {batch_test_case.execution_id}")
            try:
                # 为批量执行创建执行记录
                self.logger.info(f"🔍 [EXECUTION_DEBUG] 开始为测试用例 {batch_test_case.test_case_id} 创建执行记录")
                execution = TestExecution(
                    test_case_id=batch_test_case.test_case_id,
                    execution_name=f"批量执行_{beijing_now().strftime('%Y%m%d_%H%M%S')}",
                    status="running",
                    started_at=beijing_now()
                )
                db.add(execution)
                db.commit()
                db.refresh(execution)
                self.logger.info(f"🔍 [EXECUTION_DEBUG] 成功创建执行记录 {execution.id} 给测试用例 {batch_test_case.test_case_id}")
                
                # 更新批量测试用例记录的执行ID
                old_execution_id = batch_test_case.execution_id
                batch_test_case.execution_id = execution.id
                db.commit()
                self.logger.info(f"🔍 [EXECUTION_DEBUG] 测试用例 {batch_test_case.test_case_id} execution_id 从 {old_execution_id} 更新为 {execution.id}")
                
                # 执行测试用例，使用已创建的执行记录
                self.logger.info(f"🔍 [EXECUTION_DEBUG] 开始调用 execute_test_case，测试用例 {batch_test_case.test_case_id}，执行记录 {execution.id}")
                result = await self.test_executor.execute_test_case(
                    batch_test_case.test_case_id, 
                    headless, 
                    batch_test_case.batch_execution_id,
                    execution.id
                )
                self.logger.info(f"🔍 [EXECUTION_DEBUG] execute_test_case 返回结果： {result}")
            except asyncio.CancelledError:
                self.logger.info(f"测试用例 {batch_test_case.test_case_id} 被取消")
                batch_test_case.status = "cancelled"
                batch_test_case.completed_at = beijing_now()
                batch_test_case.updated_at = beijing_now()
                db.commit()
                # 重新抛出取消异常
                raise
            except Exception as e:
                self.logger.error(f"😨 [EXECUTION_DEBUG] 执行测试用例 {batch_test_case.test_case_id} 时发生异常: {e}")
                self.logger.error(f"🔍 [EXECUTION_DEBUG] 异常时的execution_id: {batch_test_case.execution_id}")
                
                # 如果还没有创建执行记录，创建一个简单的失败记录
                if not batch_test_case.execution_id:
                    self.logger.warning(f"🔍 [EXECUTION_DEBUG] 测试用例 {batch_test_case.test_case_id} 在异常时没有execution_id，尝试创建失败记录")
                    try:
                        execution = TestExecution(
                            test_case_id=batch_test_case.test_case_id,
                            execution_name=f"批量执行_失败_{beijing_now().strftime('%Y%m%d_%H%M%S')}",
                            status="failed",
                            overall_status="FAILED",
                            error_message=str(e),
                            started_at=beijing_now(),
                            completed_at=beijing_now(),
                            total_steps=0,
                            passed_steps=0,
                            failed_steps=0,
                            skipped_steps=0,
                            summary=f"测试用例执行失败: {str(e)}",
                            recommendations="请检查测试用例配置或系统环境设置"
                        )
                        db.add(execution)
                        db.commit()
                        db.refresh(execution)
                        
                        batch_test_case.execution_id = execution.id
                        self.logger.info(f"🔍 [EXECUTION_DEBUG] 为失败测试用例 {batch_test_case.test_case_id} 创建了执行记录 {execution.id}")
                    except Exception as create_error:
                        self.logger.error(f"😨 [EXECUTION_DEBUG] 创建失败执行记录失败: {create_error}")
                else:
                    self.logger.info(f"🔍 [EXECUTION_DEBUG] 测试用例 {batch_test_case.test_case_id} 在异常时已经有execution_id: {batch_test_case.execution_id}")
                
                batch_test_case.status = "failed"
                batch_test_case.completed_at = beijing_now()
                batch_test_case.updated_at = beijing_now()
                db.commit()
                return
            
            # 检查任务是否被取消（在执行完成后）
            if batch_executor_manager.is_batch_cancelled(batch_test_case.batch_execution_id):
                self.logger.info(f"批量执行任务 {batch_test_case.batch_execution_id} 已被取消，标记测试用例 {batch_test_case.test_case_id} 为取消")
                batch_test_case.status = "cancelled"
                batch_test_case.completed_at = beijing_now()
                batch_test_case.updated_at = beijing_now()
                db.commit()
                return
            
            # 更新执行记录ID
            self.logger.info(f"🔍 [EXECUTION_DEBUG] 测试用例 {batch_test_case.test_case_id} 执行完成，当前execution_id: {batch_test_case.execution_id}")
            if "execution_id" in result:
                old_id = batch_test_case.execution_id
                batch_test_case.execution_id = result["execution_id"]
                self.logger.info(f"🔍 [EXECUTION_DEBUG] 从结果中更新execution_id: {old_id} -> {result['execution_id']}")
            else:
                self.logger.warning(f"🔍 [EXECUTION_DEBUG] 结果中没有execution_id，保持原有值: {batch_test_case.execution_id}")
            
            # 更新状态
            if result["success"]:
                batch_test_case.status = "completed"
                self.logger.info(f"🔍 [EXECUTION_DEBUG] 测试用例 {batch_test_case.test_case_id} 执行成功，最终execution_id: {batch_test_case.execution_id}")
            else:
                batch_test_case.status = "failed"
                self.logger.warning(f"🔍 [EXECUTION_DEBUG] 测试用例 {batch_test_case.test_case_id} 执行失败，最终execution_id: {batch_test_case.execution_id}")
            
            batch_test_case.completed_at = beijing_now()
            batch_test_case.updated_at = beijing_now()
            db.commit()
            
            # 更新批量执行任务的统计数据
            batch_execution = db.query(BatchExecution).filter(
                BatchExecution.id == batch_test_case.batch_execution_id
            ).first()
            
            if batch_execution:
                # 重新计算统计数据
                completed_count = db.query(BatchExecutionTestCase).filter(
                    BatchExecutionTestCase.batch_execution_id == batch_execution.id,
                    BatchExecutionTestCase.status.in_(["completed", "failed"])
                ).count()
                
                running_count = db.query(BatchExecutionTestCase).filter(
                    BatchExecutionTestCase.batch_execution_id == batch_execution.id,
                    BatchExecutionTestCase.status == "running"
                ).count()
                
                pending_count = db.query(BatchExecutionTestCase).filter(
                    BatchExecutionTestCase.batch_execution_id == batch_execution.id,
                    BatchExecutionTestCase.status == "pending"
                ).count()
                
                # 更新批量执行任务状态
                batch_execution.success_count = completed_count - db.query(BatchExecutionTestCase).filter(
                    BatchExecutionTestCase.batch_execution_id == batch_execution.id,
                    BatchExecutionTestCase.status == "failed"
                ).count()
                
                batch_execution.failed_count = db.query(BatchExecutionTestCase).filter(
                    BatchExecutionTestCase.batch_execution_id == batch_execution.id,
                    BatchExecutionTestCase.status == "failed"
                ).count()
                
                batch_execution.running_count = running_count
                batch_execution.pending_count = pending_count
                batch_execution.updated_at = beijing_now()
                db.commit()
                
                # 推送 WebSocket 更新
                await websocket_manager.broadcast_batch_update(
                    batch_execution.id,
                    {
                        "status": batch_execution.status,
                        "success_count": batch_execution.success_count,
                        "failed_count": batch_execution.failed_count,
                        "running_count": batch_execution.running_count,
                        "pending_count": batch_execution.pending_count,
                        "total_count": batch_execution.total_count,
                        "updated_at": batch_execution.updated_at.isoformat() if batch_execution.updated_at else None
                    }
                )
                
        except Exception as e:
            self.logger.error(f"😨 [EXECUTION_DEBUG] 执行测试用例 {batch_test_case.test_case_id} 失败: {e}")
            self.logger.error(f"🔍 [EXECUTION_DEBUG] 外层异常时的execution_id: {batch_test_case.execution_id}")
            
            # 如果还没有创建执行记录，创建一个简单的失败记录
            if not batch_test_case.execution_id:
                self.logger.warning(f"🔍 [EXECUTION_DEBUG] 测试用例 {batch_test_case.test_case_id} 在外层异常时没有execution_id，尝试创建失败记录")
                try:
                    execution = TestExecution(
                        test_case_id=batch_test_case.test_case_id,
                        execution_name=f"批量执行_异常_{beijing_now().strftime('%Y%m%d_%H%M%S')}",
                        status="failed",
                        overall_status="FAILED",
                        error_message=str(e),
                        started_at=beijing_now(),
                        completed_at=beijing_now(),
                        total_steps=0,
                        passed_steps=0,
                        failed_steps=0,
                        skipped_steps=0,
                        summary=f"测试用例执行过程中发生异常: {str(e)}",
                        recommendations="请检查测试用例配置、系统环境或网络连接"
                    )
                    db.add(execution)
                    db.commit()
                    db.refresh(execution)
                    
                    batch_test_case.execution_id = execution.id
                    self.logger.info(f"🔍 [EXECUTION_DEBUG] 为异常测试用例 {batch_test_case.test_case_id} 创建了执行记录 {execution.id}")
                except Exception as create_error:
                    self.logger.error(f"😨 [EXECUTION_DEBUG] 创建异常执行记录失败: {create_error}")
            else:
                self.logger.info(f"🔍 [EXECUTION_DEBUG] 测试用例 {batch_test_case.test_case_id} 在外层异常时已经有execution_id: {batch_test_case.execution_id}")
            
            batch_test_case.status = "failed"
            batch_test_case.completed_at = beijing_now()
            batch_test_case.updated_at = beijing_now()
            db.commit()
    
    def get_batch_execution_status(self, batch_execution_id: int) -> Dict[str, Any]:
        """
        获取批量执行任务的状态
        
        Args:
            batch_execution_id: 批量执行任务ID
            
        Returns:
            批量执行任务状态
        """
        db = SessionLocal()
        try:
            # 获取批量执行任务
            batch_execution = db.query(BatchExecution).filter(
                BatchExecution.id == batch_execution_id
            ).first()
            
            if not batch_execution:
                return {
                    "success": False,
                    "error": f"批量执行任务 {batch_execution_id} 不存在"
                }
            
            # 获取批量执行任务中的测试用例
            batch_test_cases = db.query(BatchExecutionTestCase).filter(
                BatchExecutionTestCase.batch_execution_id == batch_execution_id
            ).all()
            
            test_case_details = []
            for btc in batch_test_cases:
                # 获取测试用例信息
                test_case = db.query(TestCase).filter(
                    TestCase.id == btc.test_case_id
                ).first()
                
                # 获取执行记录信息
                execution = None
                if btc.execution_id:
                    execution = db.query(TestExecution).filter(
                        TestExecution.id == btc.execution_id
                    ).first()
                
                test_case_details.append({
                    "id": btc.id,
                    "test_case_id": btc.test_case_id,
                    "test_case_name": test_case.name if test_case else "未知",
                    "execution_id": btc.execution_id,
                    "status": btc.status,
                    "overall_status": execution.overall_status if execution else None,
                    "started_at": btc.started_at.isoformat() if btc.started_at else None,
                    "completed_at": btc.completed_at.isoformat() if btc.completed_at else None,
                    "error_message": execution.error_message if execution else None
                })
            
            return {
                "success": True,
                "batch_execution": {
                    "id": batch_execution.id,
                    "name": batch_execution.name,
                    "status": batch_execution.status,
                    "total_count": batch_execution.total_count,
                    "success_count": batch_execution.success_count,
                    "failed_count": batch_execution.failed_count,
                    "running_count": batch_execution.running_count,
                    "pending_count": batch_execution.pending_count,
                    "total_duration": batch_execution.total_duration,
                    "started_at": batch_execution.started_at.isoformat() if batch_execution.started_at else None,
                    "completed_at": batch_execution.completed_at.isoformat() if batch_execution.completed_at else None,
                    "created_at": batch_execution.created_at.isoformat() if batch_execution.created_at else None,
                    "updated_at": batch_execution.updated_at.isoformat() if batch_execution.updated_at else None,
                    "test_cases": test_case_details
                }
            }
        finally:
            db.close()

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

# 全局的BatchTestExecutor实例管理器
class BatchExecutorManager:
    """批量执行器管理器"""
    
    def __init__(self):
        self._lock = asyncio.Lock()
    
    async def create_executor(self, batch_execution_id: int, max_concurrent: int = 5) -> BatchTestExecutor:
        """创建并注册一个批量执行器"""
        async with self._lock:
            executor = BatchTestExecutor(max_concurrent=max_concurrent)
            return executor
    
    async def get_executor(self, batch_execution_id: int) -> Optional[BatchTestExecutor]:
        """获取指定的批量执行器"""
        return task_context.get_batch_executor(batch_execution_id)
    
    async def cancel_executor(self, batch_execution_id: int) -> bool:
        """取消指定的批量执行器"""
        return await task_context.cancel_batch_execution(batch_execution_id)
    
    async def remove_executor(self, batch_execution_id: int):
        """移除指定的批量执行器"""
        await task_context.unregister_batch_executor(batch_execution_id)
    
    def is_batch_cancelled(self, batch_execution_id: int) -> bool:
        """检查批量执行任务是否被取消"""
        return not task_context.is_batch_registered(batch_execution_id)

# 全局实例
batch_executor_manager = BatchExecutorManager()