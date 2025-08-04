#!/usr/bin/env python3
"""
WebSocket 测试脚本
"""

import asyncio
import websockets
import json
from datetime import datetime

async def test_websocket():
    """测试 WebSocket 连接和消息"""
    uri = "ws://localhost:8000/ws"
    
    try:
        async with websockets.connect(uri) as websocket:
            print("✅ WebSocket 连接成功")
            
            # 测试订阅批量执行任务
            subscribe_message = {
                "type": "subscribe_batch",
                "batch_execution_id": 1
            }
            await websocket.send(json.dumps(subscribe_message))
            print("📤 发送订阅消息:", subscribe_message)
            
            # 等待确认消息
            response = await websocket.recv()
            response_data = json.loads(response)
            print("📥 收到响应:", response_data)
            
            # 测试心跳
            ping_message = {"type": "ping"}
            await websocket.send(json.dumps(ping_message))
            print("📤 发送心跳消息:", ping_message)
            
            response = await websocket.recv()
            response_data = json.loads(response)
            print("📥 收到心跳响应:", response_data)
            
            # 等待一段时间看是否有其他消息
            print("⏳ 等待 5 秒...")
            try:
                await asyncio.wait_for(websocket.recv(), timeout=5.0)
            except asyncio.TimeoutError:
                print("⏰ 5 秒内没有收到其他消息")
            
            # 测试取消订阅
            unsubscribe_message = {
                "type": "unsubscribe_batch",
                "batch_execution_id": 1
            }
            await websocket.send(json.dumps(unsubscribe_message))
            print("📤 发送取消订阅消息:", unsubscribe_message)
            
            response = await websocket.recv()
            response_data = json.loads(response)
            print("📥 收到取消订阅响应:", response_data)
            
    except Exception as e:
        print(f"❌ WebSocket 测试失败: {e}")

if __name__ == "__main__":
    print("🚀 开始 WebSocket 测试...")
    asyncio.run(test_websocket())
    print("✅ WebSocket 测试完成") 