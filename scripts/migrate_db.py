#!/usr/bin/env python3
"""
数据库迁移脚本

从原QQ机器人的todos.db迁移到新的Web版本数据库
删除 user_id 和 group_id 字段，保留其他所有数据
"""

import sqlite3
import shutil
from datetime import datetime
from pathlib import Path


def migrate_database(source_db: str, target_db: str):
    """
    迁移数据库
    :param source_db: 原数据库路径
    :param target_db: 新数据库路径
    """
    source_path = Path(source_db)
    target_path = Path(target_db)
    
    if not source_path.exists():
        print(f"错误: 原数据库不存在 {source_db}")
        print("提示: 如果数据库已存在于目标位置，请直接启动应用即可")
        return False
    
    print(f"开始迁移数据库...")
    print(f"原数据库: {source_db}")
    print(f"目标数据库: {target_db}")
    
    # 1. 备份原数据库
    backup_path = source_path.parent / f"{source_path.stem}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
    shutil.copy2(source_path, backup_path)
    print(f"✓ 已备份原数据库到: {backup_path}")
    
    # 2. 连接源数据库和目标数据库
    conn_source = sqlite3.connect(source_db)
    cursor_source = conn_source.cursor()
    
    conn_target = sqlite3.connect(target_db)
    cursor_target = conn_target.cursor()
    
    try:
        # 3. 在目标数据库创建新表（无user_id/group_id）
        print(f"创建新的todos表...")
        cursor_target.execute('''
            CREATE TABLE IF NOT EXISTS todos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content TEXT NOT NULL,
                priority INTEGER NOT NULL,
                created_at TIMESTAMP NOT NULL,
                deadline TIMESTAMP NOT NULL,
                skip_reminder BOOLEAN DEFAULT 0,
                completed BOOLEAN DEFAULT 0,
                completed_at TIMESTAMP,
                notified_20 BOOLEAN DEFAULT 0,
                notified_40 BOOLEAN DEFAULT 0,
                notified_60 BOOLEAN DEFAULT 0,
                notified_80 BOOLEAN DEFAULT 0,
                notified_12h BOOLEAN DEFAULT 0,
                notified_24h BOOLEAN DEFAULT 0
            )
        ''')
        
        # 4. 从源数据库读取所有数据
        cursor_source.execute('SELECT * FROM todos')
        rows = cursor_source.fetchall()
        
        if not rows:
            print("✓ 源数据库没有数据")
            conn_target.commit()
            return True
        
        # 5. 获取源表的列信息，确定哪些列要保留
        cursor_source.execute('PRAGMA table_info(todos)')
        columns_info = cursor_source.fetchall()
        columns = [col[1] for col in columns_info]
        
        # 确定要复制的列索引
        # 旧表列顺序：id, user_id, group_id, content, priority, created_at, deadline, 
        #            skip_reminder, completed, completed_at, notified_20, ...
        cols_to_keep = [
            'content', 
            'priority', 
            'created_at', 
            'deadline', 
            'skip_reminder', 
            'completed', 
            'completed_at', 
            'notified_20', 
            'notified_40', 
            'notified_60', 
            'notified_80', 
            'notified_12h', 
            'notified_24h'
        ]
        
        # 构建列索引映射
        col_indices = []
        for col in cols_to_keep:
            if col in columns:
                col_indices.append(columns.index(col))
            else:
                col_indices.append(None)
        
        # 6. 复制数据（保留id）
        count = 0
        for row in rows:
            # id 要保留
            new_id = row[0]
            
            # 构建新值
            values = [new_id]
            for idx in col_indices:
                if idx is not None and idx < len(row):
                    values.append(row[idx])
                else:
                    values.append(None)
            
            # 插入新数据库
            cursor_target.execute('''
                INSERT OR REPLACE INTO todos (
                    id, content, priority, created_at, deadline, 
                    skip_reminder, completed, completed_at, 
                    notified_20, notified_40, notified_60, notified_80, 
                    notified_12h, notified_24h
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', values)
            count += 1
        
        # 7. 提交事务
        conn_target.commit()
        print(f"✓ 成功迁移 {count} 条待办数据")
        
        # 8. 验证迁移结果
        cursor_target.execute('SELECT COUNT(*) FROM todos')
        migrated_count = cursor_target.fetchone()[0]
        print(f"✓ 验证: 新数据库中有 {migrated_count} 条记录")
        
        return True
        
    except Exception as e:
        conn_target.rollback()
        print(f"✗ 迁移失败: {e}")
        return False
    finally:
        conn_source.close()
        conn_target.close()


if __name__ == "__main__":
    import sys
    
    # 默认路径 - 使用 backend/data/todos.db 作为源和目标
    DEFAULT_SOURCE = "backend/data/todos.db"
    DEFAULT_TARGET = "backend/data/todos.db"
    
    source_db = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_SOURCE
    target_db = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_TARGET
    
    # 确保目标目录存在
    Path(target_db).parent.mkdir(parents=True, exist_ok=True)
    
    # 如果源和目标相同且文件已存在，提示用户
    if source_db == target_db and Path(source_db).exists():
        print(f"提示: 数据库 {source_db} 已存在")
        print("如果需要从其他位置迁移数据，请提供源数据库路径:")
        print("  python scripts/migrate_db.py /path/to/old/todos.db")
        sys.exit(0)
    
    success = migrate_database(source_db, target_db)
    
    if success:
        print("\n🎉 数据库迁移完成！")
    else:
        print("\n❌ 数据库迁移失败")
        sys.exit(1)
