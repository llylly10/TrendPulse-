#!/usr/bin/env python3
"""检查数据库中的关键词"""
import sqlite3

conn = sqlite3.connect('multi_source.db')
cursor = conn.cursor()

# 获取所有关键词
cursor.execute('SELECT DISTINCT keyword FROM cleaned_data')
keywords = [row[0] for row in cursor.fetchall()]
print('数据库中的关键词:', keywords)

# 每个关键词的数据量
print('\n每个关键词的数据量:')
cursor.execute('SELECT keyword, COUNT(*) FROM cleaned_data GROUP BY keyword')
for row in cursor.fetchall():
    print(f'  {row[0]}: {row[1]} 条')

# 获取最新的关键词
cursor.execute("SELECT keyword FROM cleaned_data WHERE keyword != 'unknown' ORDER BY rowid DESC LIMIT 1")
result = cursor.fetchone()
if result:
    print(f'\n最新关键词: {result[0]}')

# 查看 河北 的数据
cursor.execute("SELECT COUNT(*) FROM cleaned_data WHERE keyword = '河北'")
count = cursor.fetchone()[0]
print(f'\n河北 的数据量: {count}')

if count > 0:
    cursor.execute("SELECT content FROM cleaned_data WHERE keyword = '河北' LIMIT 3")
    print('\n河北 的前3条数据:')
    for i, row in enumerate(cursor.fetchall(), 1):
        print(f'{i}. {row[0][:80]}...')
else:
    print('河北 没有数据！')

conn.close()
