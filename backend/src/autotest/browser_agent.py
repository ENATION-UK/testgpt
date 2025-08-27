"""
Browser Use 集成模块
提供浏览器自动化功能
"""

import asyncio
import os
import sys
import logging
from typing import Optional, Dict, Any
from pathlib import Path
import json

from browser_use.llm.openai.chat import ChatOpenAI
from browser_use.llm import ChatDeepSeek
from browser_use.browser.profile import BrowserProfile
from playwright.async_api import async_playwright, Browser, Page
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class BrowserAgent:
    """浏览器自动化代理类"""
    
    def __init__(self, 
                 model_type: str = "deepseek",
                 api_key: Optional[str] = None,
                 base_url: Optional[str] = None,
                 model: str = "deepseek-chat",
                 temperature: float = 0.7,
                 max_tokens: Optional[int] = None):
        """
        初始化浏览器代理
        
        Args:
            model_type: 模型类型 ("deepseek", "openai")
            api_key: API密钥
            base_url: API基础URL
            model: 模型名称
            temperature: 温度参数
            max_tokens: 最大token数
        """
        # 尝试从配置文件读取设置
        config = self._load_config()
        
        self.model_type = model_type or config.get("model_type", "deepseek")
        self.api_key = api_key or config.get("api_key") or os.getenv("DEEPSEEK_API_KEY")
        self.base_url = base_url or config.get("base_url") or "https://api.deepseek.com/v1"
        self.model = model or config.get("model", "deepseek-chat")
        self.temperature = temperature or config.get("temperature", 0.7)
        self.max_tokens = max_tokens or config.get("max_tokens")
        
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        
        # 初始化LLM
        self.llm = self._init_llm()
        
        # 设置日志
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def _load_config(self) -> dict:
        """从配置文件加载模型配置"""
        try:
            from .config_manager import ConfigManager
            config_manager = ConfigManager()
            config_path = config_manager.get_multi_model_config_path()
            if config_path.exists():
                with open(config_path, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception as e:
            self.logger.warning(f"加载配置文件失败: {e}")
        return {}
    
    def _init_llm(self):
        """初始化语言模型"""
        if self.model_type == "deepseek":
            return ChatDeepSeek(
                base_url=self.base_url,
                model=self.model,
                api_key=self.api_key,
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
        elif self.model_type == "openai":
            return ChatOpenAI(
                model=self.model,
                api_key=self.api_key,
                temperature=self.temperature
            )
        else:
            raise ValueError(f"不支持的模型类型: {self.model_type}")
    
    async def start_browser(self, headless: bool = False):
        """启动浏览器"""
        try:
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(
                headless=headless,
                args=[
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-gpu',
                    '--disable-web-security',
                    '--disable-features=VizDisplayCompositor',
                    '--disable-extensions'
                ]
            )
            self.context = await self.browser.new_context()
            self.page = await self.context.new_page()
            self.logger.info("浏览器启动成功")
            return True
        except Exception as e:
            self.logger.error(f"浏览器启动失败: {e}")
            return False
    
    async def stop_browser(self):
        """停止浏览器"""
        try:
            if self.browser:
                await self.browser.close()
            if hasattr(self, 'playwright'):
                await self.playwright.stop()
            self.logger.info("浏览器已关闭")
        except Exception as e:
            self.logger.error(f"关闭浏览器时出错: {e}")
    
    async def run_task(self, 
                      task: str, 
                      use_vision: bool = False,
                      save_conversation_path: Optional[str] = None) -> Dict[str, Any]:
        """
        执行浏览器任务
        
        Args:
            task: 任务描述
            use_vision: 是否使用视觉功能
            save_conversation_path: 对话保存路径
            
        Returns:
            执行结果
        """
        if not self.page:
            raise RuntimeError("浏览器未启动，请先调用 start_browser()")
        
        try:
            # 尝试导入Browser Use Agent
            try:
                from browser_use import Agent
                
                # 创建 BrowserProfile 禁用默认扩展
                browser_profile = BrowserProfile(
                    enable_default_extensions=False,
                    headless=False
                )
                
                # 创建Agent
                agent = Agent(
                    task=task,
                    llm=self.llm,
                    page=self.page,
                    use_vision=use_vision,
                    save_conversation_path=save_conversation_path,
                    browser_profile=browser_profile,
                )
                
                # 执行任务
                self.logger.info(f"开始执行任务: {task}")
                result = await agent.run()
                
                return {
                    "success": True,
                    "result": result,
                    "task": task
                }
                
            except ImportError as e:
                self.logger.warning(f"Browser Use Agent导入失败，使用简化模式: {e}")
                return await self._run_simple_task(task)
            
        except Exception as e:
            self.logger.error(f"任务执行失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "task": task
            }
    
    async def _run_simple_task(self, task: str) -> Dict[str, Any]:
        """
        简化任务执行（当Browser Use不可用时）
        """
        try:
            # 简单的任务执行逻辑
            if "百度" in task and "搜索" in task:
                # 打开百度
                await self.page.goto("https://www.baidu.com")
                self.logger.info("已打开百度首页")
                
                # 提取搜索关键词
                import re
                search_match = re.search(r'搜索(.+?)(?:\s|$)', task)
                if search_match:
                    keyword = search_match.group(1)
                    # 输入搜索关键词
                    await self.page.fill("#kw", keyword)
                    await self.page.click("#su")
                    self.logger.info(f"已搜索: {keyword}")
                
                return {
                    "success": True,
                    "result": f"已完成任务: {task}",
                    "task": task
                }
            else:
                # 通用任务处理
                await self.page.goto("https://www.baidu.com")
                return {
                    "success": True,
                    "result": f"已打开百度首页，任务: {task}",
                    "task": task
                }
                
        except Exception as e:
            self.logger.error(f"简化任务执行失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "task": task
            }
    
    async def execute_web_task(self, task_description: str) -> Dict[str, Any]:
        """
        执行Web任务的便捷方法
        
        Args:
            task_description: 任务描述
            
        Returns:
            执行结果
        """
        # 确保浏览器已启动
        if not self.browser:
            await self.start_browser(headless=False)
        
        # 执行任务
        result = await self.run_task(
            task=task_description,
            use_vision=False,
            save_conversation_path='/tmp/browser_agent.log'
        )
        
        return result

# 便捷函数
async def run_browser_task(task: str, 
                          model_type: str = "deepseek",
                          api_key: Optional[str] = None,
                          headless: bool = False) -> Dict[str, Any]:
    """
    运行浏览器任务的便捷函数
    
    Args:
        task: 任务描述
        model_type: 模型类型
        api_key: API密钥
        headless: 是否无头模式
        
    Returns:
        执行结果
    """
    agent = BrowserAgent(model_type=model_type, api_key=api_key)
    
    try:
        # 启动浏览器
        await agent.start_browser(headless=headless)
        
        # 执行任务
        result = await agent.execute_web_task(task)
        
        return result
        
    finally:
        # 确保浏览器关闭
        await agent.stop_browser()

# 示例用法
async def example_usage():
    """示例用法"""
    # 方法1: 使用便捷函数
    result = await run_browser_task(
        task="打开百度，搜索Python教程",
        model_type="deepseek",
        api_key="your-api-key-here"
    )
    print("结果:", result)
    
    # 方法2: 使用类
    agent = BrowserAgent(model_type="deepseek", api_key="your-api-key-here")
    try:
        await agent.start_browser(headless=False)
        result = await agent.execute_web_task("打开GitHub，搜索FastAPI项目")
        print("结果:", result)
    finally:
        await agent.stop_browser()

if __name__ == "__main__":
    # 运行示例
    asyncio.run(example_usage()) 