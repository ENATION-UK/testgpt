"""
统计信息路由
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db, TestCase, TestExecution
from ..models import TestStatistics

router = APIRouter(prefix="/statistics", tags=["统计信息"])

@router.get("/", response_model=TestStatistics)
async def get_test_statistics(db: Session = Depends(get_db)):
    """获取测试统计信息"""
    total_test_cases = db.query(TestCase).filter(TestCase.is_deleted == False).count()
    active_test_cases = db.query(TestCase).filter(
        TestCase.is_deleted == False,
        TestCase.status == "active"
    ).count()
    
    total_executions = db.query(TestExecution).count()
    passed_executions = db.query(TestExecution).filter(
        TestExecution.status == "passed"
    ).count()
    failed_executions = db.query(TestExecution).filter(
        TestExecution.status.in_(["failed", "error"])
    ).count()
    
    success_rate = (passed_executions / total_executions * 100) if total_executions > 0 else 0
    
    return TestStatistics(
        total_test_cases=total_test_cases,
        active_test_cases=active_test_cases,
        total_executions=total_executions,
        passed_executions=passed_executions,
        failed_executions=failed_executions,
        success_rate=round(success_rate, 2)
    ) 