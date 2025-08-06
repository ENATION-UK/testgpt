"""
测试执行服务
负责执行测试用例并记录结果
"""

import asyncio
import base64
import json
import logging
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

# 设置时区为北京时间
BEIJING_TZ = timezone(timedelta(hours=8))

def beijing_now():
    """获取北京时间"""
    return datetime.now(BEIJING_TZ)

from browser_use.controller.service import Controller
from .services.multi_llm_service import MultiLLMService
from playwright.async_api import async_playwright

from .database import TestCase, TestExecution, TestStep, SessionLocal, BatchExecution, BatchExecutionTestCase
from .websocket_manager import websocket_manager

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
            api_key: DeepSeek API密钥（已废弃，现在使用多模型服务）
        """
        # 初始化多模型服务
        self.multi_llm_service = MultiLLMService()
        
        # 初始化测试控制器
        self.test_controller = Controller(output_model=TestResult)
        
        # 设置日志
        self.logger = logging.getLogger(__name__)
        
        # 批量执行器引用（用于检查取消状态）
        self.batch_executor = None
    
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

    async def execute_test_case(self, test_case_id: int, headless: bool = False, batch_execution_id: Optional[int] = None) -> Dict[str, Any]:
        """
        执行单个测试用例
        
        Args:
            test_case_id: 测试用例ID
            headless: 是否无头模式
            batch_execution_id: 批量执行任务ID（可选）
            
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
                    "error_message": "测试用例不存在",
                    "execution_id": None
                }
            
            # 创建执行记录
            execution = TestExecution(
                test_case_id=test_case_id,
                execution_name=f"{test_case.name}_{beijing_now().strftime('%Y%m%d_%H%M%S')}",
                status="running",
                started_at=beijing_now()
            )
            db.add(execution)
            db.commit()
            db.refresh(execution)
            
            # 执行浏览器测试
            result = await self._run_browser_test(test_case, execution, headless, batch_execution_id)
            
            # 更新执行记录
            execution.status = "passed" if result["success"] else "failed"
            execution.overall_status = result.get("overall_status", "FAILED")
            execution.total_duration = result.get("total_duration", 0)
            execution.summary = result.get("summary", "")
            execution.recommendations = result.get("recommendations", "")
            execution.error_message = result.get("error_message", "")
            execution.completed_at = beijing_now()
            
            # 更新统计信息
            execution.total_steps = len(result.get("test_steps", []))
            execution.passed_steps = len([s for s in result.get("test_steps", []) if s["status"] == "PASSED"])
            execution.failed_steps = len([s for s in result.get("test_steps", []) if s["status"] == "FAILED"])
            execution.skipped_steps = len([s for s in result.get("test_steps", []) if s["status"] == "SKIPPED"])
            
            # 保存浏览器日志和截图
            execution.browser_logs = result.get("browser_logs", [])
            execution.screenshots = result.get("screenshots", [])
            
            db.commit()
            
            # 保存测试步骤
            for i, step_data in enumerate(result.get("test_steps", [])):
                step = TestStep(
                    execution_id=execution.id,
                    step_name=step_data["step_name"],
                    step_order=i + 1,
                    status=step_data["status"],
                    description=step_data["description"],
                    error_message=step_data.get("error_message"),
                    screenshot_path=step_data.get("screenshot_path"),
                    duration_seconds=step_data.get("duration_seconds"),
                    started_at=beijing_now(),
                    completed_at=beijing_now()
                )
                db.add(step)
            
            db.commit()
            
            return {
                "success": result["success"],
                "execution_id": execution.id,
                "overall_status": result.get("overall_status", "FAILED"),
                "total_duration": result.get("total_duration", 0),
                "summary": result.get("summary", ""),
                "recommendations": result.get("recommendations", ""),
                "error_message": result.get("error_message", ""),
                "test_steps": result.get("test_steps", [])
            }
            
        except Exception as e:
            self.logger.error(f"执行测试用例 {test_case_id} 失败: {e}")
            return {
                "success": False,
                "error_message": str(e),
                "execution_id": None
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
    
    async def _run_browser_test(self, test_case: TestCase, execution: TestExecution, headless: bool, batch_execution_id: Optional[int] = None) -> Dict[str, Any]:
        """运行浏览器测试"""
        from playwright.async_api import async_playwright
        import asyncio
        
        async with async_playwright() as p:
            # 启动浏览器
            browser = await p.chromium.launch(
                headless=headless,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-accelerated-2d-canvas',
                    '--no-first-run',
                    '--no-zygote',
                    '--disable-gpu',
                    '--disable-features=VizDisplayCompositor'
                ]
            )
            
            try:
                # 创建新页面
                page = await browser.new_page()
                
                # 加载自定义提示词
                custom_prompt = self._load_custom_prompt()
                
                # 合并默认提示词和自定义提示词
                final_prompt = TEST_SYSTEM_PROMPT
                if custom_prompt:
                    final_prompt = f"{TEST_SYSTEM_PROMPT}\n\n{custom_prompt}"
                
                # 使用Browser Use Agent
                from browser_use import Agent
                
                # 使用多模型服务创建LLM实例
                config = self.multi_llm_service._load_multi_model_config()
                request_config = self.multi_llm_service._get_next_available_config(config)
                print(f"使用API key:{request_config.model_type}-- {request_config.api_key}")
                if not request_config:
                    raise Exception("没有可用的API key配置")
                
                llm = self.multi_llm_service._create_llm_instance(request_config)
                
                agent = Agent(
                    task=test_case.task_content,
                    llm=llm,
                    page=page,
                    use_vision=True,
                    save_conversation_path=f'/tmp/test_execution_{execution.id}',
                    controller=self.test_controller,
                    extend_system_message=final_prompt,
                )
                
                self.logger.info(f"开始执行任务: {test_case.task_content[:100]}...")
                
                start_time = beijing_now()
                
                # 检查是否被取消（在开始执行前）
                if batch_execution_id and self.batch_executor and hasattr(self.batch_executor, 'is_batch_cancelled'):
                    if self.batch_executor.is_batch_cancelled(batch_execution_id):
                        self.logger.info(f"批量执行任务 {batch_execution_id} 已被取消，停止测试用例 {test_case.id}")
                        return {
                            "success": False,
                            "error_message": "测试被取消",
                            "total_duration": 0,
                            "summary": "测试被取消",
                            "test_steps": []
                        }
                
                # 创建一个任务来定期检查取消状态
                async def check_cancellation():
                    while True:
                        await asyncio.sleep(1)  # 每秒检查一次
                        if batch_execution_id and self.batch_executor and hasattr(self.batch_executor, 'is_batch_cancelled'):
                            if self.batch_executor.is_batch_cancelled(batch_execution_id):
                                self.logger.info(f"检测到批量执行任务 {batch_execution_id} 被取消，准备停止测试用例 {test_case.id}")
                                # 关闭浏览器
                                try:
                                    await browser.close()
                                except Exception as e:
                                    self.logger.warning(f"关闭浏览器时出错: {e}")
                                return True
                    return False
                
                # 执行测试，同时运行取消检查任务
                try:
                    # 创建取消检查任务
                    cancellation_task = asyncio.create_task(check_cancellation())
                    
                    # 执行agent.run()，但设置超时以便能够响应取消
                    agent_task = asyncio.create_task(agent.run())
                    
                    # 等待任一任务完成
                    done, pending = await asyncio.wait(
                        [agent_task, cancellation_task],
                        return_when=asyncio.FIRST_COMPLETED
                    )
                    
                    # 取消未完成的任务
                    for task in pending:
                        task.cancel()
                        try:
                            await task
                        except asyncio.CancelledError:
                            pass
                    
                    # 检查是否是因为取消而结束
                    if cancellation_task in done:
                        self.logger.info(f"批量执行任务 {batch_execution_id} 已被取消，停止测试用例 {test_case.id}")
                        return {
                            "success": False,
                            "error_message": "测试被取消",
                            "total_duration": (beijing_now() - start_time).total_seconds(),
                            "summary": "测试被取消",
                            "test_steps": []
                        }
                    
                    # 如果agent任务完成，获取结果
                    if agent_task in done:
                        try:
                            history = agent_task.result()
                        except Exception as e:
                            self.logger.error(f"Agent执行失败: {e}")
                            return {
                                "success": False,
                                "error_message": f"Agent执行失败: {e}",
                                "total_duration": (beijing_now() - start_time).total_seconds(),
                                "summary": "Agent执行失败",
                                "test_steps": []
                            }
                    else:
                        # 这种情况不应该发生，但为了安全起见
                        return {
                            "success": False,
                            "error_message": "任务执行异常",
                            "total_duration": (beijing_now() - start_time).total_seconds(),
                            "summary": "任务执行异常",
                            "test_steps": []
                        }
                        
                except Exception as e:
                    self.logger.error(f"执行测试用例 {test_case.id} 时发生异常: {e}")
                    return {
                        "success": False,
                        "error_message": f"执行异常: {e}",
                        "total_duration": (beijing_now() - start_time).total_seconds(),
                        "summary": "执行异常",
                        "test_steps": []
                    }
                
                end_time = beijing_now()
                total_duration = (end_time - start_time).total_seconds()
                
                # 检查是否被取消（在执行完成后）
                if batch_execution_id and self.batch_executor and hasattr(self.batch_executor, 'is_batch_cancelled'):
                    if self.batch_executor.is_batch_cancelled(batch_execution_id):
                        self.logger.info(f"批量执行任务 {batch_execution_id} 已被取消，停止测试用例 {test_case.id}")
                        return {
                            "success": False,
                            "error_message": "测试被取消",
                            "total_duration": total_duration,
                            "summary": "测试被取消",
                            "test_steps": []
                        }
                
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
                # 确保浏览器被关闭
                try:
                    await browser.close()
                except Exception as e:
                    self.logger.warning(f"关闭浏览器时出错: {e}")
    
    def _load_custom_prompt(self) -> str:
        """加载自定义提示词"""
        try:
            from .config_manager import ConfigManager
            config_manager = ConfigManager()
            config_path = config_manager.get_prompt_config_path()
            
            if config_path.exists():
                with open(config_path, "r", encoding="utf-8") as f:
                    config = json.load(f)
                    return config.get("custom_prompt", "")
            return ""
        except Exception as e:
            self.logger.warning(f"加载自定义提示词失败: {e}")
            return ""

    def _save_screenshots(self, history, execution_id: int) -> List[str]:
        """保存截图到指定目录"""
        screenshots = history.screenshots()
        if not screenshots:
            return []
        
        # 创建输出目录
        output_dir = Path(f"test_screenshots/execution_{execution_id}")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        saved_paths = []
        timestamp = beijing_now().strftime("%Y%m%d_%H%M%S")
        
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

class BatchTestExecutor:
    """批量测试执行器"""
    
    def __init__(self, api_key: Optional[str] = None, max_concurrent: int = 5):
        """
        初始化批量测试执行器
        
        Args:
            api_key: DeepSeek API密钥
            max_concurrent: 最大并发执行数量，默认为5
        """
        self.test_executor = TestExecutor(api_key)
        self.max_concurrent = max_concurrent
        self.logger = logging.getLogger(__name__)
        self._cancelled_batch_ids = set()  # 存储被取消的批量任务ID
        
        # 将BatchTestExecutor实例传递给TestExecutor，以便在浏览器测试中检查取消状态
        self.test_executor.batch_executor = self
    
    def cancel_batch_execution(self, batch_execution_id: int):
        """取消批量执行任务"""
        self._cancelled_batch_ids.add(batch_execution_id)
        self.logger.info(f"批量执行任务 {batch_execution_id} 已被标记为取消")
    
    def is_batch_cancelled(self, batch_execution_id: int) -> bool:
        """检查批量执行任务是否被取消"""
        return batch_execution_id in self._cancelled_batch_ids
    
    async def execute_batch_test(self, test_case_ids: List[int], headless: bool = False, batch_name: str = "批量执行任务", batch_execution_id: Optional[int] = None) -> Dict[str, Any]:
        """
        执行批量测试用例
        
        Args:
            test_case_ids: 测试用例ID列表
            headless: 是否无头模式
            batch_name: 批量执行任务名称
            batch_execution_id: 可选的批量执行任务ID，如果提供则使用现有的任务
            
        Returns:
            执行结果
        """
        db = SessionLocal()
        try:
            if batch_execution_id is not None:
                # 使用现有的批量执行任务
                batch_execution = db.query(BatchExecution).filter(BatchExecution.id == batch_execution_id).first()
                if not batch_execution:
                    raise ValueError(f"批量执行任务 {batch_execution_id} 不存在")
                
                # 检查是否已经有测试用例记录
                existing_test_cases = db.query(BatchExecutionTestCase).filter(
                    BatchExecutionTestCase.batch_execution_id == batch_execution_id
                ).all()
                
                if not existing_test_cases:
                    # 创建批量执行任务中的测试用例记录
                    batch_test_cases = []
                    for test_case_id in test_case_ids:
                        batch_test_case = BatchExecutionTestCase(
                            batch_execution_id=batch_execution.id,
                            test_case_id=test_case_id,
                            status="pending"
                        )
                        db.add(batch_test_case)
                        batch_test_cases.append(batch_test_case)
                    db.commit()
                else:
                    batch_test_cases = existing_test_cases
            else:
                # 创建新的批量执行任务记录
                batch_execution = BatchExecution(
                    name=batch_name,
                    status="running",
                    total_count=len(test_case_ids),
                    pending_count=len(test_case_ids),
                    started_at=beijing_now()
                )
                db.add(batch_execution)
                db.commit()
                db.refresh(batch_execution)
                
                # 创建批量执行任务中的测试用例记录
                batch_test_cases = []
                for test_case_id in test_case_ids:
                    batch_test_case = BatchExecutionTestCase(
                        batch_execution_id=batch_execution.id,
                        test_case_id=test_case_id,
                        status="pending"
                    )
                    db.add(batch_test_case)
                    batch_test_cases.append(batch_test_case)
                db.commit()
            
            self.logger.info(f"开始批量执行任务: {batch_execution.name} (ID: {batch_execution.id})，最大并发数: {self.max_concurrent}")
            
            # 使用信号量控制并发执行测试用例
            semaphore = asyncio.Semaphore(self.max_concurrent)
            
            async def execute_with_semaphore(batch_test_case):
                async with semaphore:
                    # 检查任务是否被取消
                    if batch_executor_manager.is_batch_cancelled(batch_execution.id):
                        self.logger.info(f"批量执行任务 {batch_execution.id} 已被取消，跳过测试用例 {batch_test_case.test_case_id}")
                        return
                    
                    self.logger.info(f"开始执行测试用例 {batch_test_case.test_case_id} (当前并发数: {self.max_concurrent - semaphore._value})")
                    try:
                        result = await self._execute_single_test_in_batch(batch_test_case, headless, db)
                        self.logger.info(f"完成执行测试用例 {batch_test_case.test_case_id}")
                        return result
                    except Exception as e:
                        self.logger.error(f"执行测试用例 {batch_test_case.test_case_id} 时发生异常: {e}")
                        raise
            
            # 创建所有任务
            tasks = []
            self.logger.info(f"开始创建任务，测试用例数量: {len(batch_test_cases)}")
            for batch_test_case in batch_test_cases:
                # 只为pending状态的用例创建任务
                if batch_test_case.status != "pending":
                    continue
                # 在创建任务前检查是否被取消
                if batch_executor_manager.is_batch_cancelled(batch_execution.id):
                    self.logger.info(f"批量执行任务 {batch_execution.id} 已被取消，停止创建新任务")
                    break
                
                self.logger.info(f"创建任务 for 测试用例 {batch_test_case.test_case_id}")
                task = asyncio.create_task(execute_with_semaphore(batch_test_case))
                tasks.append(task)
            
            self.logger.info(f"创建了 {len(tasks)} 个任务")
            
            # 等待所有任务完成，但定期检查是否被取消
            if tasks:
                try:
                    # 使用asyncio.wait来更快地响应取消信号
                    done, pending = await asyncio.wait(
                        tasks,
                        return_when=asyncio.ALL_COMPLETED
                    )
                    
                    # 检查是否被取消
                    if batch_executor_manager.is_batch_cancelled(batch_execution.id):
                        # 取消所有未完成的任务
                        for task in pending:
                            task.cancel()
                        
                        # 等待所有任务完成（包括被取消的）
                        if pending:
                            await asyncio.wait(pending)
                        
                        self.logger.info(f"批量执行任务 {batch_execution.id} 已被取消")
                        # 更新任务状态为已取消
                        batch_execution.status = "cancelled"
                        batch_execution.completed_at = beijing_now()
                        batch_execution.updated_at = beijing_now()
                        db.commit()
                        
                        # 推送 WebSocket 更新
                        await websocket_manager.broadcast_batch_update(
                            batch_execution.id,
                            {
                                "status": batch_execution.status,
                                "success_count": batch_execution.success_count,
                                "failed_count": batch_execution.failed_count,
                                "running_count": batch_execution.running_count,
                                "pending_count": batch_execution.pending_count,
                                "total_count": batch_execution.total_count,
                                "completed_at": batch_execution.completed_at.isoformat() if batch_execution.completed_at else None,
                                "updated_at": batch_execution.updated_at.isoformat() if batch_execution.updated_at else None
                            }
                        )
                        
                        return {
                            "success": False,
                            "batch_execution_id": batch_execution.id,
                            "batch_name": batch_execution.name,
                            "status": "cancelled",
                            "message": "批量执行任务已被取消"
                        }
                        
                except Exception as e:
                    self.logger.error(f"批量执行任务 {batch_execution.id} 执行过程中发生异常: {e}")
            
            # 检查任务是否被取消
            if batch_executor_manager.is_batch_cancelled(batch_execution.id):
                self.logger.info(f"批量执行任务 {batch_execution.id} 已被取消")
                # 更新任务状态为已取消
                batch_execution.status = "cancelled"
                batch_execution.completed_at = beijing_now()
                batch_execution.updated_at = beijing_now()
                db.commit()
                
                # 推送 WebSocket 更新
                await websocket_manager.broadcast_batch_update(
                    batch_execution.id,
                    {
                        "status": batch_execution.status,
                        "success_count": batch_execution.success_count,
                        "failed_count": batch_execution.failed_count,
                        "running_count": batch_execution.running_count,
                        "pending_count": batch_execution.pending_count,
                        "total_count": batch_execution.total_count,
                        "completed_at": batch_execution.completed_at.isoformat() if batch_execution.completed_at else None,
                        "updated_at": batch_execution.updated_at.isoformat() if batch_execution.updated_at else None
                    }
                )
                
                return {
                    "success": False,
                    "batch_execution_id": batch_execution.id,
                    "batch_name": batch_execution.name,
                    "status": "cancelled",
                    "message": "批量执行任务已被取消"
                }
            
            # 更新批量执行任务状态为完成
            batch_execution.status = "completed"
            batch_execution.completed_at = beijing_now()
            batch_execution.updated_at = beijing_now()
            
            # 统计执行结果
            success_count = db.query(BatchExecutionTestCase).filter(
                BatchExecutionTestCase.batch_execution_id == batch_execution.id,
                BatchExecutionTestCase.status == "completed"
            ).count()
            
            failed_count = db.query(BatchExecutionTestCase).filter(
                BatchExecutionTestCase.batch_execution_id == batch_execution.id,
                BatchExecutionTestCase.status == "failed"
            ).count()
            
            batch_execution.success_count = success_count
            batch_execution.failed_count = failed_count
            batch_execution.running_count = 0
            batch_execution.pending_count = 0
            
            db.commit()
            
            # 推送批量执行任务完成通知
            await websocket_manager.broadcast_batch_update(
                batch_execution.id,
                {
                    "status": batch_execution.status,
                    "success_count": batch_execution.success_count,
                    "failed_count": batch_execution.failed_count,
                    "running_count": batch_execution.running_count,
                    "pending_count": batch_execution.pending_count,
                    "total_count": batch_execution.total_count,
                    "completed_at": batch_execution.completed_at.isoformat() if batch_execution.completed_at else None,
                    "updated_at": batch_execution.updated_at.isoformat() if batch_execution.updated_at else None
                }
            )
            
            return {
                "success": True,
                "batch_execution_id": batch_execution.id,
                "batch_name": batch_execution.name,
                "total_count": batch_execution.total_count,
                "success_count": batch_execution.success_count,
                "failed_count": batch_execution.failed_count,
                "status": batch_execution.status,
                "started_at": batch_execution.started_at.isoformat(),
                "completed_at": batch_execution.completed_at.isoformat() if batch_execution.completed_at else None
            }
            
        except Exception as e:
            self.logger.error(f"批量执行任务失败: {e}")
            # 如果使用了现有的批量执行任务，更新其状态为失败
            if batch_execution_id is not None:
                batch_execution = db.query(BatchExecution).filter(BatchExecution.id == batch_execution_id).first()
                if batch_execution:
                    batch_execution.status = "failed"
                    batch_execution.completed_at = beijing_now()
                    batch_execution.updated_at = beijing_now()
            raise
        finally:
            db.close()
    
    async def _execute_single_test_in_batch(self, batch_test_case: BatchExecutionTestCase, headless: bool, db):
        """
        在批量执行中执行单个测试用例
        
        Args:
            batch_test_case: 批量执行任务中的测试用例记录
            headless: 是否无头模式
            db: 数据库会话
        """
        try:
            # 检查任务是否被取消
            if batch_executor_manager.is_batch_cancelled(batch_test_case.batch_execution_id):
                self.logger.info(f"批量执行任务 {batch_test_case.batch_execution_id} 已被取消，跳过测试用例 {batch_test_case.test_case_id}")
                batch_test_case.status = "cancelled"
                batch_test_case.completed_at = beijing_now()
                batch_test_case.updated_at = beijing_now()
                db.commit()
                return
            
            # 更新状态为运行中
            batch_test_case.status = "running"
            batch_test_case.started_at = beijing_now()
            batch_test_case.updated_at = beijing_now()
            db.commit()
            
            # 再次检查任务是否被取消（在开始执行前）
            if batch_executor_manager.is_batch_cancelled(batch_test_case.batch_execution_id):
                self.logger.info(f"批量执行任务 {batch_test_case.batch_execution_id} 已被取消，停止测试用例 {batch_test_case.test_case_id}")
                batch_test_case.status = "cancelled"
                batch_test_case.completed_at = beijing_now()
                batch_test_case.updated_at = beijing_now()
                db.commit()
                return
            
            # 执行测试用例
            result = await self.test_executor.execute_test_case(batch_test_case.test_case_id, headless, batch_test_case.batch_execution_id)
            
            # 检查任务是否被取消（在执行完成后）
            if batch_executor_manager.is_batch_cancelled(batch_test_case.batch_execution_id):
                self.logger.info(f"批量执行任务 {batch_test_case.batch_execution_id} 已被取消，标记测试用例 {batch_test_case.test_case_id} 为取消")
                batch_test_case.status = "cancelled"
                batch_test_case.completed_at = beijing_now()
                batch_test_case.updated_at = beijing_now()
                db.commit()
                return
            
            # 更新执行记录ID
            if "execution_id" in result:
                batch_test_case.execution_id = result["execution_id"]
            
            # 更新状态
            if result["success"]:
                batch_test_case.status = "completed"
            else:
                batch_test_case.status = "failed"
            
            batch_test_case.completed_at = beijing_now()
            batch_test_case.updated_at = beijing_now()
            db.commit()
            
            # 更新批量执行任务的统计数据
            batch_execution = db.query(BatchExecution).filter(
                BatchExecution.id == batch_test_case.batch_execution_id
            ).first()
            
            if batch_execution:
                # 重新计算统计数据
                completed_count = db.query(BatchExecutionTestCase).filter(
                    BatchExecutionTestCase.batch_execution_id == batch_execution.id,
                    BatchExecutionTestCase.status.in_(["completed", "failed"])
                ).count()
                
                running_count = db.query(BatchExecutionTestCase).filter(
                    BatchExecutionTestCase.batch_execution_id == batch_execution.id,
                    BatchExecutionTestCase.status == "running"
                ).count()
                
                pending_count = db.query(BatchExecutionTestCase).filter(
                    BatchExecutionTestCase.batch_execution_id == batch_execution.id,
                    BatchExecutionTestCase.status == "pending"
                ).count()
                
                # 更新批量执行任务状态
                batch_execution.success_count = completed_count - db.query(BatchExecutionTestCase).filter(
                    BatchExecutionTestCase.batch_execution_id == batch_execution.id,
                    BatchExecutionTestCase.status == "failed"
                ).count()
                
                batch_execution.failed_count = db.query(BatchExecutionTestCase).filter(
                    BatchExecutionTestCase.batch_execution_id == batch_execution.id,
                    BatchExecutionTestCase.status == "failed"
                ).count()
                
                batch_execution.running_count = running_count
                batch_execution.pending_count = pending_count
                batch_execution.updated_at = beijing_now()
                db.commit()
                
                # 推送 WebSocket 更新
                await websocket_manager.broadcast_batch_update(
                    batch_execution.id,
                    {
                        "status": batch_execution.status,
                        "success_count": batch_execution.success_count,
                        "failed_count": batch_execution.failed_count,
                        "running_count": batch_execution.running_count,
                        "pending_count": batch_execution.pending_count,
                        "total_count": batch_execution.total_count,
                        "updated_at": batch_execution.updated_at.isoformat() if batch_execution.updated_at else None
                    }
                )
                
        except Exception as e:
            self.logger.error(f"执行测试用例 {batch_test_case.test_case_id} 失败: {e}")
            batch_test_case.status = "failed"
            batch_test_case.completed_at = beijing_now()
            batch_test_case.updated_at = beijing_now()
            db.commit()
    
    def get_batch_execution_status(self, batch_execution_id: int) -> Dict[str, Any]:
        """
        获取批量执行任务的状态
        
        Args:
            batch_execution_id: 批量执行任务ID
            
        Returns:
            批量执行任务状态
        """
        db = SessionLocal()
        try:
            # 获取批量执行任务
            batch_execution = db.query(BatchExecution).filter(
                BatchExecution.id == batch_execution_id
            ).first()
            
            if not batch_execution:
                return {
                    "success": False,
                    "error": f"批量执行任务 {batch_execution_id} 不存在"
                }
            
            # 获取批量执行任务中的测试用例
            batch_test_cases = db.query(BatchExecutionTestCase).filter(
                BatchExecutionTestCase.batch_execution_id == batch_execution_id
            ).all()
            
            test_case_details = []
            for btc in batch_test_cases:
                # 获取测试用例信息
                test_case = db.query(TestCase).filter(
                    TestCase.id == btc.test_case_id
                ).first()
                
                # 获取执行记录信息
                execution = None
                if btc.execution_id:
                    execution = db.query(TestExecution).filter(
                        TestExecution.id == btc.execution_id
                    ).first()
                
                test_case_details.append({
                    "id": btc.id,
                    "test_case_id": btc.test_case_id,
                    "test_case_name": test_case.name if test_case else "未知",
                    "execution_id": btc.execution_id,
                    "status": btc.status,
                    "overall_status": execution.overall_status if execution else None,
                    "started_at": btc.started_at.isoformat() if btc.started_at else None,
                    "completed_at": btc.completed_at.isoformat() if btc.completed_at else None,
                    "error_message": execution.error_message if execution else None
                })
            
            return {
                "success": True,
                "batch_execution": {
                    "id": batch_execution.id,
                    "name": batch_execution.name,
                    "status": batch_execution.status,
                    "total_count": batch_execution.total_count,
                    "success_count": batch_execution.success_count,
                    "failed_count": batch_execution.failed_count,
                    "running_count": batch_execution.running_count,
                    "pending_count": batch_execution.pending_count,
                    "total_duration": batch_execution.total_duration,
                    "started_at": batch_execution.started_at.isoformat() if batch_execution.started_at else None,
                    "completed_at": batch_execution.completed_at.isoformat() if batch_execution.completed_at else None,
                    "created_at": batch_execution.created_at.isoformat() if batch_execution.created_at else None,
                    "updated_at": batch_execution.updated_at.isoformat() if batch_execution.updated_at else None,
                    "test_cases": test_case_details
                }
            }
        finally:
            db.close()

# 便捷函数
async def execute_single_test(test_case_id: int, headless: bool = False) -> Dict[str, Any]:
    """执行单个测试用例的便捷函数"""
    executor = TestExecutor()
    return await executor.execute_test_case(test_case_id, headless)

async def execute_multiple_tests(test_case_ids: List[int], headless: bool = False) -> Dict[str, Any]:
    """批量执行测试用例的便捷函数"""
    executor = TestExecutor()
    return await executor.execute_test_suite(test_case_ids, headless)

async def execute_batch_tests(test_case_ids: List[int], headless: bool = False, batch_name: str = "批量执行任务") -> Dict[str, Any]:
    """批量执行测试用例的便捷函数"""
    batch_executor = BatchTestExecutor(max_concurrent=5)
    return await batch_executor.execute_batch_test(test_case_ids, headless, batch_name)

# 全局的BatchTestExecutor实例管理器
class BatchExecutorManager:
    """批量执行器管理器"""
    
    def __init__(self):
        self._executors = {}  # 存储正在运行的执行器实例
        self._lock = asyncio.Lock()
    
    async def create_executor(self, batch_execution_id: int, max_concurrent: int = 5) -> BatchTestExecutor:
        """创建并注册一个批量执行器"""
        async with self._lock:
            executor = BatchTestExecutor(max_concurrent=max_concurrent)
            self._executors[batch_execution_id] = executor
            return executor
    
    async def get_executor(self, batch_execution_id: int) -> Optional[BatchTestExecutor]:
        """获取指定的批量执行器"""
        async with self._lock:
            return self._executors.get(batch_execution_id)
    
    async def cancel_executor(self, batch_execution_id: int) -> bool:
        """取消指定的批量执行器"""
        async with self._lock:
            executor = self._executors.get(batch_execution_id)
            if executor:
                executor.cancel_batch_execution(batch_execution_id)
                return True
            return False
    
    async def remove_executor(self, batch_execution_id: int):
        """移除指定的批量执行器"""
        async with self._lock:
            if batch_execution_id in self._executors:
                del self._executors[batch_execution_id]
    
    def is_batch_cancelled(self, batch_execution_id: int) -> bool:
        """检查批量执行任务是否被取消"""
        executor = self._executors.get(batch_execution_id)
        if executor:
            return executor.is_batch_cancelled(batch_execution_id)
        return False

# 全局实例
batch_executor_manager = BatchExecutorManager()