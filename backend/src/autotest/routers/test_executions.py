"""
测试执行路由
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from ..database import get_db, TestCase, TestExecution, TestStep
from ..models import (
    TestExecutionRequest, TestExecutionResponse, TestStepResponse,
    BatchExecutionRequest, BatchExecutionResponse
)
from ..services.execution_service import ExecutionService

router = APIRouter(prefix="/test-executions", tags=["测试执行"])

@router.post("/", response_model=TestExecutionResponse)
async def execute_test_case(
    execution_request: TestExecutionRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """执行单个测试用例"""
    return await ExecutionService.execute_single_test(execution_request, background_tasks, db)

@router.post("/batch", response_model=BatchExecutionResponse)
async def execute_multiple_test_cases(
    batch_request: BatchExecutionRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """批量执行测试用例"""
    return await ExecutionService.execute_batch_tests(batch_request, background_tasks, db)

@router.get("/", response_model=List[TestExecutionResponse])
async def get_test_executions(
    skip: int = 0,
    limit: int = 100,
    test_case_id: Optional[int] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """获取测试执行记录"""
    query = db.query(TestExecution)
    
    if test_case_id:
        query = query.filter(TestExecution.test_case_id == test_case_id)
    if status:
        query = query.filter(TestExecution.status == status)
    
    executions = query.order_by(TestExecution.created_at.desc()).offset(skip).limit(limit).all()
    return executions

@router.get("/{execution_id}", response_model=TestExecutionResponse)
async def get_test_execution(execution_id: int, db: Session = Depends(get_db)):
    """获取特定测试执行记录"""
    execution = db.query(TestExecution).filter(TestExecution.id == execution_id).first()
    if not execution:
        raise HTTPException(status_code=404, detail="执行记录不存在")
    return execution

@router.get("/{execution_id}/steps", response_model=List[TestStepResponse])
async def get_test_execution_steps(execution_id: int, db: Session = Depends(get_db)):
    """获取测试执行步骤详情"""
    steps = db.query(TestStep).filter(
        TestStep.execution_id == execution_id
    ).order_by(TestStep.step_order).all()
    return steps

@router.get("/test-cases/{test_case_id}/executions", response_model=List[TestExecutionResponse])
async def get_test_case_executions(
    test_case_id: int,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """获取测试用例的执行历史"""
    executions = db.query(TestExecution).filter(
        TestExecution.test_case_id == test_case_id
    ).order_by(TestExecution.created_at.desc()).offset(skip).limit(limit).all()
    return executions 