"""
FastAPI application with complete REST API for web automation testing
"""

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, UploadFile, File, Form
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
import pandas as pd
import io
from browser_use.llm.deepseek.chat import ChatDeepSeek
from browser_use.llm.messages import SystemMessage, UserMessage, ContentPartTextParam

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

@app.post("/test-cases/preview-excel")
async def preview_excel_file(file: UploadFile = File(...)):
    """预览Excel文件内容"""
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="只支持Excel文件格式")
    
    try:
        # 读取Excel文件
        content = await file.read()
        df = pd.read_excel(io.BytesIO(content))
        
        # 处理NaN值
        df = df.fillna('')
        
        # 转换为字典列表
        data = df.to_dict('records')
        
        # 返回前5行作为预览
        preview = data[:5] if len(data) > 5 else data
        
        return {"preview": preview, "total_rows": len(data)}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"读取Excel文件失败: {str(e)}")

@app.post("/test-cases/import-excel")
async def import_excel_file(
    file: UploadFile = File(...),
    options: str = Form(...),
    db: Session = Depends(get_db)
):
    """导入Excel文件中的测试用例"""
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="只支持Excel文件格式")
    
    try:
        # 解析导入选项
        import_options = json.loads(options)
        
        # 读取Excel文件
        content = await file.read()
        df = pd.read_excel(io.BytesIO(content))
        
        # 处理NaN值
        df = df.fillna('')
        
        # 使用大模型分析Excel内容并转换为测试用例格式
        test_cases = await analyze_excel_with_llm(df, import_options)
        
        # 批量创建测试用例
        created_count = 0
        for test_case_data in test_cases:
            try:
                db_test_case = TestCase(**test_case_data)
                db.add(db_test_case)
                created_count += 1
            except Exception as e:
                print(f"创建测试用例失败: {e}")
                continue
        
        db.commit()
        
        return {
            "success": True,
            "imported_count": created_count,
            "total_rows": len(df),
            "message": f"成功导入 {created_count} 个测试用例"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"导入Excel文件失败: {str(e)}")

def _load_model_config() -> dict:
    """加载模型配置"""
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
        return config
    except Exception as e:
        print(f"加载模型配置失败: {e}")
        # 返回默认配置
        return {
            "model_type": "deepseek",
            "api_key": os.getenv("DEEPSEEK_API_KEY", ""),
            "base_url": "https://api.deepseek.com/v1",
            "model": "deepseek-chat",
            "temperature": 0.7,
            "max_tokens": None
        }

async def analyze_excel_with_llm(df: pd.DataFrame, import_options: dict) -> List[dict]:
    """使用大模型分析Excel内容并转换为测试用例格式"""
    try:
        # 加载模型配置
        config = _load_model_config()
        
        # 检查配置有效性
        if not config.get("api_key"):
            print("警告: 模型配置中缺少API密钥，使用备用转换逻辑")
            return convert_excel_to_test_cases(df, import_options)

        # 将DataFrame转换为字符串格式
        excel_content = df.to_string(index=False)
        
        # 构建提示词
        prompt = f"""
请分析以下Excel表格内容，并将其转换为测试用例格式。

Excel内容：
{excel_content}

导入选项：
- 默认状态: {import_options.get('defaultStatus', 'active')}
- 默认优先级: {import_options.get('defaultPriority', 'medium')}
- 默认分类: {import_options.get('defaultCategory', '导入')}

请将Excel中的每一行转换为一个测试用例，格式如下：
{{
    "name": "测试用例名称",
    "description": "测试用例描述",
    "task_content": "具体的测试任务内容",
    "status": "active/inactive/draft",
    "priority": "low/medium/high/critical",
    "category": "分类名称",
    "tags": ["标签1", "标签2"],
    "expected_result": "期望结果"
}}

请返回JSON格式的测试用例列表，每个测试用例包含上述所有字段。
如果Excel中没有某些字段，请使用导入选项中的默认值。
"""
        print("即将发送给大模型的提示词如下：")
        print(prompt)

        # 根据模型类型创建相应的聊天实例
        if config.get("model_type") == "deepseek":
            # 创建DeepSeek聊天实例
            chat_config = {
                'base_url': config.get('base_url', 'https://api.deepseek.com/v1'),
                'model': config.get('model', 'deepseek-chat'),
                'api_key': config.get('api_key'),
            }
            
            # 添加可选参数
            if config.get('temperature') is not None:
                chat_config['temperature'] = config.get('temperature')
            if config.get('max_tokens') is not None:
                chat_config['max_tokens'] = config.get('max_tokens')
            
            deepseek_chat = ChatDeepSeek(**chat_config)
            
            messages = [
                SystemMessage(content=[ContentPartTextParam(text="你是一个测试用例分析专家")]),
                UserMessage(content=prompt)
            ]
            
            print("🚀 调用大模型...")
            response = await deepseek_chat.ainvoke(messages)
            llm_response = response.completion
            
        else:
            raise Exception(f"暂不支持的模型类型: {config.get('model_type')}")
        
        # 解析响应
        try:
            # 尝试从响应中提取JSON
            import re
            json_match = re.search(r'\[.*\]', llm_response, re.DOTALL)
            if json_match:
                test_cases = json.loads(json_match.group())
            else:
                # 如果无法解析JSON，使用简单的转换逻辑
                test_cases = convert_excel_to_test_cases(df, import_options)
        except Exception as e:
            print(f"JSON解析失败: {e}")
            # 如果JSON解析失败，使用简单的转换逻辑
            test_cases = convert_excel_to_test_cases(df, import_options)
        
        return test_cases
        
    except Exception as e:
        print(f"大模型分析失败: {e}")
        # 如果大模型分析失败，使用简单的转换逻辑
        return convert_excel_to_test_cases(df, import_options)

def convert_excel_to_test_cases(df: pd.DataFrame, import_options: dict) -> List[dict]:
    """智能的Excel到测试用例转换逻辑"""
    test_cases = []
    
    for _, row in df.iterrows():
        # 智能识别列名并提取信息
        name = str(row.get('标题', row.get('name', row.get('名称', row.get('Name', f'测试用例_{len(test_cases) + 1}')))))
        description = str(row.get('前置条件', row.get('description', row.get('描述', row.get('Description', '')))))
        task_content = str(row.get('步骤描述', row.get('task_content', row.get('任务内容', row.get('Task', row.get('内容', ''))))))
        expected_result = str(row.get('预期结果', row.get('expected_result', row.get('期望结果', row.get('Expected Result', '')))))
        
        # 根据内容智能判断分类
        category = import_options.get('defaultCategory', '导入')
        if '组合商品' in name or '组合商品' in task_content:
            category = '组合商品功能'
        elif '会员' in name or '会员' in task_content:
            category = '会员管理'
        elif '首页' in name or '首页' in task_content:
            category = '首页功能'
        elif '分类' in name or '分类' in task_content:
            category = '分类管理'
        
        # 根据内容智能判断优先级
        priority = import_options.get('defaultPriority', 'medium')
        if any(keyword in name.lower() for keyword in ['紧急', '重要', '核心', 'critical']):
            priority = 'critical'
        elif any(keyword in name.lower() for keyword in ['高', 'high']):
            priority = 'high'
        elif any(keyword in name.lower() for keyword in ['低', 'low']):
            priority = 'low'
        
        # 根据内容智能判断状态
        status = import_options.get('defaultStatus', 'active')
        if any(keyword in name.lower() for keyword in ['草稿', 'draft']):
            status = 'draft'
        elif any(keyword in name.lower() for keyword in ['非激活', 'inactive']):
            status = 'inactive'
        
        # 生成标签
        tags = []
        if '登录' in task_content:
            tags.append('登录功能')
        if '搜索' in task_content:
            tags.append('搜索功能')
        if '审核' in task_content:
            tags.append('审核功能')
        if '发布' in task_content:
            tags.append('发布功能')
        if '编辑' in task_content:
            tags.append('编辑功能')
        if '删除' in task_content:
            tags.append('删除功能')
        
        test_case = {
            "name": name,
            "description": description,
            "task_content": task_content,
            "status": status,
            "priority": priority,
            "category": category,
            "tags": tags,
            "expected_result": expected_result
        }
        
        test_cases.append(test_case)
    
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