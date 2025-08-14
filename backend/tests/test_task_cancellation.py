"""
测试任务取消机制
"""

import asyncio
import pytest
import time
from unittest.mock import Mock, AsyncMock, patch
from src.autotest.test_executor import task_context, BatchTestExecutor, TestExecutor


class TestTaskContext:
    """测试任务上下文管理类"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """每个测试前的设置"""
        # 清空任务上下文
        task_context._batch_executors.clear()
        task_context._batch_test_cases.clear()
        task_context._test_case_browsers.clear()
        task_context._test_case_tasks.clear()
        task_context._test_case_batch_mapping.clear()
    
    @pytest.mark.asyncio
    async def test_register_batch_executor(self):
        """测试注册批量任务执行器"""
        executor = Mock()
        batch_id = 1
        
        await task_context.register_batch_executor(batch_id, executor)
        
        assert task_context.is_batch_registered(batch_id)
        assert task_context.get_batch_executor(batch_id) == executor
        assert task_context.get_test_case_count(batch_id) == 0
    
    @pytest.mark.asyncio
    async def test_register_test_case(self):
        """测试注册测试用例"""
        executor = Mock()
        batch_id = 1
        test_case_id = 100
        browser = Mock()
        task = Mock()
        
        # 先注册批量执行器
        await task_context.register_batch_executor(batch_id, executor)
        
        # 注册测试用例
        await task_context.register_test_case(batch_id, test_case_id, browser, task)
        
        assert task_context.get_test_case_count(batch_id) == 1
        assert test_case_id in task_context._test_case_browsers
        assert test_case_id in task_context._test_case_tasks
        assert task_context._test_case_batch_mapping[test_case_id] == batch_id
    
    @pytest.mark.asyncio
    async def test_unregister_test_case(self):
        """测试注销测试用例"""
        executor = Mock()
        batch_id = 1
        test_case_id = 100
        browser = Mock()
        task = Mock()
        
        # 注册
        await task_context.register_batch_executor(batch_id, executor)
        await task_context.register_test_case(batch_id, test_case_id, browser, task)
        
        # 注销
        await task_context.unregister_test_case(test_case_id)
        
        assert task_context.get_test_case_count(batch_id) == 0
        assert test_case_id not in task_context._test_case_browsers
        assert test_case_id not in task_context._test_case_tasks
        assert test_case_id not in task_context._test_case_batch_mapping
    
    @pytest.mark.asyncio
    async def test_cancel_batch_execution(self):
        """测试取消批量执行任务"""
        executor = Mock()
        batch_id = 1
        test_case_id = 100
        browser = AsyncMock()
        task = Mock()
        task.done.return_value = False
        
        # 注册
        await task_context.register_batch_executor(batch_id, executor)
        await task_context.register_test_case(batch_id, test_case_id, browser, task)
        
        # 取消
        result = await task_context.cancel_batch_execution(batch_id)
        
        assert result is True
        assert not task_context.is_batch_registered(batch_id)
        assert test_case_id not in task_context._test_case_browsers
        
        # 验证任务被取消
        task.cancel.assert_called_once()
        # 验证浏览器被关闭
        browser.close.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_cancel_nonexistent_batch(self):
        """测试取消不存在的批量任务"""
        result = await task_context.cancel_batch_execution(999)
        assert result is False


class TestBatchTestExecutor:
    """测试批量测试执行器"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """每个测试前的设置"""
        # 清空任务上下文
        task_context._batch_executors.clear()
        task_context._batch_test_cases.clear()
        task_context._test_case_browsers.clear()
        task_context._test_case_tasks.clear()
        task_context._test_case_batch_mapping.clear()
    
    @pytest.mark.asyncio
    async def test_register_to_context(self):
        """测试注册到任务上下文"""
        executor = BatchTestExecutor()
        batch_id = 1
        
        await executor.register_to_context(batch_id)
        
        assert executor.batch_execution_id == batch_id
        assert task_context.is_batch_registered(batch_id)
        assert task_context.get_batch_executor(batch_id) == executor
    
    @pytest.mark.asyncio
    async def test_unregister_from_context(self):
        """测试从任务上下文注销"""
        executor = BatchTestExecutor()
        batch_id = 1
        
        await executor.register_to_context(batch_id)
        await executor.unregister_from_context()
        
        assert executor.batch_execution_id is None
        assert not task_context.is_batch_registered(batch_id)


class TestTaskCancellationIntegration:
    """测试任务取消集成功能"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """每个测试前的设置"""
        # 清空任务上下文
        task_context._batch_executors.clear()
        task_context._batch_test_cases.clear()
        task_context._test_case_browsers.clear()
        task_context._test_case_tasks.clear()
        task_context._test_case_batch_mapping.clear()
    
    @pytest.mark.asyncio
    async def test_batch_execution_cancellation_flow(self):
        """测试批量执行取消流程"""
        # 创建批量执行器
        executor = BatchTestExecutor(max_concurrent=2)
        batch_id = 1
        
        # 模拟长时间运行的任务
        async def long_running_task():
            await asyncio.sleep(10)  # 模拟长时间运行
            return "completed"
        
        # 创建模拟任务
        task1 = asyncio.create_task(long_running_task())
        task2 = asyncio.create_task(long_running_task())
        
        # 模拟浏览器对象
        browser1 = AsyncMock()
        browser2 = AsyncMock()
        
        # 注册到任务上下文
        await executor.register_to_context(batch_id)
        await task_context.register_test_case(batch_id, 101, browser1, task1)
        await task_context.register_test_case(batch_id, 102, browser2, task2)
        
        # 验证注册成功
        assert task_context.get_test_case_count(batch_id) == 2
        assert task_context.is_batch_registered(batch_id)
        
        # 在另一个任务中取消批量执行
        async def cancel_after_delay():
            await asyncio.sleep(0.1)  # 短暂延迟后取消
            await task_context.cancel_batch_execution(batch_id)
        
        # 启动取消任务
        cancel_task = asyncio.create_task(cancel_after_delay())
        
        # 等待取消完成
        await cancel_task
        
        # 验证取消结果
        assert not task_context.is_batch_registered(batch_id)
        assert task_context.get_test_case_count(batch_id) == 0
        
        # 验证任务被取消
        assert task1.cancelled() or task1.done()
        assert task2.cancelled() or task2.done()
        
        # 验证浏览器被关闭
        browser1.close.assert_called_once()
        browser2.close.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_partial_cancellation(self):
        """测试部分取消（某些测试用例已完成，某些还在运行）"""
        executor = BatchTestExecutor(max_concurrent=2)
        batch_id = 1
        
        # 模拟快速完成的任务
        async def quick_task():
            await asyncio.sleep(0.1)
            return "quick_completed"
        
        # 模拟长时间运行的任务
        async def long_task():
            await asyncio.sleep(10)
            return "long_completed"
        
        # 创建任务
        quick_task1 = asyncio.create_task(quick_task())
        quick_task2 = asyncio.create_task(quick_task())
        long_task1 = asyncio.create_task(long_task())
        
        # 模拟浏览器
        browser1 = AsyncMock()
        browser2 = AsyncMock()
        browser3 = AsyncMock()
        
        # 注册到任务上下文
        await executor.register_to_context(batch_id)
        await task_context.register_test_case(batch_id, 101, browser1, quick_task1)
        await task_context.register_test_case(batch_id, 102, browser2, quick_task2)
        await task_context.register_test_case(batch_id, 103, browser3, long_task1)
        
        # 等待快速任务完成
        await asyncio.sleep(0.2)
        
        # 验证快速任务已完成
        assert quick_task1.done()
        assert quick_task2.done()
        assert not long_task1.done()
        
        # 此时取消批量执行
        await task_context.cancel_batch_execution(batch_id)
        
        # 验证长时间任务被取消
        assert long_task1.cancelled()
        
        # 验证浏览器被关闭
        browser3.close.assert_called_once()
        
        # 验证批量任务已注销
        assert not task_context.is_batch_registered(batch_id)


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v"])
