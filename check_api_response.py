#!/usr/bin/env python3
"""检查 API 返回的数据"""
import requests
import json

API_BASE = "http://localhost:8888/api"

print("检查 /api/source-data 返回的数据...")
response = requests.get(f"{API_BASE}/source-data")

if response.status_code == 200:
    data = response.json()
    print(f'\n返回数据量: {len(data)}')
    
    if data:
        print('\n前5条数据的关键词:')
        for i, item in enumerate(data[:5], 1):
            keyword = item.get('keyword', 'N/A')
            content = item.get('content', '')[:60]
            print(f'  {i}. keyword={keyword}, content={content}...')
        
        # 统计关键词分布
        keywords = {}
        for item in data:
            kw = item.get('keyword', 'unknown')
            keywords[kw] = keywords.get(kw, 0) + 1
        
        print('\n关键词分布:')
        for kw, count in keywords.items():
            print(f'  {kw}: {count} 条')
    else:
        print('没有数据')
else:
    print(f'请求失败: {response.status_code}')

print('\n检查 /api/dashboard 返回的数据...')
response = requests.get(f"{API_BASE}/dashboard")

if response.status_code == 200:
    data = response.json()
    print(f'当前关键词: {data.get("keyword", "N/A")}')
    print(f'数据量: {data.get("total_posts", 0)}')
else:
    print(f'请求失败: {response.status_code}')
