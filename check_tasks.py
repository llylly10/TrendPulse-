#!/usr/bin/env python3
"""检查采集任务"""
import sqlite3

conn = sqlite3.connect('multi_source.db')
cursor = conn.cursor()

cursor.execute('SELECT * FROM crawl_task ORDER BY task_id DESC LIMIT 10')
print('最近10个采集任务:')
for row in cursor.fetchall():
    print(f'  ID={row[0]}, source={row[1]}, keyword={row[2]}, language={row[3]}, limit={row[4]}')

conn.close()
