#!/usr/bin/env python3
"""
测试数据隔离修复
验证新采集的数据不会包含旧关键词的内容
"""

import sqlite3

print("="*60)
print("检查数据隔离问题")
print("="*60)

conn = sqlite3.connect('multi_source.db')
cursor = conn.cursor()

# 1. 查看所有关键词
print("\n1. 数据库中的关键词:")
cursor.execute('SELECT keyword, COUNT(*) FROM cleaned_data GROUP BY keyword')
for row in cursor.fetchall():
    print(f'   {row[0]}: {row[1]} 条')

# 2. 检查 "河北" 的数据
print("\n2. 检查 '河北' 的数据内容:")
cursor.execute("SELECT content FROM cleaned_data WHERE keyword = '河北' LIMIT 5")
hebei_data = cursor.fetchall()

if hebei_data:
    print(f"   找到 {len(hebei_data)} 条数据（显示前5条）:")
    for i, row in enumerate(hebei_data, 1):
        content = row[0][:80]
        print(f"   {i}. {content}...")
        
        # 检查是否包含不相关的关键词
        unrelated_keywords = ['ChatGPT', 'Claude', 'Gemini', 'DeepSeek', 'AI model']
        found_unrelated = [kw for kw in unrelated_keywords if kw.lower() in content.lower()]
        if found_unrelated:
            print(f"      ⚠️  包含不相关关键词: {found_unrelated}")
else:
    print("   没有数据")

# 3. 检查最近的采集任务
print("\n3. 最近的采集任务:")
cursor.execute('SELECT task_id, source_type, keyword FROM crawl_task ORDER BY task_id DESC LIMIT 6')
recent_tasks = cursor.fetchall()
for task in recent_tasks:
    print(f'   Task {task[0]}: {task[1]} - {task[2]}')

# 4. 检查 "河北" 任务采集的原始数据
print("\n4. '河北' 任务的原始数据:")
hebei_tasks = [t[0] for t in recent_tasks if t[2] == '河北']
if hebei_tasks:
    for task_id in hebei_tasks[:3]:
        cursor.execute('SELECT source_type FROM crawl_task WHERE task_id = ?', (task_id,))
        source = cursor.fetchone()[0]
        
        if source == 'youtube':
            cursor.execute('SELECT COUNT(*), title FROM youtube_video WHERE task_id = ? GROUP BY title LIMIT 1', (task_id,))
            result = cursor.fetchone()
            if result:
                print(f'   Task {task_id} (YouTube): {result[0]} 条, 示例: {result[1][:60]}...')
        elif source == 'twitter':
            cursor.execute('SELECT COUNT(*), content FROM twitter_tweet WHERE task_id = ? GROUP BY content LIMIT 1', (task_id,))
            result = cursor.fetchone()
            if result:
                print(f'   Task {task_id} (Twitter): {result[0]} 条, 示例: {result[1][:60]}...')

conn.close()

print("\n" + "="*60)
print("分析结果:")
print("="*60)
print("""
如果 '河北' 的数据中包含 ChatGPT、Claude、Gemini 等内容，
说明数据清洗时把旧数据也标记成了新关键词。

修复方法：
1. 修改 data_cleaning.py 的 process_data() 函数
2. 只处理指定 task_ids 的数据
3. 修改 collect.py 传递 task_ids 参数

修复后需要：
1. 清空 cleaned_data 表
2. 重新采集数据
3. 验证数据隔离正确
""")
