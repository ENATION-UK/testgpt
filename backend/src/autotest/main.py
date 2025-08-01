"""
FastAPI application with complete REST API for web automation testing
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import uvicorn

from .database import init_db
from .routers import test_cases, test_executions, statistics, config

# 创建FastAPI应用实例
app = FastAPI(
    title="AutoTest API",
    description="Web自动化测试工具API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== 基础路由 ====================

@app.get("/")
async def root():
    """根路径，返回欢迎信息"""
    return {
        "message": "Welcome to AutoTest API!",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }

@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {
        "status": "healthy",
        "service": "autotest-api",
        "timestamp": datetime.utcnow()
    }

# ==================== 注册路由模块 ====================

# 测试用例管理路由
app.include_router(test_cases.router)

# 测试执行路由
app.include_router(test_executions.router)

# 统计信息路由
app.include_router(statistics.router)

# 配置管理路由
app.include_router(config.router)

# ==================== 应用启动事件 ====================

@app.on_event("startup")
async def startup_event():
    """应用启动时初始化数据库"""
    init_db()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000) 