"""
WebSocket 路由，处理实时连接和消息推送
"""

import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from ..websocket_manager import websocket_manager

router = APIRouter(tags=["WebSocket"])

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket 连接端点"""
    await websocket_manager.connect(websocket)
    try:
        while True:
            # 接收客户端消息
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # 处理不同类型的消息
            if message.get("type") == "subscribe_batch":
                batch_execution_id = message.get("batch_execution_id")
                if batch_execution_id:
                    await websocket_manager.subscribe_to_batch(websocket, batch_execution_id)
                    await websocket_manager.send_personal_message(
                        json.dumps({
                            "type": "subscription_confirmed",
                            "batch_execution_id": batch_execution_id,
                            "message": f"已订阅批量执行任务 {batch_execution_id} 的进度更新"
                        }),
                        websocket
                    )
            
            elif message.get("type") == "unsubscribe_batch":
                batch_execution_id = message.get("batch_execution_id")
                if batch_execution_id:
                    websocket_manager.unsubscribe_from_batch(websocket, batch_execution_id)
                    await websocket_manager.send_personal_message(
                        json.dumps({
                            "type": "unsubscription_confirmed",
                            "batch_execution_id": batch_execution_id,
                            "message": f"已取消订阅批量执行任务 {batch_execution_id} 的进度更新"
                        }),
                        websocket
                    )
            
            elif message.get("type") == "ping":
                # 心跳检测
                await websocket_manager.send_personal_message(
                    json.dumps({"type": "pong"}),
                    websocket
                )
    
    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket)
    except Exception as e:
        print(f"WebSocket 错误: {e}")
        websocket_manager.disconnect(websocket) 