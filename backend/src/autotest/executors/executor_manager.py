"""
执行器管理器模块
"""
import asyncio
import logging
from typing import Optional

from ..core.task_context import task_context
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .batch_executor import BatchTestExecutor

class BatchExecutorManager:
    """批量执行器管理器"""
    
    def __init__(self):
        self._lock = asyncio.Lock()
    
    async def create_executor(self, batch_execution_id: int, max_concurrent: int = 5) -> 'BatchTestExecutor':
        """创建并注册一个批量执行器"""
        async with self._lock:
            from .batch_executor import BatchTestExecutor
            executor = BatchTestExecutor(max_concurrent=max_concurrent)
            return executor
    
    async def get_executor(self, batch_execution_id: int) -> Optional['BatchTestExecutor']:
        """获取指定的批量执行器"""
        return task_context.get_batch_executor(batch_execution_id)
    
    async def cancel_executor(self, batch_execution_id: int) -> bool:
        """取消指定的批量执行器"""
        return await task_context.cancel_batch_execution(batch_execution_id)
    
    async def remove_executor(self, batch_execution_id: int):
        """移除指定的批量执行器"""
        await task_context.unregister_batch_executor(batch_execution_id)
    
    def is_batch_cancelled(self, batch_execution_id: int) -> bool:
        """检查批量执行任务是否被取消"""
        return not task_context.is_batch_registered(batch_execution_id)

# 全局实例
batch_executor_manager = BatchExecutorManager()
