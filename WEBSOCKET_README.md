# WebSocket 实时进度推送功能

## 概述

本项目已实现基于 WebSocket 的实时进度推送功能，替代了之前的轮询机制，提供更高效、更实时的批量执行任务进度更新。

## 功能特性

### ✅ 实时进度推送
- 批量执行任务状态变更时自动推送
- 支持多个客户端同时订阅
- 自动重连机制

### ✅ 智能订阅管理
- 自动订阅运行中的任务
- 任务完成后自动取消订阅
- 页面切换时自动管理订阅

### ✅ 连接状态监控
- 实时显示连接状态
- 自动重连机制
- 心跳检测

## 技术实现

### 后端实现

#### 1. WebSocket 管理器 (`websocket_manager.py`)
```python
class WebSocketManager:
    - 管理所有 WebSocket 连接
    - 处理批量执行任务订阅
    - 推送实时更新消息
```

#### 2. WebSocket 路由 (`routers/websocket.py`)
```python
@router.websocket("/ws")
- 处理 WebSocket 连接
- 支持订阅/取消订阅
- 心跳检测
```

#### 3. 执行服务集成
- 在批量执行任务状态变更时推送更新
- 支持任务开始、进度更新、完成等事件

### 前端实现

#### 1. WebSocket 服务 (`services/websocket.ts`)
```typescript
class WebSocketService:
    - 自动连接和重连
    - 消息处理器管理
    - 订阅管理
```

#### 2. 批量执行页面集成
- 自动订阅运行中的任务
- 实时更新进度条和状态
- 智能取消订阅

## 消息格式

### 订阅消息
```json
{
  "type": "subscribe_batch",
  "batch_execution_id": 123
}
```

### 取消订阅消息
```json
{
  "type": "unsubscribe_batch",
  "batch_execution_id": 123
}
```

### 心跳消息
```json
{
  "type": "ping"
}
```

### 批量执行任务更新
```json
{
  "type": "batch_execution_update",
  "batch_execution_id": 123,
  "data": {
    "status": "running",
    "success_count": 5,
    "failed_count": 1,
    "running_count": 2,
    "pending_count": 0,
    "total_count": 8,
    "updated_at": "2024-01-01T12:00:00Z"
  },
  "timestamp": "2024-01-01T12:00:00Z"
}
```

## 使用方法

### 1. 启动服务
```bash
# 后端
cd backend
uv run python run.py

# 前端
cd frontend
npm run dev
```

### 2. 创建批量执行任务
1. 进入测试用例管理页面
2. 选择要执行的测试用例
3. 点击"批量执行"
4. 系统会自动创建批量执行任务并开始执行

### 3. 查看实时进度
1. 进入批量执行任务页面
2. 页面会自动订阅运行中的任务
3. 进度条和状态会实时更新
4. 任务完成后自动停止订阅

### 4. 测试 WebSocket 连接
```bash
cd backend
python test_websocket.py
```

## 优势对比

### 轮询 vs WebSocket

| 特性 | 轮询 | WebSocket |
|------|------|-----------|
| 实时性 | 延迟高（10秒间隔） | 实时推送 |
| 服务器负载 | 高（频繁请求） | 低（按需推送） |
| 网络流量 | 高（重复请求） | 低（增量更新） |
| 用户体验 | 一般 | 优秀 |
| 资源消耗 | 高 | 低 |

## 配置说明

### 后端配置
- WebSocket 端点：`ws://localhost:8000/ws`
- 心跳间隔：30秒
- 最大重连次数：5次

### 前端配置
- 自动重连：启用
- 重连延迟：1秒递增
- 心跳检测：30秒间隔

## 故障排除

### 常见问题

1. **WebSocket 连接失败**
   - 检查后端服务是否启动
   - 检查端口 8000 是否被占用
   - 检查防火墙设置

2. **消息推送延迟**
   - 检查网络连接
   - 检查服务器负载
   - 查看浏览器控制台错误

3. **订阅不生效**
   - 检查批量执行任务 ID 是否正确
   - 检查 WebSocket 连接状态
   - 查看后端日志

### 调试方法

1. **浏览器开发者工具**
   - 查看 Network 标签页的 WebSocket 连接
   - 查看 Console 标签页的消息日志

2. **后端日志**
   - 查看 WebSocket 连接日志
   - 查看消息推送日志

3. **测试脚本**
   ```bash
   python test_websocket.py
   ```

## 扩展功能

### 未来计划
- [ ] 支持更多类型的实时推送（单个测试执行、系统状态等）
- [ ] 添加消息历史记录
- [ ] 支持消息过滤和分组
- [ ] 添加消息优先级
- [ ] 支持离线消息队列

## 总结

WebSocket 实时推送功能大大提升了用户体验，减少了服务器负载，是一个重要的架构改进。通过智能的订阅管理和自动重连机制，确保了系统的稳定性和可靠性。 