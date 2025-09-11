"""
单个测试执行器模块
"""
import asyncio
import logging
from typing import Dict, Any, Optional

from browser_use import Browser, Agent
from ..core.time_utils import beijing_now
from ..core.models import ControllerTestResult
from ..core.task_context import task_context
from ..services.history_service import HistoryService
from ..services.screenshot_service import ScreenshotService
from ..services.result_parser import ResultParserService
from ..database import TestCase, TestExecution, SessionLocal
from ..websocket_manager import websocket_manager
from ..browser_event_collector import event_manager
from .base_executor import BaseExecutor

class TestExecutor(BaseExecutor):
    """测试执行器"""
    
    def __init__(self):
        super().__init__()
        self.history_service = HistoryService()
        self.screenshot_service = ScreenshotService()
        self.result_parser = ResultParserService()
    
    async def execute_test_case(self, test_case_id: int, headless: bool = False, 
                              batch_execution_id: Optional[int] = None, 
                              execution_id: Optional[int] = None) -> Dict[str, Any]:
        """执行单个测试用例"""
        db = SessionLocal()
        try:
            test_case = self._get_test_case(test_case_id, db)
            if not test_case:
                return self._create_error_result("测试用例不存在")
            
            execution = self._get_or_create_execution(test_case_id, execution_id, db)
            if not execution:
                return self._create_error_result("执行记录不存在")
            
            # 尝试缓存回放
            result = await self._try_cache_replay(test_case, execution, headless, db)
            if result:
                return self._update_execution_from_result(execution, result, db)
            
            # 执行浏览器测试
            result = await self._run_browser_test(test_case, execution, headless, batch_execution_id)
            return self._update_execution_from_result(execution, result, db)
            
        except Exception as e:
            self.logger.error(f"执行测试用例 {test_case_id} 失败: {e}")
            return self._create_error_result(str(e))
        finally:
            db.close()
    
    def _get_test_case(self, test_case_id: int, db) -> Optional[TestCase]:
        """获取测试用例"""
        return db.query(TestCase).filter(
            TestCase.id == test_case_id,
            TestCase.is_deleted == False
        ).first()
    
    def _get_or_create_execution(self, test_case_id: int, execution_id: Optional[int], db) -> Optional[TestExecution]:
        """获取或创建执行记录"""
        if execution_id:
            return db.query(TestExecution).filter(TestExecution.id == execution_id).first()
        else:
            execution = TestExecution(
                test_case_id=test_case_id,
                execution_name=f"{test_case_id}_{beijing_now().strftime('%Y%m%d_%H%M%S')}",
                status="running",
                started_at=beijing_now()
            )
            db.add(execution)
            db.commit()
            db.refresh(execution)
            return execution
    
    def _create_error_result(self, error_message: str) -> Dict[str, Any]:
        """创建错误结果"""
        return {
            "success": False,
            "error_message": error_message,
            "execution_id": None
        }
    
    def _update_execution_from_result(self, execution: TestExecution, result: Dict[str, Any], db) -> Dict[str, Any]:
        """根据结果更新执行记录"""
        execution.status = "passed" if result["success"] else "failed"
        execution.overall_status = result.get("overall_status", "FAILED")
        execution.total_duration = result.get("total_duration", 0)
        execution.summary = result.get("summary", "")
        execution.recommendations = result.get("recommendations", "")
        execution.error_message = result.get("error_message", "")
        execution.completed_at = beijing_now()
        
        # 更新统计信息
        if "total_steps" in result:
            execution.total_steps = result.get("total_steps", 0)
            execution.passed_steps = result.get("passed_steps", 0)
            execution.failed_steps = result.get("failed_steps", 0)
            execution.skipped_steps = result.get("skipped_steps", 0)
        
        execution.browser_logs = result.get("browser_logs", [])
        execution.screenshots = result.get("screenshots", [])
        
        db.commit()
        
        return {
            "success": result["success"],
            "execution_id": execution.id,
            "overall_status": result.get("overall_status", "FAILED"),
            "total_duration": result.get("total_duration", 0),
            "summary": result.get("summary", ""),
            "recommendations": result.get("recommendations", ""),
            "error_message": result.get("error_message", ""),
            "from_history": result.get("from_history", False)
        }
    
    async def _try_cache_replay(self, test_case: TestCase, execution: TestExecution, 
                               headless: bool, db) -> Optional[Dict[str, Any]]:
        """尝试缓存回放"""
        if not self.history_service.should_use_history(test_case):
            return None
        
        result = await self._try_replay_from_history(test_case, execution, headless)
        if not result:
            self.history_service.invalidate_history(test_case.id, db)
        
        return result
    
    async def _try_replay_from_history(self, test_case: TestCase, execution: TestExecution, 
                                     headless: bool) -> Optional[Dict[str, Any]]:
        """尝试从历史记录回放"""
        try:
            # 创建LLM实例
            config = self.multi_llm_service._load_multi_model_config()
            request_config = await self.multi_llm_service._get_next_available_config_with_wait(config)
            llm = self.multi_llm_service._create_llm_instance(request_config)
            
            # 创建浏览器和Agent
            browser = Browser(headless=headless, highlight_elements=False,enable_default_extensions=False)
            event_collector = event_manager.create_collector(test_case.id, execution.id)
            
            agent = Agent(
                task=f"# 操作步骤\n{test_case.task_content}\n\n# 预期结果:\n{test_case.expected_result}",
                llm=llm,
                browser=browser,
                use_vision=True,
                output_model_schema=ControllerTestResult,
                extend_system_message=self._get_final_prompt(),
                llm_timeout=120,
                step_timeout=300
            )
            
            # 注册事件监听器
            agent.eventbus.on('CreateAgentStepEvent', event_collector.collect_step_event)
            agent.eventbus.on('UpdateAgentTaskEvent', event_collector.collect_task_completion)
            agent.eventbus.on('ErrorEvent', event_collector.collect_error_event)
            
            # 启动浏览器会话
            from browser_use.browser.events import BrowserStartEvent
            event = agent.browser_session.event_bus.dispatch(BrowserStartEvent())
            await event
            await event.event_result(raise_if_any=True, raise_if_none=False)
            
            # 回放历史记录
            history_path = self.history_service.get_history_path_from_relative(test_case.history_path)
            if not history_path or not history_path.exists():
                return None
            
            history = await agent.load_and_rerun(str(history_path))
            
            # 解析结果
            test_result_data = self.result_parser.parse_test_result(history)
            test_result_data["from_history"] = True
            
            # 保存截图
            screenshots = self.screenshot_service.save_screenshots(history, execution.id)
            test_result_data["screenshots"] = screenshots
            
            return test_result_data
            
        except Exception as e:
            self.logger.warning(f"从历史记录回放失败: {e}")
            return None
        finally:
            try:
                await agent.close()
            except Exception as e:
                self.logger.warning(f"关闭浏览器时出错: {e}")
    
    async def _run_browser_test(self, test_case: TestCase, execution: TestExecution, 
                              headless: bool, batch_execution_id: Optional[int] = None) -> Dict[str, Any]:
        """运行浏览器测试"""
        agent = None
        try:
            # 创建浏览器和Agent
            browser = Browser(headless=headless, highlight_elements=False,enable_default_extensions=False)
            
            config = self.multi_llm_service._load_multi_model_config()
            request_config = await self.multi_llm_service._get_next_available_config_with_wait(config)
            llm = self.multi_llm_service._create_llm_instance(request_config)
            
            event_collector = event_manager.create_collector(test_case.id, execution.id)
            
            agent = Agent(
                task=f"# 操作步骤\n{test_case.task_content}\n\n# 预期结果:\n{test_case.expected_result}",
                llm=llm,
                browser=browser,
                use_vision=True,
                output_model_schema=ControllerTestResult,
                extend_system_message=self._get_final_prompt(),
                llm_timeout=120,
                step_timeout=300
            )
            
            # 注册事件监听器
            agent.eventbus.on('CreateAgentStepEvent', event_collector.collect_step_event)
            agent.eventbus.on('UpdateAgentTaskEvent', event_collector.collect_task_completion)
            agent.eventbus.on('ErrorEvent', event_collector.collect_error_event)
            
            start_time = beijing_now()
            
            if batch_execution_id:
                # 批量执行
                agent_task = asyncio.create_task(agent.run())
                await task_context.register_test_case(batch_execution_id, test_case.id, browser, agent_task)
                
                try:
                    history = await agent_task
                    test_result_data = self.result_parser.parse_test_result(history)
                except asyncio.CancelledError:
                    self.logger.info(f"测试用例 {test_case.id} 被取消")
                    raise
            else:
                # 单个执行
                history = await agent.run()
                test_result_data = self.result_parser.parse_test_result(history)
            
            end_time = beijing_now()
            total_duration = (end_time - start_time).total_seconds()
            
            # 保存截图
            screenshots = self.screenshot_service.save_screenshots(history, execution.id)
            
            # 保存历史记录
            history_path = ""
            if test_result_data.get("success") and agent:
                history_path = self.history_service.save_history_to_cache(test_case.id, agent, SessionLocal())
            
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
            if agent is not None:
                await agent.close()
    
    def _get_final_prompt(self) -> str:
        """获取最终提示词"""
        from ..constants.prompts import TEST_SYSTEM_PROMPT
        custom_prompt = self._load_custom_prompt()
        return f"{TEST_SYSTEM_PROMPT}\n\n{custom_prompt}" if custom_prompt else TEST_SYSTEM_PROMPT
