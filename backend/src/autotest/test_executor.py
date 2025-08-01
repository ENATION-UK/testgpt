"""
测试执行服务
负责执行测试用例并记录结果
"""

import asyncio
import base64
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

from browser_use.llm import ChatDeepSeek
from browser_use.controller.service import Controller
from playwright.async_api import async_playwright

from .database import TestCase, TestExecution, TestStep, SessionLocal

# 测试结果模型
class TestStepResult(BaseModel):
    """单个测试步骤的结果"""
    step_name: str = Field(description="测试步骤名称")
    status: str = Field(description="测试状态: PASSED, FAILED, SKIPPED")
    description: str = Field(description="步骤描述")
    error_message: Optional[str] = Field(default=None, description="如果失败，错误信息")
    screenshot_path: Optional[str] = Field(default=None, description="相关截图路径")
    duration_seconds: Optional[float] = Field(default=None, description="执行时间")

class TestResult(BaseModel):
    """完整的测试结果"""
    test_name: str = Field(description="测试名称")
    overall_status: str = Field(description="整体测试状态: PASSED, FAILED, PARTIAL")
    total_steps: int = Field(description="总步骤数")
    passed_steps: int = Field(description="通过的步骤数")
    failed_steps: int = Field(description="失败的步骤数")
    skipped_steps: int = Field(description="跳过的步骤数")
    total_duration: float = Field(description="总执行时间(秒)")
    test_steps: List[TestStepResult] = Field(description="详细的测试步骤")
    summary: str = Field(description="测试总结")
    recommendations: Optional[str] = Field(default=None, description="改进建议")

# 测试系统提示词
TEST_SYSTEM_PROMPT = """
你是一个专业的Web自动化测试专家。你的任务是执行Web测试并生成详细的测试报告。

## 测试执行规则：
1. 严格按照测试用例执行每个步骤
2. 每个步骤都要验证预期结果
3. 如果步骤失败，记录详细的错误信息
4. 为每个关键步骤截图作为证据
5. 记录每个步骤的执行时间

## 测试结果要求：
1. 必须明确标注每个步骤的PASSED/FAILED状态
2. 失败时必须提供具体的错误原因
3. 提供清晰的测试总结
4. 如果有失败，给出改进建议

## 故障处理指南：
重要: 如果你多次（连续 3 次及以上失败）未能成功执行同一操作，调用 done 并将 success 设置为 false，同时说明问题所在。
1.如果某个操作反复失败（出现相同的错误模式），不要无限重试。
2.对同一操作尝试 2 - 3 次失败后，考虑其他方法，或者调用 done 并将 success 设置为 false。
3.在 done 操作文本中记录你尝试了什么以及失败的原因。
4.如果你陷入循环或毫无进展，立即调用 done。

## 验证标准：
- 页面元素存在且可交互
- 功能按预期工作
- 页面状态正确
- 错误处理正常

记住：你的输出必须是结构化的测试报告，包含详细的成功/失败状态和原因分析。
"""

class TestExecutor:
    """测试执行器"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        初始化测试执行器
        
        Args:
            api_key: DeepSeek API密钥
        """
        # 尝试从配置文件读取设置
        config = self._load_config()
        
        self.api_key = api_key or config.get("api_key") or ""
        self.model_type = config.get("model_type", "deepseek")
        self.base_url = config.get("base_url", "https://api.deepseek.com/v1")
        self.model = config.get("model", "deepseek-chat")
        self.temperature = config.get("temperature", 0.7)
        self.max_tokens = config.get("max_tokens")
        
        self.llm = ChatDeepSeek(
            base_url=self.base_url,
            model=self.model,
            api_key=self.api_key,
            temperature=self.temperature,
            max_tokens=self.max_tokens
        )
        
        # 创建带有测试输出格式的控制器
        self.test_controller = Controller(output_model=TestResult)
        
        # 设置日志
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def _load_config(self) -> dict:
        """从配置文件加载模型配置"""
        try:
            from .config_manager import ConfigManager
            config_manager = ConfigManager()
            config_path = config_manager.get_model_config_path()
            if config_path.exists():
                with open(config_path, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception as e:
            self.logger.warning(f"加载配置文件失败: {e}")
        return {}

    async def execute_test_case(self, test_case_id: int, headless: bool = False) -> Dict[str, Any]:
        """
        执行单个测试用例
        
        Args:
            test_case_id: 测试用例ID
            headless: 是否无头模式
            
        Returns:
            执行结果
        """
        db = SessionLocal()
        try:
            # 获取测试用例
            test_case = db.query(TestCase).filter(
                TestCase.id == test_case_id,
                TestCase.is_deleted == False
            ).first()
            
            if not test_case:
                return {
                    "success": False,
                    "error": f"测试用例 {test_case_id} 不存在"
                }
            
            # 创建执行记录
            execution = TestExecution(
                test_case_id=test_case_id,
                execution_name=f"{test_case.name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                status="running",
                started_at=datetime.utcnow()
            )
            db.add(execution)
            db.commit()
            db.refresh(execution)
            
            self.logger.info(f"开始执行测试用例: {test_case.name} (ID: {test_case_id})")
            
            # 执行测试
            result = await self._run_browser_test(
                test_case=test_case,
                execution=execution,
                headless=headless
            )
            
            # 更新执行记录
            execution.status = "passed" if result["success"] else "failed"
            execution.overall_status = result.get("overall_status", "FAILED")
            execution.total_duration = result.get("total_duration", 0)
            execution.summary = result.get("summary", "")
            execution.recommendations = result.get("recommendations", "")
            execution.error_message = result.get("error_message", "")
            execution.completed_at = datetime.utcnow()
            
            # 保存测试步骤
            if result.get("test_steps"):
                for i, step_data in enumerate(result["test_steps"]):
                    step = TestStep(
                        execution_id=execution.id,
                        step_name=step_data["step_name"],
                        step_order=i + 1,
                        status=step_data["status"],
                        description=step_data["description"],
                        error_message=step_data.get("error_message"),
                        screenshot_path=step_data.get("screenshot_path"),
                        duration_seconds=step_data.get("duration_seconds"),
                        completed_at=datetime.utcnow()
                    )
                    db.add(step)
            
            # 更新统计信息
            execution.total_steps = len(result.get("test_steps", []))
            execution.passed_steps = len([s for s in result.get("test_steps", []) if s["status"] == "PASSED"])
            execution.failed_steps = len([s for s in result.get("test_steps", []) if s["status"] == "FAILED"])
            execution.skipped_steps = len([s for s in result.get("test_steps", []) if s["status"] == "SKIPPED"])
            
            db.commit()
            
            return {
                "success": result["success"],
                "execution_id": execution.id,
                "test_case_name": test_case.name,
                "overall_status": execution.overall_status,
                "total_duration": execution.total_duration,
                "summary": execution.summary,
                "test_steps": result.get("test_steps", [])
            }
            
        except Exception as e:
            self.logger.error(f"执行测试用例失败: {e}")
            if 'execution' in locals():
                execution.status = "error"
                execution.error_message = str(e)
                execution.completed_at = datetime.utcnow()
                db.commit()
            
            return {
                "success": False,
                "error": str(e)
            }
        finally:
            db.close()
    
    async def execute_test_suite(self, test_case_ids: List[int], headless: bool = False) -> Dict[str, Any]:
        """
        批量执行测试用例
        
        Args:
            test_case_ids: 测试用例ID列表
            headless: 是否无头模式
            
        Returns:
            执行结果
        """
        results = []
        total_count = len(test_case_ids)
        passed_count = 0
        failed_count = 0
        
        for i, test_case_id in enumerate(test_case_ids, 1):
            self.logger.info(f"执行进度: {i}/{total_count} - 测试用例ID: {test_case_id}")
            
            result = await self.execute_test_case(test_case_id, headless)
            results.append(result)
            
            if result["success"]:
                passed_count += 1
            else:
                failed_count += 1
        
        return {
            "success": True,
            "total_count": total_count,
            "passed_count": passed_count,
            "failed_count": failed_count,
            "results": results
        }
    
    async def _run_browser_test(self, test_case: TestCase, execution: TestExecution, headless: bool) -> Dict[str, Any]:
        """
        运行浏览器测试
        
        Args:
            test_case: 测试用例
            execution: 执行记录
            headless: 是否无头模式
            
        Returns:
            测试结果
        """
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(
                headless=headless,
                args=[
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-gpu',
                    '--disable-web-security',
                    '--disable-features=VizDisplayCompositor'
                ]
            )
            context = await browser.new_context()
            page = await context.new_page()
            
            try:
                # 使用Browser Use Agent
                from browser_use import Agent
                
                agent = Agent(
                    task=test_case.task_content,
                    llm=self.llm,
                    page=page,
                    use_vision=True,
                    save_conversation_path=f'/tmp/test_execution_{execution.id}',
                    controller=self.test_controller,
                    extend_system_message=TEST_SYSTEM_PROMPT,
                )
                
                self.logger.info(f"开始执行任务: {test_case.task_content[:100]}...")
                
                start_time = datetime.utcnow()
                history = await agent.run()
                end_time = datetime.utcnow()
                
                total_duration = (end_time - start_time).total_seconds()
                
                # 解析测试结果
                if history.final_result():
                    try:
                        test_result = TestResult.model_validate_json(history.final_result())
                        
                        # 保存截图
                        screenshots = self._save_screenshots(history, execution.id)
                        
                        return {
                            "success": test_result.overall_status == "PASSED",
                            "overall_status": test_result.overall_status,
                            "total_duration": total_duration,
                            "summary": test_result.summary,
                            "recommendations": test_result.recommendations,
                            "test_steps": [step.dict() for step in test_result.test_steps],
                            "screenshots": screenshots,
                            "browser_logs": history.action_names()
                        }
                    except Exception as e:
                        self.logger.error(f"解析测试结果失败: {e}")
                        return {
                            "success": False,
                            "error_message": f"解析测试结果失败: {e}",
                            "total_duration": total_duration,
                            "summary": "测试执行完成但结果解析失败",
                            "test_steps": []
                        }
                else:
                    return {
                        "success": False,
                        "error_message": "没有获得测试结果",
                        "total_duration": total_duration,
                        "summary": "测试执行完成但没有返回结果",
                        "test_steps": []
                    }
                    
            finally:
                await browser.close()
    
    def _save_screenshots(self, history, execution_id: int) -> List[str]:
        """保存截图到指定目录"""
        screenshots = history.screenshots()
        if not screenshots:
            return []
        
        # 创建输出目录
        output_dir = Path(f"test_screenshots/execution_{execution_id}")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        saved_paths = []
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        for i, screenshot in enumerate(screenshots):
            if screenshot and isinstance(screenshot, str):
                try:
                    # 如果是base64编码的图片
                    if screenshot.startswith('data:image'):
                        # 提取base64数据
                        header, data = screenshot.split(',', 1)
                        image_data = base64.b64decode(data)
                        
                        # 确定文件扩展名
                        if 'png' in header:
                            ext = 'png'
                        elif 'jpeg' in header or 'jpg' in header:
                            ext = 'jpg'
                        else:
                            ext = 'png'
                        
                        filename = f"screenshot_{timestamp}_{i+1:03d}.{ext}"
                        filepath = output_dir / filename
                        
                        with open(filepath, 'wb') as f:
                            f.write(image_data)
                        
                        saved_paths.append(str(filepath))
                    
                    elif screenshot.startswith('/') or ':' in screenshot:
                        # 如果是文件路径，直接复制
                        source_path = Path(screenshot)
                        if source_path.exists():
                            filename = f"screenshot_{timestamp}_{i+1:03d}{source_path.suffix}"
                            dest_path = output_dir / filename
                            
                            import shutil
                            shutil.copy2(source_path, dest_path)
                            saved_paths.append(str(dest_path))
                
                except Exception as e:
                    self.logger.error(f"保存截图 {i+1} 失败: {e}")
                    continue
        
        return saved_paths

# 便捷函数
async def execute_single_test(test_case_id: int, headless: bool = False) -> Dict[str, Any]:
    """执行单个测试用例的便捷函数"""
    executor = TestExecutor()
    return await executor.execute_test_case(test_case_id, headless)

async def execute_multiple_tests(test_case_ids: List[int], headless: bool = False) -> Dict[str, Any]:
    """批量执行测试用例的便捷函数"""
    executor = TestExecutor()
    return await executor.execute_test_suite(test_case_ids, headless) 