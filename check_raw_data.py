#!/usr/bin/env python3
"""检查原始采集数据"""
import sqlite3

conn = sqlite3.connect('multi_source.db')
cursor = conn.cursor()

# 检查最近的采集任务
print("最近5个采集任务:")
cursor.execute('SELECT task_id, source_type, keyword FROM crawl_task ORDER BY task_id DESC LIMIT 5')
tasks = cursor.fetchall()
for task in tasks:
    print(f'  Task {task[0]}: {task[1]} - {task[2]}')

# 检查每个任务对应的原始数据
print("\n检查原始数据:")
for task in tasks[:3]:  # 只检查最近3个
    task_id, source_type, keyword = task
    print(f'\nTask {task_id} ({source_type} - {keyword}):')
    
    if source_type == 'reddit':
        cursor.execute('SELECT COUNT(*) FROM reddit_submission WHERE task_id = ?', (task_id,))
        count = cursor.fetchone()[0]
        print(f'  Reddit 数据量: {count}')
        if count > 0:
            cursor.execute('SELECT title FROM reddit_submission WHERE task_id = ? LIMIT 2', (task_id,))
            for i, row in enumerate(cursor.fetchall(), 1):
                print(f'    {i}. {row[0][:60]}...')
    
    elif source_type == 'youtube':
        cursor.execute('SELECT COUNT(*) FROM youtube_video WHERE task_id = ?', (task_id,))
        count = cursor.fetchone()[0]
        print(f'  YouTube 数据量: {count}')
        if count > 0:
            cursor.execute('SELECT title FROM youtube_video WHERE task_id = ? LIMIT 2', (task_id,))
            for i, row in enumerate(cursor.fetchall(), 1):
                print(f'    {i}. {row[0][:60]}...')
    
    elif source_type == 'twitter':
        cursor.execute('SELECT COUNT(*) FROM twitter_tweet WHERE task_id = ?', (task_id,))
        count = cursor.fetchone()[0]
        print(f'  Twitter 数据量: {count}')
        if count > 0:
            cursor.execute('SELECT content FROM twitter_tweet WHERE task_id = ? LIMIT 2', (task_id,))
            for i, row in enumerate(cursor.fetchall(), 1):
                print(f'    {i}. {row[0][:60]}...')

conn.close()
