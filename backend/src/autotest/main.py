"""
FastAPI application with complete REST API for web automation testing
"""

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime
import uvicorn
import asyncio
import json
from pathlib import Path
import os

from .database import (
    get_db, TestCase, TestExecution, TestStep, TestSuite, TestSuiteCase,
    init_db, SessionLocal
)
from .test_executor import TestExecutor, execute_single_test, execute_multiple_tests

# 创建FastAPI应用实例
app = FastAPI(
    title="AutoTest API",
    description="Web自动化测试工具API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== 数据模型 ====================

# 测试用例相关模型
class TestCaseCreate(BaseModel):
    name: str
    description: Optional[str] = None
    task_content: str
    status: str = "active"
    priority: str = "medium"
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    expected_result: Optional[str] = None

class TestCaseUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    task_content: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    expected_result: Optional[str] = None

class TestCaseResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    task_content: str
    status: str
    priority: str
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    expected_result: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# 测试执行相关模型
class TestExecutionRequest(BaseModel):
    test_case_id: int
    headless: bool = False

class TestExecutionResponse(BaseModel):
    id: int
    test_case_id: int
    execution_name: str
    status: str
    overall_status: Optional[str] = None
    total_steps: int
    passed_steps: int
    failed_steps: int
    skipped_steps: int
    total_duration: Optional[float] = None
    summary: Optional[str] = None
    recommendations: Optional[str] = None
    error_message: Optional[str] = None
    started_at: datetime
    completed_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True

class TestStepResponse(BaseModel):
    id: int
    execution_id: int
    step_name: str
    step_order: int
    status: str
    description: Optional[str] = None
    error_message: Optional[str] = None
    screenshot_path: Optional[str] = None
    duration_seconds: Optional[float] = None
    started_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# 批量执行模型
class BatchExecutionRequest(BaseModel):
    test_case_ids: List[int]
    headless: bool = False

class BatchExecutionResponse(BaseModel):
    success: bool
    total_count: int
    passed_count: int
    failed_count: int
    results: List[Dict[str, Any]]

# 统计信息模型
class TestStatistics(BaseModel):
    total_test_cases: int
    active_test_cases: int
    total_executions: int
    passed_executions: int
    failed_executions: int
    success_rate: float

# 模型配置相关模型
class ModelConfig(BaseModel):
    """模型配置"""
    model_type: str = Field(description="模型类型: deepseek, openai")
    api_key: str = Field(description="API密钥")
    base_url: Optional[str] = Field(default=None, description="API基础URL")
    model: str = Field(description="模型名称")
    temperature: float = Field(default=0.7, description="温度参数")
    max_tokens: Optional[int] = Field(default=None, description="最大token数")

class ModelConfigResponse(BaseModel):
    """模型配置响应"""
    model_type: str
    api_key: str
    base_url: Optional[str] = None
    model: str
    temperature: float
    max_tokens: Optional[int] = None
    is_valid: bool = Field(description="配置是否有效")

# ==================== API端点 ====================

@app.get("/")
async def root():
    """根路径，返回欢迎信息"""
    return {
        "message": "Welcome to AutoTest API!",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }

@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {
        "status": "healthy",
        "service": "autotest-api",
        "timestamp": datetime.utcnow()
    }

# ==================== 测试用例管理 ====================

@app.get("/test-cases", response_model=List[TestCaseResponse])
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

@app.get("/test-cases/{test_case_id}", response_model=TestCaseResponse)
async def get_test_case(test_case_id: int, db: Session = Depends(get_db)):
    """获取特定测试用例"""
    test_case = db.query(TestCase).filter(
        TestCase.id == test_case_id,
        TestCase.is_deleted == False
    ).first()
    if not test_case:
        raise HTTPException(status_code=404, detail="测试用例不存在")
    return test_case

@app.post("/test-cases", response_model=TestCaseResponse)
async def create_test_case(test_case: TestCaseCreate, db: Session = Depends(get_db)):
    """创建新测试用例"""
    db_test_case = TestCase(**test_case.dict())
    db.add(db_test_case)
    db.commit()
    db.refresh(db_test_case)
    return db_test_case

@app.put("/test-cases/{test_case_id}", response_model=TestCaseResponse)
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

@app.delete("/test-cases/{test_case_id}")
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

@app.get("/test-cases/status/{status}")
async def get_test_cases_by_status(status: str, db: Session = Depends(get_db)):
    """根据状态获取测试用例"""
    test_cases = db.query(TestCase).filter(
        TestCase.status == status,
        TestCase.is_deleted == False
    ).all()
    return test_cases

@app.get("/test-cases/category/{category}")
async def get_test_cases_by_category(category: str, db: Session = Depends(get_db)):
    """根据分类获取测试用例"""
    test_cases = db.query(TestCase).filter(
        TestCase.category == category,
        TestCase.is_deleted == False
    ).all()
    return test_cases

# ==================== 测试执行 ====================

@app.post("/test-executions", response_model=TestExecutionResponse)
async def execute_test_case(
    execution_request: TestExecutionRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
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
        run_test_in_background,
        execution.id,
        execution_request.test_case_id,
        execution_request.headless
    )
    
    return execution

@app.post("/test-executions/batch", response_model=BatchExecutionResponse)
async def execute_multiple_test_cases(
    batch_request: BatchExecutionRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
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
        run_batch_tests_in_background,
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

@app.get("/test-executions", response_model=List[TestExecutionResponse])
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

@app.get("/test-executions/{execution_id}", response_model=TestExecutionResponse)
async def get_test_execution(execution_id: int, db: Session = Depends(get_db)):
    """获取特定测试执行记录"""
    execution = db.query(TestExecution).filter(TestExecution.id == execution_id).first()
    if not execution:
        raise HTTPException(status_code=404, detail="执行记录不存在")
    return execution

@app.get("/test-executions/{execution_id}/steps", response_model=List[TestStepResponse])
async def get_test_execution_steps(execution_id: int, db: Session = Depends(get_db)):
    """获取测试执行步骤详情"""
    steps = db.query(TestStep).filter(
        TestStep.execution_id == execution_id
    ).order_by(TestStep.step_order).all()
    return steps

@app.get("/test-cases/{test_case_id}/executions", response_model=List[TestExecutionResponse])
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

# ==================== 统计信息 ====================

@app.get("/statistics", response_model=TestStatistics)
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

# ==================== 模型配置 ====================

@app.get("/model-config", response_model=ModelConfigResponse)
async def get_model_config():
    """获取当前模型配置"""
    try:
        config_path = Path("model_config.json")
        if config_path.exists():
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
        else:
            # 默认配置
            config = {
                "model_type": "deepseek",
                "api_key": os.getenv("DEEPSEEK_API_KEY", ""),
                "base_url": "https://api.deepseek.com/v1",
                "model": "deepseek-chat",
                "temperature": 0.7,
                "max_tokens": None
            }
        
        # 验证配置有效性
        is_valid = bool(config.get("api_key"))
        
        return ModelConfigResponse(
            **config,
            is_valid=is_valid
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取模型配置失败: {str(e)}")

@app.put("/model-config", response_model=ModelConfigResponse)
async def update_model_config(config: ModelConfig):
    """更新模型配置"""
    try:
        config_path = Path("model_config.json")
        
        # 保存配置到文件
        config_data = config.dict()
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config_data, f, ensure_ascii=False, indent=2)
        
        # 验证配置有效性
        is_valid = bool(config.api_key)
        
        return ModelConfigResponse(
            **config_data,
            is_valid=is_valid
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新模型配置失败: {str(e)}")

@app.post("/model-config/test")
async def test_model_config(config: ModelConfig):
    """测试模型配置"""
    try:
        from .browser_agent import BrowserAgent
        
        # 创建临时代理测试配置
        agent = BrowserAgent(
            model_type=config.model_type,
            api_key=config.api_key,
            base_url=config.base_url,
            model=config.model
        )
        
        # 尝试初始化LLM
        llm = agent._init_llm()
        
        return {
            "success": True,
            "message": "模型配置测试成功"
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"模型配置测试失败: {str(e)}"
        }

# ==================== 后台任务 ====================

async def run_test_in_background(execution_id: int, test_case_id: int, headless: bool):
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

async def run_batch_tests_in_background(test_case_ids: List[int], headless: bool):
    """在后台运行批量测试"""
    try:
        result = await execute_multiple_tests(test_case_ids, headless)
        # 批量测试的结果会通过单个测试的执行记录来查看
    except Exception as e:
        print(f"批量测试执行失败: {e}")

# ==================== 应用启动事件 ====================

@app.on_event("startup")
async def startup_event():
    """应用启动时初始化数据库"""
    init_db()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000) 