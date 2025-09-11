"""
测试结果模型
"""
from typing import Optional
from pydantic import BaseModel, Field

class TestStepResult(BaseModel):
    """单个测试步骤的结果"""
    step_name: str = Field(description="测试步骤名称")
    status: str = Field(description="测试状态: PASSED, FAILED, SKIPPED")
    description: str = Field(description="步骤描述")
    error_message: Optional[str] = Field(default=None, description="如果失败，错误信息")
    screenshot_path: Optional[str] = Field(default=None, description="相关截图路径")
    duration_seconds: Optional[float] = Field(default=None, description="执行时间")

class ControllerTestResult(BaseModel):
    """用于Controller的简化测试结果模型"""
    test_name: str = Field(description="测试名称")
    overall_status: str = Field(description="整体测试状态: PASSED, FAILED, PARTIAL")
    total_steps: int = Field(description="总步骤数")
    passed_steps: int = Field(description="通过的步骤数")
    failed_steps: int = Field(description="失败的步骤数")
    skipped_steps: int = Field(description="跳过的步骤数")
    total_duration: float = Field(description="总执行时间(秒)")
    summary: str = Field(description="测试总结")
    recommendations: Optional[str] = Field(default=None, description="改进建议")

class TestResult(BaseModel):
    """完整的测试结果"""
    test_name: str = Field(description="测试名称")
    overall_status: str = Field(description="整体测试状态: PASSED, FAILED, PARTIAL")
    total_steps: int = Field(description="总步骤数")
    passed_steps: int = Field(description="通过的步骤数")
    failed_steps: int = Field(description="失败的步骤数")
    skipped_steps: int = Field(description="跳过的步骤数")
    total_duration: float = Field(description="总执行时间(秒)")
    summary: str = Field(description="测试总结")
    recommendations: Optional[str] = Field(default=None, description="改进建议")
