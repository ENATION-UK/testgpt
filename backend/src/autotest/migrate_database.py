"""
数据库迁移脚本
为test_step表添加新的字段以支持Browser-Use事件收集
"""

import sqlite3
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config_manager import ConfigManager

def migrate_database():
    """执行数据库迁移"""
    try:
        # 获取数据库路径
        config_manager = ConfigManager()
        db_path = config_manager.get_database_path()
        print(f"数据库路径: {db_path}")
        
        # 连接数据库
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 检查当前表结构
        cursor.execute('PRAGMA table_info(test_step);')
        columns = cursor.fetchall()
        existing_columns = [col[1] for col in columns]
        print(f"现有字段: {existing_columns}")
        
        # 需要添加的字段
        new_columns = [
            ("url", "VARCHAR(2000)"),
            ("actions", "JSON"),
            ("evaluation", "TEXT"),
            ("memory", "TEXT"),
            ("next_goal", "TEXT"),
            ("screenshot_data", "TEXT"),
            ("event_timestamp", "DATETIME"),
            ("step_metadata", "JSON")
        ]
        
        # 添加缺失的字段
        for column_name, column_type in new_columns:
            if column_name not in existing_columns:
                try:
                    cursor.execute(f'ALTER TABLE test_step ADD COLUMN {column_name} {column_type};')
                    print(f"✓ 添加字段: {column_name} ({column_type})")
                except sqlite3.OperationalError as e:
                    print(f"⚠️  添加字段 {column_name} 时出错: {e}")
            else:
                print(f"✓ 字段已存在: {column_name}")
        
        # 提交更改
        conn.commit()
        print("✓ 数据库迁移完成")
        
        # 验证新表结构
        cursor.execute('PRAGMA table_info(test_step);')
        columns = cursor.fetchall()
        print("\n更新后的表结构:")
        for col in columns:
            print(f"  {col[1]} ({col[2]})")
        
        # 关闭连接
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ 数据库迁移失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("开始数据库迁移...")
    success = migrate_database()
    if success:
        print("🎉 数据库迁移成功完成！")
        sys.exit(0)
    else:
        print("💥 数据库迁移失败！")
        sys.exit(1)