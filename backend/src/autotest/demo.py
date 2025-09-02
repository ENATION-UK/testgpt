import asyncio
import base64
import os
import sys
import logging

from openai import BaseModel
from playwright.async_api import async_playwright

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

from pathlib import Path
from datetime import datetime

from browser_use.llm import ChatDeepSeek
from browser_use.browser.profile import BrowserProfile

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from browser_use.controller.service import Controller

load_dotenv()

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
# Initialize the model with standard OpenAI API

# 定义测试结果的结构化输出格式
class TestStep(BaseModel):
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
    test_steps: List[TestStep] = Field(description="详细的测试步骤")
    summary: str = Field(description="测试总结")
    recommendations: Optional[str] = Field(default=None, description="改进建议")

# 创建带有测试输出格式的控制器
test_controller = Controller(output_model=TestResult)

llm = ChatDeepSeek(
    base_url='https://api.deepseek.com/v1',
    model='deepseek-chat',
    api_key="",
    timeout=120.0  # 设置LLM客户端超时时间为120秒
)

def get_status_emoji(status: str) -> str:
    """根据状态返回对应的emoji"""
    status_map = {
        "PASSED": "✅",
        "FAILED": "❌",
        "SKIPPED": "⏭️",
        "PARTIAL": "⚠️"
    }
    return status_map.get(status.upper(), "❓")


def print_test_report(test_result: TestResult, history):
    """打印格式化的测试报告"""

    print("\n" + "="*80)
    print("📊 自动化测试报告")
    print("="*80)

    # 基本信息
    print(f"🧪 测试名称: {test_result.test_name}")
    print(f"📈 整体状态: {get_status_emoji(test_result.overall_status)} {test_result.overall_status}")
    print(f"⏱️  总执行时间: {test_result.total_duration:.2f}秒")
    print(f"📊 步骤统计: {test_result.passed_steps}通过 / {test_result.failed_steps}失败 / {test_result.skipped_steps}跳过")

    # 详细步骤
    print(f"\n📋 详细测试步骤:")
    print("-" * 80)

    for i, step in enumerate(test_result.test_steps, 1):
        status_emoji = get_status_emoji(step.status)
        print(f"{i:2d}. {status_emoji} {step.step_name}")
        print(f"    描述: {step.description}")
        if step.duration_seconds:
            print(f"    耗时: {step.duration_seconds:.2f}秒")
        if step.error_message:
            print(f"    ❌ 错误: {step.error_message}")
        if step.screenshot_path:
            print(f"    📸 截图: {step.screenshot_path}")

        print()

    # 测试总结
    print("📝 测试总结:")
    print("-" * 40)
    print(test_result.summary)

    # 改进建议
    if test_result.recommendations:
        print(f"\n💡 改进建议:")
        print("-" * 40)
        print(test_result.recommendations)

    # 额外信息
    print(f"\n🔍 额外信息:")
    print("-" * 40)
    print(f"🌐 访问的URL: {len(history.urls())} 个")
    print(f"⚡ 执行的动作: {len(history.action_names())} 个")
    print(f"📸 截图数量: {len(history.screenshots())} 个")
    screenshot_dir="/tmp/screenshots"
    # 保存并显示截图
    if history.screenshots():
        print(f"\n📸 截图信息:")
        print("-" * 40)

        # 保存截图到目录
        saved_screenshots = save_screenshots_to_directory(history, screenshot_dir)

        if saved_screenshots:
            print(f"✅ 截图已保存到目录: {screenshot_dir}/")
            print(f"📁 保存的截图文件:")
            for i, path in enumerate(saved_screenshots, 1):
                print(f"   {i}. {path}")
        else:
            print("⚠️  没有可保存的截图")

    if history.has_errors():
        print(f"🚨 执行错误: {len(history.errors())} 个")
        for error in history.errors():
            if error:
                print(f"   - {error}")

    print("\n" + "="*80)

async def main():
    async with async_playwright() as playwright:
        # Launch browser using Playwright directly
        browser = await playwright.chromium.launch(
            headless=False,
            args=[
                '--no-sandbox',
                '--disable-dev-shm-usage',
                '--disable-gpu',
                '--disable-web-security',
                '--disable-features=VizDisplayCompositor',
                '--disable-extensions'
            ]
        )
        context = await browser.new_context()
        page = await context.new_page()
        task = """

# 登录测试
打开
https://seller-bbc740.javamall.com.cn/

输入用户名superadmin
密码123456
验证码1111


# 验证条件
是否正常进入控制台

        """
        # 使用Browser Use Agent
        from browser_use import Agent
        
        # 创建 BrowserProfile 禁用默认扩展
        browser_profile = BrowserProfile(
            enable_default_extensions=False,
            headless=False
        )
        
        # Pass the page directly to Agent
        agent = Agent(
            task=task,
            llm=llm,
            page=page,  # Pass page directly as shortcut
            use_vision=True,  # Enable vision capabilities for screenshot analysis
            save_conversation_path='/tmp/javashop4',
            controller=test_controller,
            extend_system_message=TEST_SYSTEM_PROMPT,
            browser_profile=browser_profile,
            llm_timeout=120,    # LLM调用超时时间（秒）
            step_timeout=300    # 每个步骤的超时时间（秒）
        )

        print("🚀 使用Browser Use Agent执行任务...")
        print(f"📋 任务: {task}")

        history = await agent.run()
                
        await browser.close()

        # 解析测试结果
        if history.final_result():
            try:
                test_result = TestResult.model_validate_json(history.final_result())
                print_test_report(test_result, history)

                print("📋 原始结果:")
                print(history.final_result())
            except Exception as e:
                print(f"❌ 解析测试结果失败: {e}")
                print("📋 原始结果:")
                print(history.final_result())
        else:
            print("❌ 没有获得测试结果")


def save_screenshots_to_directory(history, output_dir: str = "test_screenshots") -> List[str]:
    """保存截图到指定目录并返回路径列表"""
    screenshots = history.screenshots()
    print(f'截图数据-----{screenshots}')
    if not screenshots:
        return []

    # 创建输出目录
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)

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
                    filepath = output_path / filename

                    with open(filepath, 'wb') as f:
                        f.write(image_data)

                    saved_paths.append(str(filepath))

                elif screenshot.startswith('/') or ':' in screenshot:
                    # 如果是文件路径，直接复制
                    source_path = Path(screenshot)
                    if source_path.exists():
                        filename = f"screenshot_{timestamp}_{i+1:03d}{source_path.suffix}"
                        dest_path = output_path / filename

                        import shutil
                        shutil.copy2(source_path, dest_path)
                        saved_paths.append(str(dest_path))

            except Exception as e:
                print(f"⚠️  保存截图 {i+1} 失败: {e}")
                continue

    return saved_paths



if __name__ == '__main__':
    asyncio.run(main()) 