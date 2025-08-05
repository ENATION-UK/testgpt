"""
测试执行服务
"""

from fastapi import HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from datetime import datetime, timezone, timedelta
from typing import List
import asyncio

# 设置时区为北京时间
BEIJING_TZ = timezone(timedelta(hours=8))

def beijing_now():
    """获取北京时间"""
    return datetime.now(BEIJING_TZ)

from ..database import TestCase, TestExecution, TestStep, SessionLocal, BatchExecution, BatchExecutionTestCase
from ..models import TestExecutionRequest, TestExecutionResponse, BatchExecutionRequest, BatchExecutionResponse
from ..test_executor import execute_single_test, execute_multiple_tests, BatchTestExecutor, batch_executor_manager
from ..websocket_manager import websocket_manager

class ExecutionService:
    """测试执行服务类"""
    
    @staticmethod
    async def execute_single_test(
        execution_request: TestExecutionRequest,
        background_tasks: BackgroundTasks,
        db: Session
    ) -> TestExecutionResponse:
        """执行单个测试用例"""
        # 检查测试用例是否存在
        test_case = db.query(TestCase).filter(
            TestCase.id == execution_request.test_case_id,
            TestCase.is_deleted == False
        ).first()
        if not test_case:
            raise HTTPException(status_code=404, detail="测试用例不存在")
        
        # 创建执行记录
        execution = TestExecution(
            test_case_id=execution_request.test_case_id,
            execution_name=f"{test_case.name}_{beijing_now().strftime('%Y%m%d_%H%M%S')}",
            status="running",
            started_at=beijing_now()
        )
        db.add(execution)
        db.commit()
        db.refresh(execution)
        
        # 在后台执行测试
        background_tasks.add_task(
            ExecutionService._run_test_in_background,
            execution.id,
            execution_request.test_case_id,
            execution_request.headless
        )
        
        return execution

    @staticmethod
    async def execute_batch_tests(
        batch_request: BatchExecutionRequest,
        background_tasks: BackgroundTasks,
        db: Session
    ) -> BatchExecutionResponse:
        """批量执行测试用例"""
        # 检查所有测试用例是否存在
        test_cases = db.query(TestCase).filter(
            TestCase.id.in_(batch_request.test_case_ids),
            TestCase.is_deleted == False
        ).all()
        
        if len(test_cases) != len(batch_request.test_case_ids):
            raise HTTPException(status_code=404, detail="部分测试用例不存在")
        
        # 在后台执行批量测试
        background_tasks.add_task(
            ExecutionService._run_batch_tests_in_background,
            batch_request.test_case_ids,
            batch_request.headless
        )
        
        return {
            "success": True,
            "total_count": len(batch_request.test_case_ids),
            "passed_count": 0,
            "failed_count": 0,
            "results": [],
            "message": "批量测试已开始执行，请查看执行记录"
        }

    @staticmethod
    async def create_batch_execution(
        batch_request: BatchExecutionRequest,
        background_tasks: BackgroundTasks,
        db: Session
    ) -> dict:
        """创建批量执行任务"""
        # 检查所有测试用例是否存在
        test_cases = db.query(TestCase).filter(
            TestCase.id.in_(batch_request.test_case_ids),
            TestCase.is_deleted == False
        ).all()
        
        if len(test_cases) != len(batch_request.test_case_ids):
            raise HTTPException(status_code=404, detail="部分测试用例不存在")
        
        # 创建批量执行任务记录 - 状态设为pending，不立即执行
        batch_execution = BatchExecution(
            name=f"批量执行任务_{beijing_now().strftime('%Y%m%d_%H%M%S')}",
            status="pending",  # 改为pending状态
            total_count=len(batch_request.test_case_ids),
            pending_count=len(batch_request.test_case_ids),
            headless=batch_request.headless,  # 保存headless设置
            # 不设置started_at，因为还没有开始执行
        )
        db.add(batch_execution)
        db.commit()
        db.refresh(batch_execution)
        
        # 创建批量执行任务中的测试用例记录
        batch_test_cases = []
        for test_case_id in batch_request.test_case_ids:
            batch_test_case = BatchExecutionTestCase(
                batch_execution_id=batch_execution.id,
                test_case_id=test_case_id,
                status="pending"
            )
            db.add(batch_test_case)
            batch_test_cases.append(batch_test_case)
        
        db.commit()
        
        # 不再立即在后台执行批量测试
        # background_tasks.add_task(
        #     ExecutionService._run_batch_execution_in_background,
        #     batch_execution.id,
        #     batch_request.test_case_ids,
        #     batch_request.headless
        # )
        
        return {
            "success": True,
            "batch_execution_id": batch_execution.id,
            "message": "批量执行任务已创建，请点击执行按钮开始执行"
        }

    @staticmethod
    async def start_batch_execution(
        batch_execution_id: int,
        background_tasks: BackgroundTasks,
        db: Session
    ) -> dict:
        """启动批量执行任务"""
        # 检查批量执行任务是否存在
        batch_execution = db.query(BatchExecution).filter(BatchExecution.id == batch_execution_id).first()
        if not batch_execution:
            raise HTTPException(status_code=404, detail="批量执行任务不存在")
        
        # 检查任务状态
        if batch_execution.status == "running":
            raise HTTPException(status_code=400, detail="任务已在运行中")
        elif batch_execution.status in ["completed", "failed", "cancelled"]:
            raise HTTPException(status_code=400, detail="任务已完成，无法重新启动")
        
        # 获取测试用例ID列表
        batch_test_cases = db.query(BatchExecutionTestCase).filter(
            BatchExecutionTestCase.batch_execution_id == batch_execution_id
        ).all()
        
        test_case_ids = [btc.test_case_id for btc in batch_test_cases]
        
        if not test_case_ids:
            raise HTTPException(status_code=400, detail="批量执行任务中没有测试用例")
        
        # 更新任务状态为运行中
        batch_execution.status = "running"
        batch_execution.started_at = beijing_now()
        batch_execution.updated_at = beijing_now()
        
        # 重置所有测试用例状态为pending
        for btc in batch_test_cases:
            btc.status = "pending"
            btc.started_at = None
            btc.completed_at = None
            btc.execution_id = None
        
        # 更新统计信息
        batch_execution.pending_count = len(test_case_ids)
        batch_execution.running_count = 0
        batch_execution.success_count = 0
        batch_execution.failed_count = 0
        
        db.commit()
        
        # 在后台执行批量测试
        background_tasks.add_task(
            ExecutionService._run_batch_execution_in_background,
            batch_execution.id,
            test_case_ids,
            batch_execution.headless  # 使用数据库中保存的headless设置
        )
        
        return {
            "success": True,
            "message": "批量执行任务已启动"
        }

    @staticmethod
    async def stop_batch_execution(
        batch_execution_id: int,
        db: Session
    ) -> dict:
        """停止批量执行任务"""
        # 检查批量执行任务是否存在
        batch_execution = db.query(BatchExecution).filter(BatchExecution.id == batch_execution_id).first()
        if not batch_execution:
            raise HTTPException(status_code=404, detail="批量执行任务不存在")
        
        # 检查任务状态
        if batch_execution.status not in ["running", "pending"]:
            raise HTTPException(status_code=400, detail="任务不在运行状态，无法停止")
        
        # 尝试取消正在运行的执行器
        executor_cancelled = await batch_executor_manager.cancel_executor(batch_execution_id)
        
        # 更新任务状态为已取消
        batch_execution.status = "cancelled"
        batch_execution.completed_at = beijing_now()
        batch_execution.updated_at = beijing_now()
        
        # 停止所有正在运行的测试用例
        running_test_cases = db.query(BatchExecutionTestCase).filter(
            BatchExecutionTestCase.batch_execution_id == batch_execution_id,
            BatchExecutionTestCase.status == "running"
        ).all()
        
        for btc in running_test_cases:
            btc.status = "cancelled"
            btc.completed_at = beijing_now()
            # 如果有对应的执行记录，也将其标记为取消
            if btc.execution_id:
                execution = db.query(TestExecution).filter(TestExecution.id == btc.execution_id).first()
                if execution:
                    execution.status = "cancelled"
                    execution.completed_at = beijing_now()
        
        # 将pending状态的测试用例也标记为取消
        pending_test_cases = db.query(BatchExecutionTestCase).filter(
            BatchExecutionTestCase.batch_execution_id == batch_execution_id,
            BatchExecutionTestCase.status == "pending"
        ).all()
        
        for btc in pending_test_cases:
            btc.status = "cancelled"
            btc.completed_at = beijing_now()
        
        # 更新统计信息
        cancelled_count = len(running_test_cases) + len(pending_test_cases)
        batch_execution.running_count = 0
        batch_execution.pending_count = 0
        batch_execution.failed_count += cancelled_count
        
        db.commit()
        
        # 推送WebSocket更新
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
            "message": "批量执行任务已停止"
        }

    @staticmethod
    async def _run_test_in_background(execution_id: int, test_case_id: int, headless: bool):
        """在后台运行单个测试"""
        try:
            result = await execute_single_test(test_case_id, headless)
            
            # 更新执行记录
            db = SessionLocal()
            try:
                execution = db.query(TestExecution).filter(TestExecution.id == execution_id).first()
                if execution:
                    execution.status = "passed" if result["success"] else "failed"
                    execution.overall_status = result.get("overall_status", "FAILED")
                    execution.total_duration = result.get("total_duration", 0)
                    execution.summary = result.get("summary", "")
                    execution.recommendations = result.get("recommendations", "")
                    execution.error_message = result.get("error_message", "")
                    execution.completed_at = beijing_now()
                    
                    # 更新统计信息
                    execution.total_steps = len(result.get("test_steps", []))
                    execution.passed_steps = len([s for s in result.get("test_steps", []) if s["status"] == "PASSED"])
                    execution.failed_steps = len([s for s in result.get("test_steps", []) if s["status"] == "FAILED"])
                    execution.skipped_steps = len([s for s in result.get("test_steps", []) if s["status"] == "SKIPPED"])
                    
                    db.commit()
            finally:
                db.close()
                
        except Exception as e:
            # 更新执行记录为错误状态
            db = SessionLocal()
            try:
                execution = db.query(TestExecution).filter(TestExecution.id == execution_id).first()
                if execution:
                    execution.status = "error"
                    execution.error_message = str(e)
                    execution.completed_at = beijing_now()
                    db.commit()
            finally:
                db.close()

    @staticmethod
    async def _run_batch_tests_in_background(test_case_ids: List[int], headless: bool):
        """在后台运行批量测试"""
        try:
            result = await execute_multiple_tests(test_case_ids, headless)
            # 批量测试的结果会通过单个测试的执行记录来查看
        except Exception as e:
            print(f"批量测试执行失败: {e}")

    @staticmethod
    async def _run_batch_execution_in_background(batch_execution_id: int, test_case_ids: List[int], headless: bool):
        """在后台运行批量执行任务"""
        try:
            # 创建并注册批量执行器
            batch_executor = await batch_executor_manager.create_executor(batch_execution_id, max_concurrent=5)
            result = await batch_executor.execute_batch_test(test_case_ids, headless, batch_execution_id=batch_execution_id)
            
            # 执行完成后移除执行器
            await batch_executor_manager.remove_executor(batch_execution_id)
            
            # 注意：不需要在这里更新批量执行任务状态，因为BatchTestExecutor已经处理了
            
        except Exception as e:
            # 更新批量执行任务为错误状态
            db = SessionLocal()
            try:
                batch_execution = db.query(BatchExecution).filter(BatchExecution.id == batch_execution_id).first()
                if batch_execution:
                    batch_execution.status = "failed"
                    batch_execution.completed_at = beijing_now()
                    batch_execution.updated_at = beijing_now()
                    db.commit()
                    
                    # 推送 WebSocket 更新
                    await websocket_manager.broadcast_batch_update(
                        batch_execution_id,
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
            finally:
                db.close()
            
            # 移除执行器
            await batch_executor_manager.remove_executor(batch_execution_id)