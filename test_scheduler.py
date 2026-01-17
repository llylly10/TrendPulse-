"""测试定时任务功能"""
import sqlite3
import time
from datetime import datetime

conn = sqlite3.connect("multi_source.db")
cursor = conn.cursor()

print("=" * 60)
print("定时任务测试")
print("=" * 60)

# 创建一个测试订阅（30秒间隔）
print("\n1. 创建测试订阅（30秒间隔）...")
cursor.execute("""
    INSERT INTO subscriptions (keyword, language, reddit_limit, youtube_limit, twitter_limit, interval_seconds, next_run)
    VALUES (?, ?, ?, ?, ?, ?, ?)
""", ("测试关键词", "zh", 10, 10, 10, 30, int(time.time())))
conn.commit()

sub_id = cursor.lastrowid
print(f"✓ 订阅已创建，ID: {sub_id}")

# 查询订阅信息
cursor.execute("SELECT * FROM subscriptions WHERE id = ?", (sub_id,))
sub = cursor.fetchone()
columns = [desc[0] for desc in cursor.description]
sub_dict = dict(zip(columns, sub))

print(f"\n订阅信息：")
print(f"  关键词: {sub_dict['keyword']}")
print(f"  间隔: {sub_dict['interval_seconds']} 秒")
print(f"  下次运行: {datetime.fromtimestamp(sub_dict['next_run'])}")

print("\n2. 等待定时任务触发...")
print("   提示：后端每分钟检查一次，请等待...")
print("   你可以在前端查看订阅列表，或者查看后端日志")

# 监控订阅状态
print("\n3. 监控订阅状态（按 Ctrl+C 停止）...")
try:
    last_run = sub_dict['last_run']
    while True:
        time.sleep(5)
        cursor.execute("SELECT last_run, next_run FROM subscriptions WHERE id = ?", (sub_id,))
        result = cursor.fetchone()
        if result:
            current_last_run, next_run = result
            if current_last_run != last_run:
                print(f"\n✓ 任务已执行！")
                print(f"  执行时间: {datetime.fromtimestamp(current_last_run)}")
                print(f"  下次运行: {datetime.fromtimestamp(next_run)}")
                last_run = current_last_run
            else:
                print(f"  等待中... 下次运行: {datetime.fromtimestamp(next_run)}", end='\r')
except KeyboardInterrupt:
    print("\n\n4. 清理测试数据...")
    cursor.execute("DELETE FROM subscriptions WHERE id = ?", (sub_id,))
    conn.commit()
    print("✓ 测试订阅已删除")

conn.close()
print("\n测试完成！")
