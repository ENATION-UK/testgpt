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

    os.environ["ANONYMIZED_TELEMETRY"] = "false"
    os.environ["BROWSER_USE_CLOUD_SYNC"] = "false"
        
    # 检查环境变量
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    reload = os.getenv("RELOAD", "true").lower() == "true"
    
    print(f"📍 服务地址: http://{host}:{port}")
    print(f"🔄 自动重载: {reload}")
    print(f"📖 API文档: http://{host}:{port}/docs")
    print(f"📖 ReDoc文档: http://{host}:{port}/redoc")
    
    # 在启动服务前输出配置信息
    try:
        from autotest.config_manager import ConfigManager
        print("\n📁 配置管理器路径信息:")
        config_manager = ConfigManager()
        print(f"   数据目录: {config_manager.data_dir}")
        print(f"   数据库文件: {config_manager.get_database_path()}")
        print(f"   多模型配置: {config_manager.get_multi_model_config_path()}")
        print(f"   提示词配置: {config_manager.get_prompt_config_path()}")
        print(f"   历史缓存目录: {config_manager.get_history_directory()}")
        print(f"   截图目录: {config_manager.get_screenshots_directory()}")
        print(f"   测试历史缓存: {config_manager.get_test_history_cache_directory()}")
        print(f"   Docker环境: {config_manager.is_docker_environment()}")
        print("✅ 配置管理器初始化完成\n")
    except Exception as e:
        print(f"⚠️  配置管理器初始化失败: {e}\n")
    
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