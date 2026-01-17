"""自动清空旧数据（不需要确认）"""
import sqlite3
import os

DB_NAME = "multi_source.db"
REPORT_FILE = "analysis_report.json"

print("=" * 60)
print("清空旧数据")
print("=" * 60)

# 1. 删除报告文件
if os.path.exists(REPORT_FILE):
    os.remove(REPORT_FILE)
    print(f"✓ 已删除 {REPORT_FILE}")
else:
    print(f"  {REPORT_FILE} 不存在")

# 2. 清空数据库表
conn = sqlite3.connect(DB_NAME)
cursor = conn.cursor()

try:
    cursor.execute("DELETE FROM cleaned_data")
    conn.commit()
    print(f"✓ 已清空 cleaned_data 表")
except Exception as e:
    print(f"⚠️ 清空 cleaned_data 失败: {e}")

conn.close()

print("\n所有旧数据已清空！")
print("现在可以测试新的关键词功能了。")
