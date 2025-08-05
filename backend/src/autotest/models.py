"""
数据模型定义
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

# 测试用例相关模型
class TestCaseCreate(BaseModel):
    name: str
    description: Optional[str] = None
    task_content: str
    status: str = "active"
    priority: str = "medium"
    category: Optional[str] = None
    category_id: Optional[int] = None
    tags: Optional[List[str]] = None
    expected_result: Optional[str] = None

class TestCaseUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    task_content: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    category: Optional[str] = None
    category_id: Optional[int] = None
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
    category_id: Optional[int] = None
    tags: Optional[List[str]] = None
    expected_result: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# 分类相关模型
class CategoryCreate(BaseModel):
    name: str
    description: Optional[str] = None
    parent_id: Optional[int] = None
    sort_order: int = 0

class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    parent_id: Optional[int] = None
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None

class CategoryResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    parent_id: Optional[int] = None
    level: int
    sort_order: int
    is_active: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    children: Optional[List['CategoryResponse']] = []
    test_case_count: Optional[int] = 0

    class Config:
        from_attributes = True

# 分类树形结构响应
class CategoryTreeResponse(BaseModel):
    categories: List[CategoryResponse]
    total_count: int

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

# 提示词配置相关模型
class PromptConfig(BaseModel):
    """提示词配置"""
    custom_prompt: str = Field(default="", description="自定义提示词")

class PromptConfigResponse(BaseModel):
    """提示词配置响应"""
    custom_prompt: str
    is_valid: bool = Field(description="配置是否有效") 