"""检查订阅状态"""
import sqlite3
import time
from datetime import datetime

conn = sqlite3.connect('multi_source.db')
cursor = conn.cursor()

cursor.execute('SELECT id, keyword, interval_seconds, last_run, next_run FROM subscriptions')
rows = cursor.fetchall()

print('当前订阅:')
print('=' * 80)

now = int(time.time())
for r in rows:
    sub_id, keyword, interval_seconds, last_run, next_run = r
    print(f'ID: {sub_id}')
    print(f'  关键词: {keyword}')
    print(f'  间隔: {interval_seconds}秒')
    print(f'  last_run: {last_run} ({datetime.fromtimestamp(last_run) if last_run > 0 else "未执行"})')
    print(f'  next_run: {next_run} ({datetime.fromtimestamp(next_run) if next_run > 0 else "未设置"})')
    print(f'  当前时间: {now} ({datetime.fromtimestamp(now)})')
    print(f'  状态: {"待执行" if next_run <= now else f"等待中（还需 {next_run - now} 秒）"}')
    print()

conn.close()
