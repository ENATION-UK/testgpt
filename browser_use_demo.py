#!/usr/bin/env python3
"""
Browser Use Demo - 展示如何调用和判断测试结果
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

async def test_login_scenario():
    """测试登录场景"""
    print("🚀 开始测试登录场景...")
    
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
        
        # 定义测试任务
        test_task = """
        登录测试，打开
        @https://admin-bbc740.javamall.com.cn/dashboard

        输入用户名superadmin
        密码111111
        验证码1111
        点击登录，检测是否能正常登录
        """
        
        print(f"📋 测试任务: {test_task}")
        
        # 创建Agent并执行任务
        agent = Agent(
            task=test_task,
            llm=llm,
            page=page,
            use_vision=False,
            save_conversation_path='/tmp/login_test.log',
        )
        
        try:
            print("🔄 开始执行测试...")
            result = await agent.run()
            
            print("=" * 50)
            print("📊 测试结果分析:")
            print("=" * 50)
            
            # 打印原始返回值
            print(f"🔍 原始返回值类型: {type(result)}")
            print(f"🔍 原始返回值: {result}")
            
            # 分析结果
            if result:
                print("✅ 测试执行完成")
                
                # 检查是否包含成功关键词
                success_keywords = ["成功", "登录成功", "dashboard", "管理", "欢迎"]
                failure_keywords = ["失败", "错误", "无法", "不能", "异常"]
                
                result_str = str(result).lower()
                
                has_success = any(keyword in result_str for keyword in success_keywords)
                has_failure = any(keyword in result_str for keyword in failure_keywords)
                
                if has_success and not has_failure:
                    print("🎉 测试结果: 通过")
                    print("📝 判断依据: 包含成功关键词")
                elif has_failure:
                    print("❌ 测试结果: 失败")
                    print("📝 判断依据: 包含失败关键词")
                else:
                    print("⚠️  测试结果: 不确定")
                    print("📝 需要进一步分析")
                
                # 提取关键信息
                print("\n📋 关键信息提取:")
                if "dashboard" in result_str:
                    print("  - 检测到dashboard页面")
                if "superadmin" in result_str:
                    print("  - 检测到用户名输入")
                if "111111" in result_str:
                    print("  - 检测到密码输入")
                    
            else:
                print("❌ 测试执行失败: 无返回值")
                
        except Exception as e:
            print(f"❌ 测试执行异常: {e}")
            
        finally:
            await browser.close()
            print("🔒 浏览器已关闭")

async def test_simple_scenario():
    """测试简单场景"""
    print("\n🚀 开始测试简单场景...")
    
    llm = ChatDeepSeek(
        base_url='https://api.deepseek.com/v1',
        model='deepseek-chat',
        api_key="",
    )
    
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        
        # 简单任务
        simple_task = "打开百度，搜索Python，然后点击第一个搜索结果"
        
        print(f"📋 简单任务: {simple_task}")
        
        agent = Agent(
            task=simple_task,
            llm=llm,
            page=page,
            use_vision=False,
            save_conversation_path='/tmp/simple_test.log',
        )
        
        try:
            result = await agent.run()
            
            print("=" * 30)
            print("📊 简单测试结果:")
            print(f"返回值: {result}")
            
            # 简单判断逻辑
            if result and len(str(result)) > 10:
                print("✅ 测试可能成功")
            else:
                print("❌ 测试可能失败")
                
        except Exception as e:
            print(f"❌ 简单测试异常: {e}")
            
        finally:
            await browser.close()

def main():
    """主函数"""
    print("🎯 Browser Use Demo - 测试结果分析")
    print("=" * 60)
    
    # 设置日志
    logging.basicConfig(level=logging.INFO)
    
    # 运行测试
    asyncio.run(test_login_scenario())
    asyncio.run(test_simple_scenario())
    
    print("\n💡 总结:")
    print("1. Browser Use返回的是字符串结果")
    print("2. 可以通过关键词匹配判断成功/失败")
    print("3. 需要根据具体业务场景定义判断规则")
    print("4. 建议结合页面截图和日志进行综合判断")

if __name__ == "__main__":
    main() 