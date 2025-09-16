#!/usr/bin/env python3
"""
数据库连接和查询测试脚本
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from testgpt.database import test_connection, SessionLocal, TestCase
from sqlalchemy import text

def test_database_connection():
    """测试数据库连接"""
    print("🔍 测试数据库连接...")
    if test_connection():
        print("✅ 数据库连接测试通过！")
        return True
    else:
        print("❌ 数据库连接测试失败！")
        return False

def test_query_test_case_table():
    """测试查询test_case表"""
    print("\n🔍 测试查询test_case表...")
    
    try:
        db = SessionLocal()
        
        # 方法1: 使用原生SQL查询
        print("1. 使用原生SQL查询:")
        result = db.execute(text("SELECT COUNT(*) as count FROM test_case"))
        count = result.fetchone()[0]
        print(f"   test_case表中共有 {count} 条记录")
        
        # 方法2: 使用ORM查询
        print("2. 使用ORM查询:")
        test_cases = db.query(TestCase).all()
        print(f"   通过ORM查询到 {len(test_cases)} 条记录")
        
        # 显示前5条记录
        if test_cases:
            print("   前5条记录:")
            for i, case in enumerate(test_cases[:5]):
                print(f"   {i+1}. ID: {case.id}, 名称: {case.name}, 状态: {case.status}")
        else:
            print("   表中暂无数据")
        
        # 方法3: 查询特定状态的记录
        print("3. 查询活跃状态的记录:")
        active_cases = db.query(TestCase).filter(TestCase.status == "active").all()
        print(f"   活跃状态的记录: {len(active_cases)} 条")
        
        # 方法4: 查询表结构
        print("4. 查询表结构:")
        result = db.execute(text("DESCRIBE test_case"))
        columns = result.fetchall()
        print("   表结构:")
        for col in columns:
            print(f"   - {col[0]}: {col[1]}")
        
        db.close()
        print("✅ test_case表查询测试通过！")
        return True
        
    except Exception as e:
        print(f"❌ test_case表查询测试失败: {e}")
        return False

def test_create_test_case():
    """测试创建测试用例"""
    print("\n🔍 测试创建测试用例...")
    
    try:
        db = SessionLocal()
        
        # 创建测试用例
        new_case = TestCase(
            name="API测试用例",
            description="这是一个通过ORM创建的测试用例",
            status="active"
        )
        
        db.add(new_case)
        db.commit()
        db.refresh(new_case)
        
        print(f"✅ 成功创建测试用例，ID: {new_case.id}")
        
        # 验证创建
        created_case = db.query(TestCase).filter(TestCase.id == new_case.id).first()
        if created_case:
            print(f"   验证成功: {created_case.name}")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"❌ 创建测试用例失败: {e}")
        db.rollback()
        db.close()
        return False

def main():
    """主测试函数"""
    print("🚀 开始数据库测试...")
    print("=" * 50)
    
    # 测试数据库连接
    if not test_database_connection():
        print("❌ 数据库连接失败，无法继续测试")
        return
    
    # 测试查询test_case表
    if not test_query_test_case_table():
        print("❌ test_case表查询失败")
        return
    
    # 测试创建测试用例
    test_create_test_case()
    
    print("\n✅ 所有数据库测试完成！")

if __name__ == "__main__":
    main() 