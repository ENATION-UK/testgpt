"""
Browser-Use 事件机制测试验证脚本
验证新的事件收集器和实时推送机制是否正常工作
"""

import asyncio
import logging
import sys
import os
from datetime import datetime
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "backend" / "src"))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_event_collection():
    """测试事件收集功能"""
    logger.info("开始测试Browser-Use事件收集功能")
    
    try:
        # 动态导入模块
        from testgpt.browser_event_collector import event_manager
        
        # 创建测试用例ID和执行ID
        test_case_id = 1
        execution_id = 1
        
        # 创建事件收集器
        event_collector = event_manager.create_collector(test_case_id, execution_id)
        
        # 验证收集器创建成功
        assert event_collector is not None, "事件收集器创建失败"
        logger.info("✓ 事件收集器创建成功")
        
        # 测试步骤事件收集
        class MockStepEvent:
            def __init__(self):
                self.step = 1
                self.url = "https://www.baidu.com"
                self.actions = [{"action_type": "goto", "url": "https://www.baidu.com"}]
                self.evaluation_previous_goal = "访问百度首页"
                self.memory = "正在执行测试任务"
                self.next_goal = "验证页面加载成功"
                self.screenshot_url = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="
        
        mock_event = MockStepEvent()
        await event_collector.collect_step_event(mock_event)
        
        # 验证步骤事件被正确收集
        assert len(event_collector.step_events) == 1, "步骤事件未被正确收集"
        assert event_collector.step_events[0].step_number == 1, "步骤编号不正确"
        assert event_collector.step_events[0].url == "https://www.baidu.com", "URL未正确收集"
        logger.info("✓ 步骤事件收集功能正常")
        
        # 测试任务完成事件收集
        class MockCompletionEvent:
            def __init__(self):
                self.id = "test_task_1"
                self.done_output = "任务执行成功"
                self.finished_at = datetime.now()
        
        mock_completion_event = MockCompletionEvent()
        await event_collector.collect_task_completion(mock_completion_event)
        
        # 验证任务完成事件被正确收集
        assert event_collector.task_completion is not None, "任务完成事件未被正确收集"
        assert event_collector.task_completion.success == True, "任务成功状态不正确"
        logger.info("✓ 任务完成事件收集功能正常")
        
        # 测试转换为测试结果
        test_result = event_collector.convert_to_test_result()
        
        # 验证测试结果转换
        assert "success" in test_result, "测试结果缺少success字段"
        logger.info("✓ 测试结果转换功能正常")
        
        # 测试获取步骤摘要
        summary = event_collector.get_step_summary()
        assert "total_steps" in summary, "步骤摘要缺少total_steps字段"
        assert summary["total_steps"] == 1, "总步骤数不正确"
        logger.info("✓ 步骤摘要功能正常")
        
        logger.info("所有事件收集功能测试通过！")
        return True
        
    except Exception as e:
        logger.error(f"测试过程中发生错误: {e}")
        import traceback
        logger.error(f"详细错误信息: {traceback.format_exc()}")
        return False

async def test_websocket_integration():
    """测试WebSocket集成"""
    logger.info("开始测试WebSocket集成")
    
    try:
        # 导入WebSocket管理器
        from testgpt.websocket_manager import websocket_manager
        
        # 验证WebSocket管理器存在
        assert websocket_manager is not None, "WebSocket管理器未正确初始化"
        logger.info("✓ WebSocket管理器初始化正常")
        
        # 测试订阅功能
        # 注意：这里不实际创建WebSocket连接，只是验证方法存在
        assert hasattr(websocket_manager, 'subscribe_to_execution'), "缺少subscribe_to_execution方法"
        assert hasattr(websocket_manager, 'broadcast_execution_update'), "缺少broadcast_execution_update方法"
        logger.info("✓ WebSocket订阅和广播方法存在")
        
        logger.info("WebSocket集成测试通过！")
        return True
        
    except Exception as e:
        logger.error(f"WebSocket集成测试过程中发生错误: {e}")
        import traceback
        logger.error(f"详细错误信息: {traceback.format_exc()}")
        return False

async def main():
    """主测试函数"""
    logger.info("开始Browser-Use事件机制集成测试")
    
    # 测试事件收集功能
    event_test_passed = await test_event_collection()
    
    # 测试WebSocket集成
    websocket_test_passed = await test_websocket_integration()
    
    # 汇总测试结果
    if event_test_passed and websocket_test_passed:
        logger.info("🎉 所有测试通过！Browser-Use事件机制集成成功！")
        return True
    else:
        logger.error("❌ 部分测试失败！")
        if not event_test_passed:
            logger.error("  - 事件收集功能测试失败")
        if not websocket_test_passed:
            logger.error("  - WebSocket集成测试失败")
        return False

if __name__ == "__main__":
    # 运行测试
    result = asyncio.run(main())
    sys.exit(0 if result else 1)