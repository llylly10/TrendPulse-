"""添加 keyword 字段到 cleaned_data 表"""
import sqlite3

conn = sqlite3.connect("multi_source.db")
cursor = conn.cursor()

try:
    # 检查是否已经有 keyword 列
    cursor.execute("PRAGMA table_info(cleaned_data)")
    columns = [col[1] for col in cursor.fetchall()]
    
    if 'keyword' in columns:
        print("✓ keyword 字段已存在")
    else:
        print("🔄 添加 keyword 字段...")
        
        # 添加 keyword 列
        cursor.execute("ALTER TABLE cleaned_data ADD COLUMN keyword TEXT")
        
        # 将现有数据的 keyword 设置为 'unknown'
        cursor.execute("UPDATE cleaned_data SET keyword = 'unknown' WHERE keyword IS NULL")
        
        conn.commit()
        print("✓ keyword 字段已添加")
        print("  - 现有数据的 keyword 已设置为 'unknown'")
        print("  - 建议清空旧数据：python clear_data.py")
        
except Exception as e:
    print(f"✗ 迁移失败: {e}")
    conn.rollback()
finally:
    conn.close()
