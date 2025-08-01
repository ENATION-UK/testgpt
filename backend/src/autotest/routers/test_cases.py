"""
测试用例管理路由
"""

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
import pandas as pd
import io
import json

from ..database import get_db, TestCase
from ..models import TestCaseCreate, TestCaseUpdate, TestCaseResponse
from ..services.excel_service import ExcelService

router = APIRouter(prefix="/test-cases", tags=["测试用例管理"])

@router.get("/", response_model=List[TestCaseResponse])
async def get_test_cases(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    category: Optional[str] = None,
    priority: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """获取测试用例列表"""
    query = db.query(TestCase).filter(TestCase.is_deleted == False)
    
    if status:
        query = query.filter(TestCase.status == status)
    if category:
        query = query.filter(TestCase.category == category)
    if priority:
        query = query.filter(TestCase.priority == priority)
    
    test_cases = query.offset(skip).limit(limit).all()
    return test_cases

@router.get("/{test_case_id}", response_model=TestCaseResponse)
async def get_test_case(test_case_id: int, db: Session = Depends(get_db)):
    """获取特定测试用例"""
    test_case = db.query(TestCase).filter(
        TestCase.id == test_case_id,
        TestCase.is_deleted == False
    ).first()
    if not test_case:
        raise HTTPException(status_code=404, detail="测试用例不存在")
    return test_case

@router.post("/", response_model=TestCaseResponse)
async def create_test_case(test_case: TestCaseCreate, db: Session = Depends(get_db)):
    """创建新测试用例"""
    db_test_case = TestCase(**test_case.dict())
    db.add(db_test_case)
    db.commit()
    db.refresh(db_test_case)
    return db_test_case

@router.put("/{test_case_id}", response_model=TestCaseResponse)
async def update_test_case(
    test_case_id: int,
    test_case: TestCaseUpdate,
    db: Session = Depends(get_db)
):
    """更新测试用例"""
    db_test_case = db.query(TestCase).filter(
        TestCase.id == test_case_id,
        TestCase.is_deleted == False
    ).first()
    if not db_test_case:
        raise HTTPException(status_code=404, detail="测试用例不存在")
    
    update_data = test_case.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_test_case, field, value)
    
    db.commit()
    db.refresh(db_test_case)
    return db_test_case

@router.delete("/{test_case_id}")
async def delete_test_case(test_case_id: int, db: Session = Depends(get_db)):
    """删除测试用例（软删除）"""
    db_test_case = db.query(TestCase).filter(
        TestCase.id == test_case_id,
        TestCase.is_deleted == False
    ).first()
    if not db_test_case:
        raise HTTPException(status_code=404, detail="测试用例不存在")
    
    db_test_case.is_deleted = True
    db.commit()
    return {"message": f"测试用例 {db_test_case.name} 已删除"}

@router.get("/status/{status}")
async def get_test_cases_by_status(status: str, db: Session = Depends(get_db)):
    """根据状态获取测试用例"""
    test_cases = db.query(TestCase).filter(
        TestCase.status == status,
        TestCase.is_deleted == False
    ).all()
    return test_cases

@router.get("/category/{category}")
async def get_test_cases_by_category(category: str, db: Session = Depends(get_db)):
    """根据分类获取测试用例"""
    test_cases = db.query(TestCase).filter(
        TestCase.category == category,
        TestCase.is_deleted == False
    ).all()
    return test_cases

@router.post("/preview-excel")
async def preview_excel_file(file: UploadFile = File(...)):
    """预览Excel文件内容"""
    return await ExcelService.preview_excel(file)

@router.post("/import-excel")
async def import_excel_file(
    file: UploadFile = File(...),
    options: str = Form(...),
    db: Session = Depends(get_db)
):
    """导入Excel文件中的测试用例"""
    return await ExcelService.import_excel(file, options, db) 