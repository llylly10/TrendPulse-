"""
清空所有数据，恢复到初始状态
"""
import sqlite3
import os

DB_NAME = "multi_source.db"
REPORT_FILE = "analysis_report.json"

def clear_all_data():
    """清空数据库和报告文件"""
    
    # 1. 删除报告文件
    if os.path.exists(REPORT_FILE):
        os.remove(REPORT_FILE)
        print(f"✓ 已删除 {REPORT_FILE}")
    
    # 2. 清空数据库表
    if os.path.exists(DB_NAME):
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        # 清空 cleaned_data 表
        try:
            cursor.execute("DELETE FROM cleaned_data")
            print("✓ 已清空 cleaned_data 表")
        except:
            print("⚠ cleaned_data 表不存在或已为空")
        
        # 清空订阅表（可选）
        try:
            cursor.execute("DELETE FROM subscriptions")
            print("✓ 已清空 subscriptions 表")
        except:
            print("⚠ subscriptions 表不存在或已为空")
        
        # 清空报警表（可选）
        try:
            cursor.execute("DELETE FROM alerts")
            print("✓ 已清空 alerts 表")
        except:
            print("⚠ alerts 表不存在或已为空")
        
        conn.commit()
        conn.close()
        print(f"✓ 数据库已清空")
    else:
        print(f"⚠ 数据库文件 {DB_NAME} 不存在")
    
    print("\n所有数据已清空！现在可以看到空状态了。")

if __name__ == "__main__":
    print("=" * 50)
    print("清空所有数据")
    print("=" * 50 + "\n")
    
    confirm = input("确定要清空所有数据吗？(yes/no): ")
    if confirm.lower() == 'yes':
        clear_all_data()
    else:
        print("已取消")
