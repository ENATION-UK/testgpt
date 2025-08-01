#!/usr/bin/env python3
"""
MySQL数据库连接测试脚本
"""

import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# 设置环境变量使用MySQL
os.environ["USE_MYSQL"] = "true"

from autotest.database import test_connection, SessionLocal, TestCase
from sqlalchemy import text

def test_mysql_connection():
    """测试MySQL数据库连接"""
    print("🔍 测试MySQL数据库连接...")
    
    # 测试网络连接
    import subprocess
    try:
        result = subprocess.run(['ping', '-c', '3', '192.168.2.153'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("✅ 网络连接正常")
        else:
            print("❌ 网络连接失败")
            print("请检查:")
            print("1. 网络连接是否正常")
            print("2. MySQL服务器是否运行")
            print("3. 防火墙设置")
            return False
    except Exception as e:
        print(f"❌ 网络测试失败: {e}")
        return False
    
    # 测试数据库连接
    if test_connection():
        print("✅ MySQL数据库连接成功！")
        return True
    else:
        print("❌ MySQL数据库连接失败！")
        return False

def test_mysql_query():
    """测试MySQL查询"""
    print("\n🔍 测试MySQL查询...")
    
    try:
        db = SessionLocal()
        
        # 查询test_case表
        print("1. 查询test_case表:")
        result = db.execute(text("SELECT COUNT(*) as count FROM test_case"))
        count = result.fetchone()[0]
        print(f"   test_case表中共有 {count} 条记录")
        
        # 查询表结构
        print("2. 查询表结构:")
        result = db.execute(text("DESCRIBE test_case"))
        columns = result.fetchall()
        print("   表结构:")
        for col in columns:
            print(f"   - {col[0]}: {col[1]}")
        
        # 查询前几条记录
        print("3. 查询前5条记录:")
        result = db.execute(text("SELECT id, name, status FROM test_case LIMIT 5"))
        records = result.fetchall()
        for record in records:
            print(f"   ID: {record[0]}, 名称: {record[1]}, 状态: {record[2]}")
        
        db.close()
        print("✅ MySQL查询测试成功！")
        return True
        
    except Exception as e:
        print(f"❌ MySQL查询测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🚀 开始MySQL数据库测试...")
    print("=" * 50)
    
    if test_mysql_connection():
        test_mysql_query()
    else:
        print("\n💡 建议:")
        print("1. 检查MySQL服务器是否运行在192.168.2.153:3306")
        print("2. 确认用户名root和密码12346是否正确")
        print("3. 确认autotest数据库是否存在")
        print("4. 检查网络连接和防火墙设置")

if __name__ == "__main__":
    main() 