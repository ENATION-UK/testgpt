#!/usr/bin/env python3
"""
测试项目设置是否正确
"""

import os
import sys
import subprocess
import requests
import time

def test_backend():
    """测试后端API"""
    print("🔍 测试后端API...")
    
    try:
        # 检查后端目录
        if not os.path.exists("backend"):
            print("❌ 后端目录不存在")
            return False
            
        # 检查后端依赖
        if not os.path.exists("backend/pyproject.toml"):
            print("❌ 后端依赖文件不存在")
            return False
            
        print("✅ 后端目录结构正确")
        return True
        
    except Exception as e:
        print(f"❌ 后端测试失败: {e}")
        return False

def test_frontend():
    """测试前端设置"""
    print("🔍 测试前端设置...")
    
    try:
        # 检查前端目录
        if not os.path.exists("frontend"):
            print("❌ 前端目录不存在")
            return False
            
        # 检查前端依赖
        if not os.path.exists("frontend/package.json"):
            print("❌ 前端依赖文件不存在")
            return False
            
        # 检查前端源码
        if not os.path.exists("frontend/src"):
            print("❌ 前端源码目录不存在")
            return False
            
        print("✅ 前端目录结构正确")
        return True
        
    except Exception as e:
        print(f"❌ 前端测试失败: {e}")
        return False

def test_root_config():
    """测试根目录配置"""
    print("🔍 测试根目录配置...")
    
    try:
        # 检查根目录package.json
        if not os.path.exists("package.json"):
            print("❌ 根目录package.json不存在")
            return False
            
        # 检查脚本目录
        if not os.path.exists("scripts"):
            print("❌ 脚本目录不存在")
            return False
            
        # 检查Docker配置
        if not os.path.exists("docker"):
            print("❌ Docker配置目录不存在")
            return False
            
        print("✅ 根目录配置正确")
        return True
        
    except Exception as e:
        print(f"❌ 根目录配置测试失败: {e}")
        return False

def main():
    """主函数"""
    print("🚀 开始测试项目设置...")
    print("=" * 50)
    
    tests = [
        ("后端设置", test_backend),
        ("前端设置", test_frontend),
        ("根目录配置", test_root_config),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}")
        print("-" * 30)
        if test_func():
            passed += 1
            print(f"✅ {test_name} 通过")
        else:
            print(f"❌ {test_name} 失败")
    
    print("\n" + "=" * 50)
    print(f"📊 测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！项目设置正确。")
        print("\n📝 下一步:")
        print("1. 运行 'npm run dev' 启动开发环境")
        print("2. 访问 http://localhost:3000 查看前端界面")
        print("3. 访问 http://localhost:8000/docs 查看API文档")
    else:
        print("⚠️  部分测试失败，请检查项目设置。")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 