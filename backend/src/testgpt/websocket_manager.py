"""
WebSocket 管理器，用于实时推送批量执行任务进度
"""

import json
import asyncio
from typing import Dict, Set, Any
from fastapi import WebSocket, WebSocketDisconnect
from datetime import datetime, timezone, timedelta

# 设置时区为北京时间
BEIJING_TZ = timezone(timedelta(hours=8))

def beijing_now():
    """获取北京时间"""
    return datetime.now(BEIJING_TZ)


class WebSocketManager:
    """WebSocket 连接管理器"""
    
    def __init__(self):
        # 存储所有活跃的 WebSocket 连接
        self.active_connections: Set[WebSocket] = set()
        # 存储订阅特定批量执行任务的连接
        self.batch_subscriptions: Dict[int, Set[WebSocket]] = {}
        # 存储订阅特定测试执行的连接
        self.execution_subscriptions: Dict[int, Set[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket):
        """接受新的 WebSocket 连接"""
        await websocket.accept()
        self.active_connections.add(websocket)
        print(f"WebSocket 连接已建立，当前连接数: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        """断开 WebSocket 连接"""
        self.active_connections.discard(websocket)
        # 从所有订阅中移除该连接
        for batch_id in list(self.batch_subscriptions.keys()):
            self.batch_subscriptions[batch_id].discard(websocket)
            # 如果订阅列表为空，删除该批量执行任务的订阅
            if not self.batch_subscriptions[batch_id]:
                del self.batch_subscriptions[batch_id]
        
        # 从执行订阅中移除该连接
        for execution_id in list(self.execution_subscriptions.keys()):
            self.execution_subscriptions[execution_id].discard(websocket)
            # 如果订阅列表为空，删除该测试执行的订阅
            if not self.execution_subscriptions[execution_id]:
                del self.execution_subscriptions[execution_id]
                
        print(f"WebSocket 连接已断开，当前连接数: {len(self.active_connections)}")
    
    async def subscribe_to_batch(self, websocket: WebSocket, batch_execution_id: int):
        """订阅特定批量执行任务的进度更新"""
        if batch_execution_id not in self.batch_subscriptions:
            self.batch_subscriptions[batch_execution_id] = set()
        self.batch_subscriptions[batch_execution_id].add(websocket)
        print(f"订阅批量执行任务 {batch_execution_id}，当前订阅数: {len(self.batch_subscriptions[batch_execution_id])}")
    
    def unsubscribe_from_batch(self, websocket: WebSocket, batch_execution_id: int):
        """取消订阅特定批量执行任务"""
        if batch_execution_id in self.batch_subscriptions:
            self.batch_subscriptions[batch_execution_id].discard(websocket)
            if not self.batch_subscriptions[batch_execution_id]:
                del self.batch_subscriptions[batch_execution_id]
    
    async def subscribe_to_execution(self, websocket: WebSocket, execution_id: int):
        """订阅特定测试执行的进度更新"""
        if execution_id not in self.execution_subscriptions:
            self.execution_subscriptions[execution_id] = set()
        self.execution_subscriptions[execution_id].add(websocket)
        print(f"订阅测试执行 {execution_id}，当前订阅数: {len(self.execution_subscriptions[execution_id])}")
    
    def unsubscribe_from_execution(self, websocket: WebSocket, execution_id: int):
        """取消订阅特定测试执行"""
        if execution_id in self.execution_subscriptions:
            self.execution_subscriptions[execution_id].discard(websocket)
            if not self.execution_subscriptions[execution_id]:
                del self.execution_subscriptions[execution_id]
    
    async def send_personal_message(self, message: str, websocket: WebSocket):
        """发送个人消息"""
        try:
            await websocket.send_text(message)
        except WebSocketDisconnect:
            self.disconnect(websocket)
        except Exception as e:
            print(f"发送个人消息失败: {e}")
            self.disconnect(websocket)
    
    async def broadcast(self, message: str):
        """广播消息给所有连接"""
        disconnected = set()
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except WebSocketDisconnect:
                disconnected.add(connection)
            except Exception as e:
                print(f"广播消息失败: {e}")
                disconnected.add(connection)
        
        # 清理断开的连接
        for connection in disconnected:
            self.disconnect(connection)
    
    async def broadcast_batch_update(self, batch_execution_id: int, data: Dict[str, Any]):
        """广播批量执行任务更新给订阅者"""
        if batch_execution_id not in self.batch_subscriptions:
            return
        
        message = json.dumps({
            "type": "batch_execution_update",
            "batch_execution_id": batch_execution_id,
            "data": data,
            "timestamp": beijing_now().isoformat()
        })
        
        disconnected = set()
        for connection in self.batch_subscriptions[batch_execution_id]:
            try:
                await connection.send_text(message)
            except WebSocketDisconnect:
                disconnected.add(connection)
            except Exception as e:
                print(f"发送批量执行任务更新失败: {e}")
                disconnected.add(connection)
        
        # 清理断开的连接
        for connection in disconnected:
            self.disconnect(connection)
    
    async def broadcast_execution_update(self, execution_id: int, data: Dict[str, Any]):
        """广播测试执行更新给订阅者"""
        if execution_id not in self.execution_subscriptions:
            # 如果没有特定执行订阅，尝试广播到所有连接
            await self.broadcast(json.dumps({
                "type": "execution_update",
                "execution_id": execution_id,
                "data": data,
                "timestamp": beijing_now().isoformat()
            }))
            return
        
        message = json.dumps({
            "type": "execution_update",
            "execution_id": execution_id,
            "data": data,
            "timestamp": beijing_now().isoformat()
        })
        
        disconnected = set()
        for connection in self.execution_subscriptions[execution_id]:
            try:
                await connection.send_text(message)
            except WebSocketDisconnect:
                disconnected.add(connection)
            except Exception as e:
                print(f"发送测试执行更新失败: {e}")
                disconnected.add(connection)
        
        # 清理断开的连接
        for connection in disconnected:
            self.disconnect(connection)
    
    async def broadcast_batch_list_update(self, data: Dict[str, Any]):
        """广播批量执行任务列表更新"""
        message = json.dumps({
            "type": "batch_execution_list_update",
            "data": data,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        await self.broadcast(message)


# 全局 WebSocket 管理器实例
websocket_manager = WebSocketManager()