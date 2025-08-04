"""
测试执行服务
"""

from fastapi import HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List
import asyncio

from ..database import TestCase, TestExecution, TestStep, SessionLocal, BatchExecution, BatchExecutionTestCase
from ..models import TestExecutionRequest, TestExecutionResponse, BatchExecutionRequest, BatchExecutionResponse
from ..test_executor import execute_single_test, execute_multiple_tests, BatchTestExecutor

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
            execution_name=f"{test_case.name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            status="running",
            started_at=datetime.utcnow()
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
        
        # 创建批量执行任务记录
        batch_execution = BatchExecution(
            name=f"批量执行任务_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            status="running",
            total_count=len(batch_request.test_case_ids),
            pending_count=len(batch_request.test_case_ids),
            started_at=datetime.utcnow()
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
        
        # 在后台执行批量测试
        background_tasks.add_task(
            ExecutionService._run_batch_execution_in_background,
            batch_execution.id,
            batch_request.test_case_ids,
            batch_request.headless
        )
        
        return {
            "success": True,
            "batch_execution_id": batch_execution.id,
            "message": "批量执行任务已创建并开始执行"
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
                    execution.completed_at = datetime.utcnow()
                    
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
                    execution.completed_at = datetime.utcnow()
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
            # 使用BatchTestExecutor执行批量测试
            batch_executor = BatchTestExecutor()
            result = await batch_executor.execute_batch_test(test_case_ids, headless)
            
            # 更新批量执行任务状态
            db = SessionLocal()
            try:
                batch_execution = db.query(BatchExecution).filter(BatchExecution.id == batch_execution_id).first()
                if batch_execution:
                    batch_execution.status = "completed"
                    batch_execution.completed_at = datetime.utcnow()
                    batch_execution.updated_at = datetime.utcnow()
                    db.commit()
            finally:
                db.close()
                
        except Exception as e:
            # 更新批量执行任务为错误状态
            db = SessionLocal()
            try:
                batch_execution = db.query(BatchExecution).filter(BatchExecution.id == batch_execution_id).first()
                if batch_execution:
                    batch_execution.status = "failed"
                    batch_execution.completed_at = datetime.utcnow()
                    batch_execution.updated_at = datetime.utcnow()
                    db.commit()
            finally:
                db.close()