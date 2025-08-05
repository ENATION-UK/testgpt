#!/usr/bin/env python3
"""
数据库迁移脚本 - 添加分类管理功能
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from sqlalchemy import create_engine, text, inspect
from src.autotest.database import DATABASE_URL, engine, SessionLocal

def migrate_categories():
    """执行分类管理相关的数据库迁移"""
    print("🔧 开始执行分类管理数据库迁移...")
    
    # 检查数据库类型
    is_sqlite = 'sqlite' in DATABASE_URL.lower()
    
    with engine.connect() as conn:
        inspector = inspect(engine)
        
        # 检查分类表是否存在
        if is_sqlite:
            # SQLite方式检查表是否存在
            result = conn.execute(text("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='category'
            """))
            category_exists = result.fetchone() is not None
        else:
            # MySQL方式检查表是否存在
            result = conn.execute(text("""
                SELECT COUNT(*) 
                FROM information_schema.tables 
                WHERE table_schema = 'autotest' 
                AND table_name = 'category'
            """))
            category_exists = result.scalar() > 0
        
        if not category_exists:
            print("📝 创建分类表...")
            if is_sqlite:
                conn.execute(text("""
                    CREATE TABLE category (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name VARCHAR(100) NOT NULL,
                        description TEXT,
                        parent_id INTEGER,
                        level INTEGER DEFAULT 0,
                        sort_order INTEGER DEFAULT 0,
                        is_active BOOLEAN DEFAULT 1,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        is_deleted BOOLEAN DEFAULT 0,
                        FOREIGN KEY (parent_id) REFERENCES category(id)
                    )
                """))
            else:
                conn.execute(text("""
                    CREATE TABLE category (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        name VARCHAR(100) NOT NULL COMMENT '分类名称',
                        description TEXT COMMENT '分类描述',
                        parent_id INT COMMENT '父分类ID',
                        level INT DEFAULT 0 COMMENT '分类层级',
                        sort_order INT DEFAULT 0 COMMENT '排序顺序',
                        is_active BOOLEAN DEFAULT TRUE COMMENT '是否激活',
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
                        is_deleted BOOLEAN DEFAULT FALSE COMMENT '是否删除',
                        FOREIGN KEY (parent_id) REFERENCES category(id)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='分类表'
                """))
            print("✅ 分类表创建成功")
        else:
            print("ℹ️  分类表已存在")
        
        # 检查测试用例表是否有category_id字段
        if is_sqlite:
            # SQLite方式检查字段是否存在
            result = conn.execute(text("PRAGMA table_info(test_case)"))
            columns = [row[1] for row in result.fetchall()]
            category_id_exists = 'category_id' in columns
        else:
            # MySQL方式检查字段是否存在
            result = conn.execute(text("""
                SELECT COUNT(*) 
                FROM information_schema.columns 
                WHERE table_schema = 'autotest' 
                AND table_name = 'test_case' 
                AND column_name = 'category_id'
            """))
            category_id_exists = result.scalar() > 0
        
        if not category_id_exists:
            print("📝 为测试用例表添加category_id字段...")
            conn.execute(text("""
                ALTER TABLE test_case 
                ADD COLUMN category_id INTEGER
            """))
            print("✅ category_id字段添加成功")
        else:
            print("ℹ️  category_id字段已存在")
        
        # 创建一些示例分类数据
        print("📝 创建示例分类数据...")
        
        # 检查是否已有数据
        result = conn.execute(text("SELECT COUNT(*) FROM category"))
        if result.scalar() == 0:
            # 创建根分类
            conn.execute(text("""
                INSERT INTO category (name, description, level, sort_order) VALUES
                ('功能测试', '功能测试相关用例', 0, 1),
                ('性能测试', '性能测试相关用例', 0, 2),
                ('安全测试', '安全测试相关用例', 0, 3),
                ('兼容性测试', '兼容性测试相关用例', 0, 4)
            """))
            
            # 获取根分类ID
            result = conn.execute(text("SELECT id FROM category WHERE name = '功能测试'"))
            func_test_id = result.scalar()
            
            result = conn.execute(text("SELECT id FROM category WHERE name = '性能测试'"))
            perf_test_id = result.scalar()
            
            # 创建子分类
            conn.execute(text(f"""
                INSERT INTO category (name, description, parent_id, level, sort_order) VALUES
                ('用户管理', '用户注册、登录、权限管理等功能测试', {func_test_id}, 1, 1),
                ('订单管理', '订单创建、支付、退款等功能测试', {func_test_id}, 1, 2),
                ('商品管理', '商品上架、下架、库存管理等功能测试', {func_test_id}, 1, 3),
                ('压力测试', '高并发、大数据量压力测试', {perf_test_id}, 1, 1),
                ('负载测试', '系统负载能力测试', {perf_test_id}, 1, 2)
            """))
            
            print("✅ 示例分类数据创建成功")
        else:
            print("ℹ️  分类数据已存在")
        
        conn.commit()
    
    print("🎉 分类管理数据库迁移完成！")

if __name__ == "__main__":
    migrate_categories() 