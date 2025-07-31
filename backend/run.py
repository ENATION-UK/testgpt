#!/usr/bin/env python3
"""
启动脚本
用于启动AutoTest API服务
"""

import uvicorn
import os
import sys
from pathlib import Path

# 添加src目录到Python路径
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

def main():
    """主函数"""
    print("🚀 启动AutoTest API服务...")
    
    # 检查环境变量
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    reload = os.getenv("RELOAD", "true").lower() == "true"
    
    print(f"📍 服务地址: http://{host}:{port}")
    print(f"🔄 自动重载: {reload}")
    print(f"📖 API文档: http://{host}:{port}/docs")
    print(f"📖 ReDoc文档: http://{host}:{port}/redoc")
    
    # 启动服务
    uvicorn.run(
        "autotest.main:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )

if __name__ == "__main__":
    main() 