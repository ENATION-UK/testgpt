# 批量执行并发控制功能

## 概述

为了支持大量测试用例的批量执行，同时避免系统资源过载，我们实现了并发控制功能。

## 功能特性

### 1. 并发限制
- **默认并发数**: 5个测试用例同时执行
- **控制机制**: 使用 `asyncio.Semaphore` 进行并发控制
- **资源管理**: 自动管理浏览器实例和系统资源

### 2. 执行流程
1. 创建批量执行任务记录
2. 为每个测试用例创建执行记录
3. 使用信号量控制并发执行
4. 实时更新执行状态和进度
5. 通过WebSocket推送实时更新

### 3. 日志监控
- 记录每个测试用例的开始和完成时间
- 显示当前并发执行数量
- 异常处理和错误记录

## 代码实现

### BatchTestExecutor 类

```python
class BatchTestExecutor:
    def __init__(self, api_key: Optional[str] = None, max_concurrent: int = 5):
        self.test_executor = TestExecutor(api_key)
        self.max_concurrent = max_concurrent  # 最大并发数
        self.logger = logging.getLogger(__name__)
```

### 并发控制实现

```python
# 使用信号量控制并发执行测试用例
semaphore = asyncio.Semaphore(self.max_concurrent)

async def execute_with_semaphore(batch_test_case):
    async with semaphore:
        self.logger.info(f"开始执行测试用例 {batch_test_case.test_case_id} (当前并发数: {self.max_concurrent - semaphore._value})")
        return await self._execute_single_test_in_batch(batch_test_case, headless, db)

# 创建所有任务
tasks = []
for batch_test_case in batch_test_cases:
    task = execute_with_semaphore(batch_test_case)
    tasks.append(task)

# 等待所有任务完成
await asyncio.gather(*tasks)
```

## 使用方式

### 1. 默认使用（5个并发）
```python
batch_executor = BatchTestExecutor()
result = await batch_executor.execute_batch_test(test_case_ids, headless)
```

### 2. 自定义并发数
```python
batch_executor = BatchTestExecutor(max_concurrent=10)  # 设置10个并发
result = await batch_executor.execute_batch_test(test_case_ids, headless)
```

## 性能优化建议

### 1. 并发数设置
- **低配置服务器**: 建议设置为3-5个并发
- **中等配置服务器**: 建议设置为5-10个并发
- **高配置服务器**: 建议设置为10-20个并发

### 2. 资源监控
- 监控内存使用情况
- 监控CPU使用率
- 监控网络带宽

### 3. 分批执行
对于大量测试用例（如1000+），建议：
1. 将用例分成多个批次
2. 每个批次设置合理的并发数
3. 批次间设置适当的时间间隔

## 未来扩展

### 1. 动态并发控制
- 根据系统资源动态调整并发数
- 支持运行时修改并发设置

### 2. 优先级队列
- 支持测试用例优先级设置
- 高优先级用例优先执行

### 3. 资源池管理
- 浏览器实例池化管理
- 更精细的资源控制

## 测试验证

运行测试脚本验证并发控制功能：

```bash
cd backend
uv run python tests/test_concurrent_execution.py
```

## 注意事项

1. **内存使用**: 每个浏览器实例大约占用50-100MB内存
2. **网络带宽**: 大量并发可能对目标网站造成压力
3. **稳定性**: 建议在测试环境中先验证并发设置
4. **监控**: 密切关注系统资源使用情况

## 相关文件

- `src/autotest/test_executor.py`: 批量执行器实现
- `src/autotest/services/execution_service.py`: 执行服务
- `tests/test_concurrent_execution.py`: 并发控制测试 