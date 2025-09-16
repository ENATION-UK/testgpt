"""
数据模型定义
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

# 测试用例相关模型
class TestCaseCreate(BaseModel):
    name: str
    task_content: str
    status: str = "active"
    priority: str = "medium"
    category: Optional[str] = None
    category_id: Optional[int] = None
    tags: Optional[List[str]] = None
    expected_result: Optional[str] = None

class TestCaseUpdate(BaseModel):
    name: Optional[str] = None
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
    
    # 新增字段：Browser-Use事件详细信息
    url: Optional[str] = None
    actions: Optional[List[Dict[str, Any]]] = None
    evaluation: Optional[str] = None
    memory: Optional[str] = None
    next_goal: Optional[str] = None
    screenshot_data: Optional[str] = None
    event_timestamp: Optional[datetime] = None
    step_metadata: Optional[Dict[str, Any]] = None

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
    model_type: str = Field(description="模型类型: deepseek, openai, doubao")
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

# 多模型配置相关模型
class ModelProviderConfig(BaseModel):
    """单个模型提供商配置"""
    provider_id: str = Field(description="提供商ID，唯一标识")
    provider_name: str = Field(description="提供商名称")
    model_type: str = Field(description="模型类型: deepseek, openai, doubao")
    base_url: str = Field(description="API基础URL")
    model: str = Field(description="模型名称")
    temperature: float = Field(default=0.7, description="温度参数")
    max_tokens: Optional[int] = Field(default=None, description="最大token数")
    api_keys: List[str] = Field(description="API密钥列表")
    rate_limit: int = Field(default=2, description="限流数量")
    is_active: bool = Field(default=True, description="是否启用")
    current_key_index: int = Field(default=0, description="当前使用的密钥索引")

class MultiModelConfig(BaseModel):
    """多模型配置"""
    providers: List[ModelProviderConfig] = Field(description="模型提供商配置列表")
    current_provider_index: int = Field(default=0, description="当前使用的提供商索引")

class MultiModelConfigResponse(BaseModel):
    """多模型配置响应"""
    providers: List[ModelProviderConfig]
    current_provider_index: int
    total_providers: int
    total_api_keys: int
    is_valid: bool = Field(description="配置是否有效")

class LLMRequestConfig(BaseModel):
    """LLM请求配置"""
    provider_id: str
    model_type: str
    api_key: str
    base_url: str
    model: str
    temperature: float
    max_tokens: Optional[int] = None

# Excel导入任务相关模型
class ImportTaskCreate(BaseModel):
    """创建导入任务"""
    name: str = Field(description="任务名称")
    file_name: str = Field(description="Excel文件名")
    import_mode: str = Field(default="smart", description="导入模式: standard(标准模版) 或 smart(智能识别)")
    import_options: Dict[str, Any] = Field(description="导入选项")
    batch_size: int = Field(default=10, description="批次大小")

class ImportTaskResponse(BaseModel):
    """导入任务响应"""
    id: int
    name: str
    file_name: str
    status: str
    import_mode: Optional[str] = "smart"
    total_rows: int
    processed_rows: int
    success_rows: int
    failed_rows: int
    current_batch: int
    total_batches: int
    progress_percentage: float
    import_options: Optional[Dict[str, Any]] = None
    error_log: Optional[List[Dict[str, Any]]] = None
    result_summary: Optional[Dict[str, Any]] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class ImportTaskStatus(BaseModel):
    """导入任务状态"""
    task_id: int
    status: str
    progress_percentage: float
    current_batch: int
    total_batches: int
    processed_rows: int
    total_rows: int
    success_rows: int
    failed_rows: int
    error_messages: List[str] = []

class ImportTaskListResponse(BaseModel):
    """导入任务列表响应"""
    tasks: List[ImportTaskResponse]
    total: int
    has_running_task: bool 