"""
任务上下文管理模块
"""
import asyncio
import logging
from typing import Dict, Any, List, Optional, Set

class TaskContext:
    """任务上下文管理类，用于维护正在运行的任务和浏览器对象"""
    
    def __init__(self):
        # 批量任务ID -> 批量任务执行器实例
        self._batch_executors: Dict[int, 'BatchTestExecutor'] = {}
        # 批量任务ID -> 该任务下的所有测试用例ID集合
        self._batch_test_cases: Dict[int, Set[int]] = {}
        # 测试用例ID -> 浏览器对象
        self._test_case_browsers: Dict[int, Any] = {}
        # 测试用例ID -> 对应的任务
        self._test_case_tasks: Dict[int, asyncio.Task] = {}
        # 测试用例ID -> 所属的批量任务ID
        self._test_case_batch_mapping: Dict[int, int] = {}
        # 锁，用于保护并发访问
        self._lock = asyncio.Lock()
    
    async def register_batch_executor(self, batch_execution_id: int, executor: 'BatchTestExecutor'):
        """注册批量任务执行器"""
        async with self._lock:
            self._batch_executors[batch_execution_id] = executor
            self._batch_test_cases[batch_execution_id] = set()
            logging.info(f"注册批量任务执行器: {batch_execution_id}")
            logging.info(f"当前批量任务执行器: {list(self._batch_executors.keys())}")
            logging.info(f"当前批量任务测试用例映射: {self._batch_test_cases}")
    
    async def unregister_batch_executor(self, batch_execution_id: int):
        """注销批量任务执行器"""
        logging.info(f"=== 开始注销批量任务执行器: {batch_execution_id} ===")
        try:
            async with self._lock:
                logging.info(f"步骤1: 获取锁成功，开始注销批量任务执行器: {batch_execution_id}")
                logging.info(f"注销前状态:")
                logging.info(f"  - 批量任务 {batch_execution_id} 在执行器中: {batch_execution_id in self._batch_executors}")
                logging.info(f"  - 批量任务 {batch_execution_id} 在测试用例映射中: {batch_execution_id in self._batch_test_cases}")
                
                logging.info(f"步骤2: 从执行器上下文中移除批量任务: {batch_execution_id}")
                if batch_execution_id in self._batch_executors:
                    del self._batch_executors[batch_execution_id]
                    logging.info(f"步骤2完成: 已从执行器上下文中移除批量任务: {batch_execution_id}")
                else:
                    logging.info(f"步骤2完成: 批量任务 {batch_execution_id} 不在执行器上下文中")
                
                logging.info(f"步骤3: 从测试用例映射中移除批量任务: {batch_execution_id}")
                if batch_execution_id in self._batch_test_cases:
                    del self._batch_test_cases[batch_execution_id]
                    logging.info(f"步骤3完成: 已从测试用例映射中移除批量任务: {batch_execution_id}")
                else:
                    logging.info(f"步骤3完成: 批量任务 {batch_execution_id} 不在测试用例映射中")
                
                logging.info(f"步骤4: 注销批量任务执行器: {batch_execution_id} 完成")
                logging.info(f"注销后状态:")
                logging.info(f"  - 剩余批量任务执行器: {list(self._batch_executors.keys())}")
                logging.info(f"  - 剩余批量任务测试用例映射: {self._batch_test_cases}")
        except Exception as e:
            logging.error(f"注销批量任务执行器 {batch_execution_id} 时出错: {e}")
            logging.error(f"错误详情: {type(e).__name__}: {str(e)}")
            import traceback
            logging.error(f"错误堆栈: {traceback.format_exc()}")
            raise
        finally:
            logging.info(f"=== 注销批量任务执行器: {batch_execution_id} 结束 ===")
    
    async def register_test_case(self, batch_execution_id: int, test_case_id: int, browser: Any, task: asyncio.Task):
        """注册测试用例的执行上下文"""
        async with self._lock:
            self._batch_test_cases[batch_execution_id].add(test_case_id)
            self._test_case_browsers[test_case_id] = browser
            self._test_case_tasks[test_case_id] = task
            self._test_case_batch_mapping[test_case_id] = batch_execution_id
            logging.info(f"注册测试用例: {test_case_id} -> 批量任务: {batch_execution_id}")
            logging.info(f"当前任务上下文状态:")
            logging.info(f"  - 批量任务 {batch_execution_id} 下的测试用例: {self._batch_test_cases[batch_execution_id]}")
            logging.info(f"  - 所有测试用例浏览器: {list(self._test_case_browsers.keys())}")
            logging.info(f"  - 所有测试用例任务: {list(self._test_case_tasks.keys())}")
            logging.info(f"  - 测试用例到批量任务的映射: {self._test_case_batch_mapping}")
    
    async def unregister_test_case(self, test_case_id: int):
        """注销测试用例的执行上下文"""
        logging.info(f"=== 开始注销测试用例: {test_case_id} ===")
        try:
            async with self._lock:
                logging.info(f"步骤1: 获取锁成功，开始注销测试用例: {test_case_id}")
                logging.info(f"注销前状态:")
                logging.info(f"  - 测试用例 {test_case_id} 在浏览器中: {test_case_id in self._test_case_browsers}")
                logging.info(f"  - 测试用例 {test_case_id} 在任务中: {test_case_id in self._test_case_tasks}")
                logging.info(f"  - 测试用例 {test_case_id} 在批量任务映射中: {test_case_id in self._test_case_batch_mapping}")
                
                logging.info(f"步骤2: 从浏览器上下文中移除测试用例: {test_case_id}")
                if test_case_id in self._test_case_browsers:
                    del self._test_case_browsers[test_case_id]
                    logging.info(f"步骤2完成: 已从浏览器上下文中移除测试用例: {test_case_id}")
                else:
                    logging.info(f"步骤2完成: 测试用例 {test_case_id} 不在浏览器上下文中")
                
                logging.info(f"步骤3: 从任务上下文中移除测试用例: {test_case_id}")
                if test_case_id in self._test_case_tasks:
                    del self._test_case_tasks[test_case_id]
                    logging.info(f"步骤3完成: 已从任务上下文中移除测试用例: {test_case_id}")
                else:
                    logging.info(f"步骤3完成: 测试用例 {test_case_id} 不在任务上下文中")
                
                # 从批量任务中移除
                logging.info(f"步骤4: 从批量任务中移除测试用例: {test_case_id}")
                batch_execution_id = self._test_case_batch_mapping.get(test_case_id)
                logging.info(f"步骤4a: 获取到批量任务ID: {batch_execution_id}")
                if batch_execution_id and batch_execution_id in self._batch_test_cases:
                    self._batch_test_cases[batch_execution_id].discard(test_case_id)
                    logging.info(f"步骤4b: 已从批量任务 {batch_execution_id} 中移除测试用例: {test_case_id}")
                else:
                    logging.info(f"步骤4b: 批量任务 {batch_execution_id} 不在映射中或不存在")
                
                logging.info(f"步骤5: 移除测试用例 {test_case_id} 的批量任务映射")
                if test_case_id in self._test_case_batch_mapping:
                    del self._test_case_batch_mapping[test_case_id]
                    logging.info(f"步骤5完成: 已移除测试用例 {test_case_id} 的批量任务映射")
                else:
                    logging.info(f"步骤5完成: 测试用例 {test_case_id} 不在批量任务映射中")
                
                logging.info(f"步骤6: 注销测试用例: {test_case_id} 完成")
        except Exception as e:
            logging.error(f"注销测试用例 {test_case_id} 时出错: {e}")
            logging.error(f"错误详情: {type(e).__name__}: {str(e)}")
            import traceback
            logging.error(f"错误堆栈: {traceback.format_exc()}")
            raise
        finally:
            logging.info(f"=== 注销测试用例: {test_case_id} 结束 ===")
    
    async def cancel_batch_execution(self, batch_execution_id: int) -> bool:
        """取消批量执行任务"""
        # 先获取锁，收集需要处理的数据
        test_case_ids = []
        cancelled_count = 0
        
        async with self._lock:
            if batch_execution_id not in self._batch_executors:
                logging.warning(f"批量任务 {batch_execution_id} 不存在")
                return False
            
            logging.info(f"开始取消批量任务: {batch_execution_id}")
            
            # 获取该批量任务下的所有测试用例
            test_case_ids = self._batch_test_cases.get(batch_execution_id, set()).copy()
            logging.info(f"批量任务 {batch_execution_id} 下共有 {len(test_case_ids)} 个测试用例: {test_case_ids}")
        
        # 释放锁后，先取消所有相关的测试用例任务和关闭浏览器，但不立即注销
        for test_case_id in test_case_ids:
            logging.info(f"正在取消测试用例 {test_case_id}...")
            if await self._cancel_test_case_without_unregister(test_case_id):
                cancelled_count += 1
                logging.info(f"测试用例 {test_case_id} 取消成功")
            else:
                logging.warning(f"测试用例 {test_case_id} 取消失败")
        
        # 现在统一注销所有测试用例（这些方法会自己获取锁）
        logging.info(f"开始统一注销所有测试用例...")
        for test_case_id in test_case_ids:
            await self.unregister_test_case(test_case_id)
        
        # 注销批量任务执行器（这个方法会自己获取锁）
        await self.unregister_batch_executor(batch_execution_id)
        
        logging.info(f"批量任务 {batch_execution_id} 已取消，共取消 {cancelled_count} 个测试用例")
        return True
    
    async def _cancel_test_case_without_unregister(self, test_case_id: int) -> bool:
        """取消单个测试用例（不包含注销，仅取消任务和关闭浏览器）"""
        try:
            logging.info(f"开始取消测试用例 {test_case_id}（不注销）...")
            logging.info(f"测试用例 {test_case_id} 的任务状态: {test_case_id in self._test_case_tasks}")
            logging.info(f"测试用例 {test_case_id} 的浏览器状态: {test_case_id in self._test_case_browsers}")
            
            # 取消任务
            if test_case_id in self._test_case_tasks:
                task = self._test_case_tasks[test_case_id]
                logging.info(f"测试用例 {test_case_id} 的任务状态: done={task.done()}, cancelled={task.cancelled()}")
                if not task.done():
                    task.cancel()
                    logging.info(f"已取消测试用例 {test_case_id} 的任务")
                else:
                    logging.info(f"测试用例 {test_case_id} 的任务已完成，无需取消")
            else:
                logging.warning(f"测试用例 {test_case_id} 的任务不在任务上下文中")
            
            # 关闭浏览器
            if test_case_id in self._test_case_browsers:
                browser = self._test_case_browsers[test_case_id]
                logging.info(f"正在关闭测试用例 {test_case_id} 的浏览器...")
                try:
                    await browser.close()
                    logging.info(f"已关闭测试用例 {test_case_id} 的浏览器")
                except Exception as e:
                    logging.warning(f"关闭测试用例 {test_case_id} 的浏览器时出错: {e}")
            else:
                logging.warning(f"测试用例 {test_case_id} 的浏览器不在任务上下文中")
            
            logging.info(f"测试用例 {test_case_id} 取消完成（未注销）")
            return True
            
        except Exception as e:
            logging.error(f"取消测试用例 {test_case_id} 时出错: {e}")
            return False
    
    def get_batch_executor(self, batch_execution_id: int) -> Optional['BatchTestExecutor']:
        """获取批量任务执行器"""
        return self._batch_executors.get(batch_execution_id)
    
    def is_batch_registered(self, batch_execution_id: int) -> bool:
        """检查批量任务是否已注册"""
        return batch_execution_id in self._batch_executors
    
    def get_test_case_count(self, batch_execution_id: int) -> int:
        """获取批量任务下的测试用例数量"""
        return len(self._batch_test_cases.get(batch_execution_id, set()))
    
    def get_all_batch_ids(self) -> List[int]:
        """获取所有已注册的批量任务ID"""
        return list(self._batch_executors.keys())

# 全局任务上下文管理器
task_context = TaskContext()
