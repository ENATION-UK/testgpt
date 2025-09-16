"""
测试执行路由
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from ..database import get_db, TestCase, TestExecution, TestStep, BatchExecution, BatchExecutionTestCase
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
    """获取测试执行记录列表"""
    query = db.query(TestExecution)
    
    if test_case_id:
        query = query.filter(TestExecution.test_case_id == test_case_id)
    if status:
        query = query.filter(TestExecution.status == status)
    
    executions = query.order_by(TestExecution.created_at.desc()).offset(skip).limit(limit).all()
    return executions

# 批量执行任务相关路由 - 必须在通用路由之前定义
@router.post("/batch-executions", response_model=dict)
async def create_batch_execution(
    batch_request: BatchExecutionRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """创建批量执行任务"""
    return await ExecutionService.create_batch_execution(batch_request, background_tasks, db)

@router.get("/batch-executions", response_model=List[dict])
async def get_batch_executions(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """获取批量执行任务列表"""
    query = db.query(BatchExecution)
    
    if status:
        query = query.filter(BatchExecution.status == status)
    
    batch_executions = query.order_by(BatchExecution.created_at.desc()).offset(skip).limit(limit).all()
    
    # 转换为字典格式
    result = []
    for batch in batch_executions:
        result.append({
            "id": batch.id,
            "name": batch.name,
            "status": batch.status,
            "total_count": batch.total_count,
            "success_count": batch.success_count,
            "failed_count": batch.failed_count,
            "running_count": batch.running_count,
            "pending_count": batch.pending_count,
            "total_duration": batch.total_duration,
            "headless": batch.headless,
            "started_at": batch.started_at.isoformat() if batch.started_at else None,
            "completed_at": batch.completed_at.isoformat() if batch.completed_at else None,
            "created_at": batch.created_at.isoformat() if batch.created_at else None,
            "updated_at": batch.updated_at.isoformat() if batch.updated_at else None
        })
    
    return result

@router.get("/batch-executions/{batch_execution_id}", response_model=dict)
async def get_batch_execution(batch_execution_id: int, db: Session = Depends(get_db)):
    """获取特定批量执行任务的详细信息"""
    batch_execution = db.query(BatchExecution).filter(BatchExecution.id == batch_execution_id).first()
    if not batch_execution:
        raise HTTPException(status_code=404, detail="批量执行任务不存在")
    
    # 获取批量执行任务中的测试用例详情
    batch_test_cases = db.query(BatchExecutionTestCase).filter(
        BatchExecutionTestCase.batch_execution_id == batch_execution_id
    ).all()
    
    # 获取测试用例信息
    test_cases_info = []
    for btc in batch_test_cases:
        test_case = db.query(TestCase).filter(TestCase.id == btc.test_case_id).first()
        test_case_info = {
            "test_case_id": btc.test_case_id,
            "test_case_name": test_case.name if test_case else "未知测试用例",
            "status": btc.status,
            "started_at": btc.started_at.isoformat() if btc.started_at else None,
            "completed_at": btc.completed_at.isoformat() if btc.completed_at else None,
            "execution_id": btc.execution_id
        }
        test_cases_info.append(test_case_info)
    
    return {
        "id": batch_execution.id,
        "name": batch_execution.name,
        "status": batch_execution.status,
        "total_count": batch_execution.total_count,
        "success_count": batch_execution.success_count,
        "failed_count": batch_execution.failed_count,
        "running_count": batch_execution.running_count,
        "pending_count": batch_execution.pending_count,
        "total_duration": batch_execution.total_duration,
        "headless": batch_execution.headless,
        "started_at": batch_execution.started_at.isoformat() if batch_execution.started_at else None,
        "completed_at": batch_execution.completed_at.isoformat() if batch_execution.completed_at else None,
        "created_at": batch_execution.created_at.isoformat() if batch_execution.created_at else None,
        "updated_at": batch_execution.updated_at.isoformat() if batch_execution.updated_at else None,
        "test_cases": test_cases_info
    }

@router.post("/batch-executions/{batch_execution_id}/start", response_model=dict)
async def start_batch_execution(
    batch_execution_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """启动批量执行任务"""
    return await ExecutionService.start_batch_execution(batch_execution_id, background_tasks, db)

@router.post("/batch-executions/{batch_execution_id}/stop", response_model=dict)
async def stop_batch_execution(
    batch_execution_id: int,
    db: Session = Depends(get_db)
):
    """停止批量执行任务"""
    return await ExecutionService.stop_batch_execution(batch_execution_id, db)

# 通用路由 - 必须在特定路由之后定义
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


@router.get("/batch-executions/{batch_execution_id}/test-cases", response_model=dict)
async def get_batch_execution_test_cases(
    batch_execution_id: int,
    skip: int = 0,
    limit: int = 20,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """获取批量执行任务中的测试用例详情（支持分页和搜索）"""
    batch_execution = db.query(BatchExecution).filter(BatchExecution.id == batch_execution_id).first()
    if not batch_execution:
        raise HTTPException(status_code=404, detail="批量执行任务不存在")
    
    # 构建查询
    query = db.query(BatchExecutionTestCase).filter(
        BatchExecutionTestCase.batch_execution_id == batch_execution_id
    )
    
    # 如果有搜索关键词，添加搜索条件
    if search:
        # 获取测试用例名称匹配的测试用例ID
        test_case_ids = db.query(TestCase.id).filter(
            TestCase.name.contains(search)
        ).all()
        test_case_ids = [tc[0] for tc in test_case_ids]
        
        # 添加测试用例ID过滤条件
        query = query.filter(BatchExecutionTestCase.test_case_id.in_(test_case_ids))
    
    # 获取总数
    total = query.count()
    
    # 应用分页
    batch_test_cases = query.offset(skip).limit(limit).all()
    
    # 获取测试用例信息
    test_cases_info = []
    for btc in batch_test_cases:
        test_case = db.query(TestCase).filter(TestCase.id == btc.test_case_id).first()
        
        # 获取执行记录的详细信息（包括整体状态等）
        overall_status = None
        if btc.execution_id:
            execution = db.query(TestExecution).filter(TestExecution.id == btc.execution_id).first()
            overall_status = execution.overall_status if execution else None
        
        test_case_info = {
            "id": btc.id,
            "batch_execution_id": btc.batch_execution_id,
            "test_case_id": btc.test_case_id,
            "execution_id": btc.execution_id,
            "status": btc.status,
            "overall_status": overall_status,
            "started_at": btc.started_at.isoformat() if btc.started_at else None,
            "completed_at": btc.completed_at.isoformat() if btc.completed_at else None,
            "test_case_name": test_case.name if test_case else "未知测试用例"
        }
        test_cases_info.append(test_case_info)
    
    return {
        "test_cases": test_cases_info,
        "total": total,
        "skip": skip,
        "limit": limit
    }
