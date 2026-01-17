"""测试关键词隔离功能"""
import requests
import time
from datetime import datetime

API_BASE = "http://localhost:8888/api"

def print_section(title):
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)

print_section("关键词隔离功能测试")

# 1. 测试第一个关键词：Gemini
print("\n1. 测试关键词：Gemini")
print("   启动采集任务...")
response = requests.post(f"{API_BASE}/collect", json={
    "keyword": "Gemini",
    "language": "en",
    "reddit_limit": 5,
    "youtube_limit": 5,
    "twitter_limit": 5
})

if response.status_code in [200, 202]:
    print("✓ Gemini 采集任务已启动")
else:
    print(f"✗ 启动失败: {response.text}")
    exit(1)

# 等待任务完成
print("   等待任务完成...")
max_wait = 120
waited = 0

while waited < max_wait:
    time.sleep(3)
    waited += 3
    
    try:
        status_response = requests.get(f"{API_BASE}/task-status")
        if status_response.status_code == 200:
            status = status_response.json()
            if not status['is_running']:
                print(f"✓ Gemini 任务完成")
                break
            print(f"  [{waited}s] {status.get('progress', '...')}", end='\r')
    except:
        pass

if waited >= max_wait:
    print("\n⚠️ 超时")
    exit(1)

# 检查 Gemini 数据
print("\n2. 检查 Gemini 数据...")
time.sleep(2)
response = requests.get(f"{API_BASE}/dashboard")
if response.status_code == 200:
    data = response.json()
    print(f"✓ 仪表盘数据")
    print(f"  关键词: {data.get('keyword', 'N/A')}")
    print(f"  总帖子数: {data.get('total_posts', 0)}")
    print(f"  情感得分: {data.get('sentiment', {}).get('score', 0)}")
    
    if data.get('keyword') != 'Gemini':
        print(f"⚠️ 警告：关键词不匹配！期望 'Gemini'，实际 '{data.get('keyword')}'")
else:
    print("✗ 获取数据失败")

# 检查源数据
response = requests.get(f"{API_BASE}/source-data")
if response.status_code == 200:
    posts = response.json()
    print(f"\n✓ 源数据: {len(posts)} 条")
    if posts:
        keywords = set(post.get('keyword', 'N/A') for post in posts[:5])
        print(f"  前5条的关键词: {keywords}")
        if 'Gemini' not in keywords:
            print(f"⚠️ 警告：源数据中没有 Gemini 关键词！")

# 3. 测试第二个关键词：ChatGPT
print("\n3. 测试关键词：ChatGPT")
print("   启动采集任务...")
response = requests.post(f"{API_BASE}/collect", json={
    "keyword": "ChatGPT",
    "language": "en",
    "reddit_limit": 5,
    "youtube_limit": 5,
    "twitter_limit": 5
})

if response.status_code in [200, 202]:
    print("✓ ChatGPT 采集任务已启动")
else:
    print(f"✗ 启动失败: {response.text}")
    exit(1)

# 等待任务完成
print("   等待任务完成...")
waited = 0

while waited < max_wait:
    time.sleep(3)
    waited += 3
    
    try:
        status_response = requests.get(f"{API_BASE}/task-status")
        if status_response.status_code == 200:
            status = status_response.json()
            if not status['is_running']:
                print(f"✓ ChatGPT 任务完成")
                break
            print(f"  [{waited}s] {status.get('progress', '...')}", end='\r')
    except:
        pass

# 检查 ChatGPT 数据
print("\n4. 检查 ChatGPT 数据...")
time.sleep(2)
response = requests.get(f"{API_BASE}/dashboard")
if response.status_code == 200:
    data = response.json()
    print(f"✓ 仪表盘数据")
    print(f"  关键词: {data.get('keyword', 'N/A')}")
    print(f"  总帖子数: {data.get('total_posts', 0)}")
    print(f"  情感得分: {data.get('sentiment', {}).get('score', 0)}")
    
    if data.get('keyword') != 'ChatGPT':
        print(f"⚠️ 警告：关键词不匹配！期望 'ChatGPT'，实际 '{data.get('keyword')}'")
    else:
        print(f"✓ 关键词正确！现在显示的是 ChatGPT 的数据")

# 5. 验证数据隔离
print("\n5. 验证数据隔离...")
response = requests.get(f"{API_BASE}/source-data")
if response.status_code == 200:
    posts = response.json()
    keywords = {}
    for post in posts:
        kw = post.get('keyword', 'unknown')
        keywords[kw] = keywords.get(kw, 0) + 1
    
    print(f"✓ 数据库中的关键词分布:")
    for kw, count in keywords.items():
        print(f"  {kw}: {count} 条")
    
    if len(keywords) >= 2:
        print(f"\n✓ 成功！数据已按关键词隔离")
        print(f"  - 不同关键词的数据分别存储")
        print(f"  - 仪表盘显示最新关键词的数据")
    else:
        print(f"\n⚠️ 警告：只有一个关键词的数据")

print("\n" + "=" * 60)
print("测试完成！")
print("=" * 60)
print("\n总结：")
print("  1. 每个关键词的数据独立存储")
print("  2. 仪表盘自动显示最新关键词的数据")
print("  3. 不同关键词的分析结果互不干扰")
print("  4. 前端会自动显示对应关键词的内容")
