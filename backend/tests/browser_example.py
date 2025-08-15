#!/usr/bin/env python3
"""
Browser Use 使用示例111
基于你提供的代码进行优化
"""

import asyncio
import os
import sys
import logging
from pathlib import Path

# 添加项目路径
sys.path.append(str(Path(__file__).parent / "src"))

from browser_use.llm.openai.chat import ChatOpenAI
from playwright.async_api import async_playwright
from dotenv import load_dotenv
from browser_use.llm import ChatDeepSeek
from browser_use import Agent

# 加载环境变量
load_dotenv()

async def main():
    """主函数"""
    # 初始化模型
    llm = ChatDeepSeek(
        base_url='https://api.deepseek.com/v1',
        model='deepseek-chat',
        api_key="",
    )
    
    async with async_playwright() as playwright:
        # 启动浏览器
        browser = await playwright.chromium.launch(
            headless=False,  # 显示浏览器窗口
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
        
        # 定义任务
        task = """
        打开百度，搜索Python教程，然后点击第一个搜索结果
        """
        
        # 创建Agent并执行任务
        agent = Agent(
            task=task,
            llm=llm,
            page=page,
            use_vision=False,  # 禁用视觉功能以提高性能
            save_conversation_path='/tmp/browser_example.log',
        )
        
        print("🚀 开始执行浏览器任务...")
        print(f"任务: {task}")
        
        try:
            result = await agent.run()
            print("✅ 任务执行完成！")
            print(f"结果: {result}")
        except Exception as e:
            print(f"❌ 任务执行失败: {e}")
        finally:
            await browser.close()
            print("🔒 浏览器已关闭")

if __name__ == '__main__':
    # 设置日志
    logging.basicConfig(level=logging.INFO)
    
    # 运行主函数
    asyncio.run(main()) 