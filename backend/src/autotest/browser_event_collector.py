"""
Browser-Use 事件收集器
利用 Browser-Use 的事件机制实现实时步骤记录和结果收集
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass
from .database import SessionLocal, TestStep
from datetime import datetime, timezone, timedelta

# 设置时区为北京时间
BEIJING_TZ = timezone(timedelta(hours=8))

def beijing_now():
    """获取北京时间"""
    return datetime.now(BEIJING_TZ)

@dataclass
class StepEventData:
    """步骤事件数据"""
    step_number: int
    timestamp: datetime
    url: Optional[str] = None
    actions: Optional[List[Dict[str, Any]]] = None
    evaluation: Optional[str] = None
    memory: Optional[str] = None
    next_goal: Optional[str] = None
    screenshot_data: Optional[str] = None
    status: str = "RUNNING"
    duration: Optional[float] = None
    error_message: Optional[str] = None
    
    def __post_init__(self):
        if self.actions is None:
            self.actions = []

@dataclass
class TaskCompletionData:
    """任务完成数据"""
    task_id: Optional[str]
    status: str  # "completed", "failed", "cancelled"
    success: bool
    output: Optional[str] = None
    finished_at: Optional[datetime] = None
    total_steps: int = 0
    error_message: Optional[str] = None


class BrowserUseEventCollector:
    """Browser-Use 事件收集器"""
    
    def __init__(self, test_case_id: int, execution_id: int):
        self.test_case_id = test_case_id
        self.execution_id = execution_id
        self.logger = logging.getLogger(__name__)
        
        # 步骤数据存储
        self.step_events: List[StepEventData] = []
        self.task_completion: Optional[TaskCompletionData] = None
        
        # 步骤时间跟踪
        self.step_start_times: Dict[int, datetime] = {}
        
        # 回调函数
        self.on_step_update: Optional[Callable] = None
        self.on_task_completion: Optional[Callable] = None
        
        # WebSocket管理器
        from .websocket_manager import websocket_manager
        self.websocket_manager = websocket_manager
        
        self.logger.info(f"初始化事件收集器 - 测试用例ID: {test_case_id}, 执行ID: {execution_id}")
    
    def set_callbacks(self, on_step_update: Optional[Callable] = None, on_task_completion: Optional[Callable] = None):
        """设置回调函数"""
        self.on_step_update = on_step_update
        self.on_task_completion = on_task_completion
    
    async def collect_step_event(self, event):
        """收集步骤执行事件"""
        try:
            self.logger.info(f"收到步骤事件: {type(event).__name__}")
            
            # 记录步骤开始时间
            step_number = getattr(event, 'step', 0)
            if step_number > 0 and step_number not in self.step_start_times:
                self.step_start_times[step_number] = beijing_now()
            
            # 提取步骤数据
            step_data = StepEventData(
                step_number=step_number,
                timestamp=beijing_now(),
                url=getattr(event, 'url', None),
                actions=getattr(event, 'actions', []),
                evaluation=getattr(event, 'evaluation_previous_goal', None),
                memory=getattr(event, 'memory', None),
                next_goal=getattr(event, 'next_goal', None),
                screenshot_data=self._extract_screenshot(event),
                status="RUNNING"
            )
            
            # 计算步骤执行时间
            if step_number in self.step_start_times:
                duration = (step_data.timestamp - self.step_start_times[step_number]).total_seconds()
                step_data.duration = duration
            
            # 检查是否已存在相同步骤编号的记录
            existing_step = None
            existing_step_index = -1
            for i, existing in enumerate(self.step_events):
                if existing.step_number == step_data.step_number:
                    existing_step = existing
                    existing_step_index = i
                    break
            
            # 如果已存在相同步骤编号，合并信息而不是简单替换
            if existing_step:
                # 合并步骤数据，保留最新的非空值
                merged_step = self._merge_step_data(existing_step, step_data)
                self.step_events[existing_step_index] = merged_step
                step_data = merged_step
                self.logger.info(f"合并更新步骤 {step_number}")
            else:
                # 存储新步骤数据
                self.step_events.append(step_data)
                self.logger.info(f"添加新步骤 {step_number}")
            
            self.logger.info(f"步骤 {step_number} 记录完成: {step_data.url}")
            
            # 实时保存步骤数据到数据库
            await self._save_step_to_database(step_data, not existing_step)
            
            # 实时推送步骤更新到WebSocket
            await self._broadcast_step_update(step_data)
            
            # 异步调用回调函数
            if self.on_step_update:
                asyncio.create_task(self.on_step_update(step_data))
                
        except Exception as e:
            self.logger.error(f"收集步骤事件失败: {e}")
    
    async def collect_task_completion(self, event):
        """收集任务完成事件"""
        try:
            self.logger.info(f"收到任务完成事件: {type(event).__name__}")
            
            # 提取完成数据
            success = getattr(event, 'done_output', None) is not None
            
            self.task_completion = TaskCompletionData(
                task_id=getattr(event, 'id', None),
                status='completed' if success else 'failed',
                success=success,
                output=getattr(event, 'done_output', None),
                finished_at=getattr(event, 'finished_at', None) or beijing_now(),
                total_steps=len(self.step_events),
                error_message=None if success else "任务未正常完成"
            )
            
            # 更新最后一个步骤的状态
            if self.step_events:
                last_step = self.step_events[-1]
                last_step.status = "PASSED" if success else "FAILED"
                if not success:
                    last_step.error_message = self.task_completion.error_message
            
            self.logger.info(f"任务完成记录: {self.task_completion.status}")
            
            # 实时推送任务完成更新到WebSocket
            await self._broadcast_task_completion(self.task_completion)
            
            # 异步调用回调函数
            if self.on_task_completion:
                asyncio.create_task(self.on_task_completion(self.task_completion))
                
        except Exception as e:
            self.logger.error(f"收集任务完成事件失败: {e}")
    
    async def collect_error_event(self, event):
        """收集错误事件"""
        try:
            self.logger.warning(f"收到错误事件: {type(event).__name__}")
            
            # 更新当前步骤状态为失败
            if self.step_events:
                current_step = self.step_events[-1]
                current_step.status = "FAILED"
                current_step.error_message = str(getattr(event, 'error', '未知错误'))
                
                # 实时推送步骤更新到WebSocket
                await self._broadcast_step_update(current_step)
                
                # 异步调用回调函数
                if self.on_step_update:
                    asyncio.create_task(self.on_step_update(current_step))
            
        except Exception as e:
            self.logger.error(f"收集错误事件失败: {e}")
    
    def _extract_screenshot(self, event) -> Optional[str]:
        """从事件中提取截图数据"""
        screenshot_url = getattr(event, 'screenshot_url', None)
        if screenshot_url:
            # 截取前100个字符作为标识
            return screenshot_url[:100] + '...' if len(screenshot_url) > 100 else screenshot_url
        return None
    
    async def _save_step_to_database(self, step_data: StepEventData, is_new: bool = True):
        """实时保存步骤数据到数据库"""
        try:
            db = SessionLocal()
            try:
                if is_new:
                    # 创建新的测试步骤记录
                    step = TestStep(
                        execution_id=self.execution_id,
                        step_name=f"步骤 {step_data.step_number}",
                        step_order=step_data.step_number,
                        status=step_data.status,
                        description=step_data.next_goal or step_data.evaluation or "执行浏览器操作",
                        error_message=step_data.error_message,
                        screenshot_path=step_data.screenshot_data,
                        duration_seconds=step_data.duration,
                        started_at=step_data.timestamp,
                        completed_at=step_data.timestamp,
                        # 新增字段
                        url=step_data.url,
                        actions=step_data.actions,
                        evaluation=step_data.evaluation,
                        memory=step_data.memory,
                        next_goal=step_data.next_goal,
                        screenshot_data=step_data.screenshot_data,
                        event_timestamp=step_data.timestamp,
                        step_metadata={
                            "timestamp": step_data.timestamp.isoformat() if step_data.timestamp else None,
                            "duration": step_data.duration
                        }
                    )
                    db.add(step)
                    db.commit()
                    db.refresh(step)
                    self.logger.info(f"步骤 {step_data.step_number} 已实时保存到数据库，ID: {step.id}")
                else:
                    # 查找并更新现有的测试步骤记录
                    existing_step = db.query(TestStep).filter(
                        TestStep.execution_id == self.execution_id,
                        TestStep.step_order == step_data.step_number
                    ).first()
                    
                    if existing_step:
                        # 合并更新现有记录，保留非空值
                        if step_data.url is not None:
                            existing_step.url = step_data.url
                        if step_data.actions is not None and len(step_data.actions) > 0:
                            existing_step.actions = step_data.actions
                        if step_data.evaluation is not None:
                            existing_step.evaluation = step_data.evaluation
                        if step_data.memory is not None:
                            existing_step.memory = step_data.memory
                        if step_data.next_goal is not None:
                            existing_step.next_goal = step_data.next_goal
                        if step_data.screenshot_data is not None:
                            existing_step.screenshot_data = step_data.screenshot_data
                        if step_data.status is not None:
                            existing_step.status = step_data.status
                        if step_data.duration is not None:
                            existing_step.duration_seconds = step_data.duration
                        if step_data.error_message is not None:
                            existing_step.error_message = step_data.error_message
                        
                        existing_step.completed_at = step_data.timestamp
                        existing_step.event_timestamp = step_data.timestamp
                        existing_step.description = step_data.next_goal or step_data.evaluation or existing_step.description or "执行浏览器操作"
                        
                        # 更新元数据
                        if existing_step.step_metadata:
                            metadata = existing_step.step_metadata
                            if step_data.timestamp:
                                metadata["timestamp"] = step_data.timestamp.isoformat()
                            if step_data.duration is not None:
                                metadata["duration"] = step_data.duration
                            existing_step.step_metadata = metadata
                        else:
                            existing_step.step_metadata = {
                                "timestamp": step_data.timestamp.isoformat() if step_data.timestamp else None,
                                "duration": step_data.duration
                            }
                        
                        db.commit()
                        db.refresh(existing_step)
                        self.logger.info(f"步骤 {step_data.step_number} 已合并更新到数据库，ID: {existing_step.id}")
                    else:
                        # 如果没有找到现有记录，则创建新记录
                        step = TestStep(
                            execution_id=self.execution_id,
                            step_name=f"步骤 {step_data.step_number}",
                            step_order=step_data.step_number,
                            status=step_data.status,
                            description=step_data.next_goal or step_data.evaluation or "执行浏览器操作",
                            error_message=step_data.error_message,
                            screenshot_path=step_data.screenshot_data,
                            duration_seconds=step_data.duration,
                            started_at=step_data.timestamp,
                            completed_at=step_data.timestamp,
                            # 新增字段
                            url=step_data.url,
                            actions=step_data.actions,
                            evaluation=step_data.evaluation,
                            memory=step_data.memory,
                            next_goal=step_data.next_goal,
                            screenshot_data=step_data.screenshot_data,
                            event_timestamp=step_data.timestamp,
                            step_metadata={
                                "timestamp": step_data.timestamp.isoformat() if step_data.timestamp else None,
                                "duration": step_data.duration
                            }
                        )
                        db.add(step)
                        db.commit()
                        db.refresh(step)
                        self.logger.info(f"步骤 {step_data.step_number} 已实时保存到数据库，ID: {step.id}")
            except Exception as e:
                db.rollback()
                self.logger.error(f"保存步骤 {step_data.step_number} 到数据库失败: {e}")
            finally:
                db.close()
        except Exception as e:
            self.logger.error(f"获取数据库会话失败: {e}")
    
    async def _broadcast_step_update(self, step_data: StepEventData):
        """广播步骤更新到WebSocket"""
        try:
            # 构造步骤更新数据
            step_update_data = {
                "type": "step_update",
                "test_case_id": self.test_case_id,
                "execution_id": self.execution_id,
                "step_data": {
                    "step_number": step_data.step_number,
                    "status": step_data.status,
                    "url": step_data.url,
                    "next_goal": step_data.next_goal,
                    "evaluation": step_data.evaluation,
                    "actions": step_data.actions,
                    "duration": step_data.duration,
                    "timestamp": step_data.timestamp.isoformat()
                }
            }
            
            # 广播到WebSocket
            await self.websocket_manager.broadcast_batch_update(
                self.execution_id, 
                step_update_data
            )
        except Exception as e:
            self.logger.error(f"广播步骤更新失败: {e}")
    
    async def _broadcast_task_completion(self, completion_data: TaskCompletionData):
        """广播任务完成更新到WebSocket"""
        try:
            # 构造任务完成数据
            task_completion_data = {
                "type": "task_completion",
                "test_case_id": self.test_case_id,
                "execution_id": self.execution_id,
                "completion_data": {
                    "status": completion_data.status,
                    "success": completion_data.success,
                    "output": completion_data.output,
                    "finished_at": completion_data.finished_at.isoformat() if completion_data.finished_at else None,
                    "total_steps": completion_data.total_steps,
                    "error_message": completion_data.error_message
                }
            }
            
            # 广播到WebSocket
            await self.websocket_manager.broadcast_batch_update(
                self.execution_id, 
                task_completion_data
            )
        except Exception as e:
            self.logger.error(f"广播任务完成更新失败: {e}")
    
    def get_step_summary(self) -> Dict[str, Any]:
        """获取步骤执行摘要"""
        total_steps = len(self.step_events)
        passed_steps = len([s for s in self.step_events if s.status == "PASSED"])
        failed_steps = len([s for s in self.step_events if s.status == "FAILED"])
        running_steps = len([s for s in self.step_events if s.status == "RUNNING"])
        
        total_duration = sum(s.duration for s in self.step_events if s.duration) or 0
        
        return {
            "total_steps": total_steps,
            "passed_steps": passed_steps,
            "failed_steps": failed_steps,
            "running_steps": running_steps,
            "total_duration": total_duration,
            "success_rate": (passed_steps / total_steps * 100) if total_steps > 0 else 0
        }
    
    def convert_to_test_result(self) -> Dict[str, Any]:
        """转换为测试结果格式"""
        summary = self.get_step_summary()
        
        # 构造测试步骤数据
        test_steps = []
        for step_data in self.step_events:
            test_steps.append({
                "step_name": f"步骤 {step_data.step_number}",
                "step_order": step_data.step_number,
                "status": step_data.status,
                "description": step_data.next_goal or step_data.evaluation or "执行浏览器操作",
                "error_message": step_data.error_message,
                "screenshot_path": step_data.screenshot_data,
                "duration_seconds": step_data.duration,
                "url": step_data.url,
                "actions": step_data.actions,
                "timestamp": step_data.timestamp.isoformat()
            })
        
        # 判断整体状态
        if self.task_completion:
            overall_status = "PASSED" if self.task_completion.success else "FAILED"
        else:
            overall_status = "FAILED" if summary["failed_steps"] > 0 else "PARTIAL"
        
        return {
            "success": self.task_completion.success if self.task_completion else False,
            "overall_status": overall_status,
            "total_duration": summary["total_duration"],
            "summary": self._generate_summary(),
            "recommendations": self._generate_recommendations(),
            "test_steps": test_steps,
            "task_completion": self.task_completion.__dict__ if self.task_completion else None
        }
    
    def _generate_summary(self) -> str:
        """生成测试摘要"""
        summary = self.get_step_summary()
        
        if self.task_completion and self.task_completion.success:
            return f"测试执行成功，共 {summary['total_steps']} 个步骤，耗时 {summary['total_duration']:.2f} 秒"
        else:
            return f"测试执行失败，共 {summary['total_steps']} 个步骤，{summary['failed_steps']} 个失败，耗时 {summary['total_duration']:.2f} 秒"
    
    def _generate_recommendations(self) -> Optional[str]:
        """生成改进建议"""
        summary = self.get_step_summary()
        
        if summary["failed_steps"] > 0:
            return "建议检查失败步骤的错误信息，优化页面元素定位或增加等待时间"
        elif summary["total_duration"] > 60:
            return "测试执行时间较长，建议优化步骤或增加并发执行"
        else:
            return "测试执行正常，无特殊建议"
    
    def _merge_step_data(self, existing_step: StepEventData, new_step: StepEventData) -> StepEventData:
        """合并两个步骤数据，保留最新的非空值"""
        # 创建合并后的步骤数据
        merged_step = StepEventData(
            step_number=existing_step.step_number,
            timestamp=new_step.timestamp,  # 使用最新的时间戳
            url=new_step.url if new_step.url is not None else existing_step.url,
            actions=new_step.actions if new_step.actions is not None and len(new_step.actions) > 0 else existing_step.actions,
            evaluation=new_step.evaluation if new_step.evaluation is not None else existing_step.evaluation,
            memory=new_step.memory if new_step.memory is not None else existing_step.memory,
            next_goal=new_step.next_goal if new_step.next_goal is not None else existing_step.next_goal,
            screenshot_data=new_step.screenshot_data if new_step.screenshot_data is not None else existing_step.screenshot_data,
            status=new_step.status if new_step.status is not None else existing_step.status,
            duration=new_step.duration if new_step.duration is not None else existing_step.duration,
            error_message=new_step.error_message if new_step.error_message is not None else existing_step.error_message
        )
        
        return merged_step


class BrowserUseEventManager:
    """Browser-Use 事件管理器"""
    
    def __init__(self):
        self.collectors: Dict[str, BrowserUseEventCollector] = {}
        self.logger = logging.getLogger(__name__)
    
    def create_collector(self, test_case_id: int, execution_id: int) -> BrowserUseEventCollector:
        """创建事件收集器"""
        collector_key = f"{test_case_id}_{execution_id}"
        
        if collector_key in self.collectors:
            self.logger.warning(f"收集器已存在: {collector_key}")
            return self.collectors[collector_key]
        
        collector = BrowserUseEventCollector(test_case_id, execution_id)
        self.collectors[collector_key] = collector
        
        self.logger.info(f"创建事件收集器: {collector_key}")
        return collector
    
    def get_collector(self, test_case_id: int, execution_id: int) -> Optional[BrowserUseEventCollector]:
        """获取事件收集器"""
        collector_key = f"{test_case_id}_{execution_id}"
        return self.collectors.get(collector_key)
    
    def remove_collector(self, test_case_id: int, execution_id: int):
        """移除事件收集器"""
        collector_key = f"{test_case_id}_{execution_id}"
        if collector_key in self.collectors:
            del self.collectors[collector_key]
            self.logger.info(f"移除事件收集器: {collector_key}")


# 全局事件管理器实例
event_manager = BrowserUseEventManager()