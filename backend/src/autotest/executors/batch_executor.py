"""
批量测试执行器模块
"""
import asyncio
import logging
from typing import Dict, Any, List, Optional

from ..core.time_utils import beijing_now
from ..core.task_context import task_context
from ..database import TestCase, TestExecution, BatchExecution, BatchExecutionTestCase, SessionLocal
from ..websocket_manager import websocket_manager
from .test_executor import TestExecutor

class BatchTestExecutor:
    """批量测试执行器"""
    
    def __init__(self, max_concurrent: int = 5):
        """
        初始化批量测试执行器
        
        Args:
            max_concurrent: 最大并发执行数量，默认为5
        """
        self.test_executor = TestExecutor()
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
    
    async def execute_batch_test(self, test_case_ids: List[int], headless: bool = False, 
                                batch_name: str = "批量执行任务", 
                                batch_execution_id: Optional[int] = None) -> Dict[str, Any]:
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
    
    async def _execute_single_test_in_batch(self, batch_test_case: BatchExecutionTestCase, 
                                          headless: bool, db):
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
            if not task_context.is_batch_registered(batch_test_case.batch_execution_id):
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
            if not task_context.is_batch_registered(batch_test_case.batch_execution_id):
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
            if not task_context.is_batch_registered(batch_test_case.batch_execution_id):
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
