#!/usr/bin/env python3
"""
测试前端源数据更新问题
验证API返回的数据是否正确按关键词过滤
"""

import requests
import json
import time

API_BASE = "http://localhost:8888/api"

def test_source_data_endpoint():
    """测试源数据端点是否正确返回数据"""
    print("=" * 60)
    print("测试源数据API端点")
    print("=" * 60)
    
    # 1. 获取仪表盘数据，查看当前关键词
    print("\n1. 获取仪表盘数据...")
    response = requests.get(f"{API_BASE}/dashboard")
    if response.status_code == 200:
        dashboard = response.json()
        current_keyword = dashboard.get("keyword", "未知")
        print(f"   ✓ 当前关键词: {current_keyword}")
        print(f"   ✓ 总数据量: {dashboard.get('total_posts', 0)}")
    else:
        print(f"   ✗ 获取仪表盘失败: {response.status_code}")
        return
    
    # 2. 获取源数据（不指定关键词，应该自动使用最新关键词）
    print("\n2. 获取源数据（自动检测关键词）...")
    response = requests.get(f"{API_BASE}/source-data")
    if response.status_code == 200:
        posts = response.json()
        print(f"   ✓ 返回数据量: {len(posts)}")
        
        if posts:
            # 检查所有数据的关键词
            keywords = set()
            for post in posts:
                if 'keyword' in post:
                    keywords.add(post['keyword'])
            
            print(f"   ✓ 数据中的关键词: {keywords}")
            
            # 显示前3条数据
            print("\n   前3条数据:")
            for i, post in enumerate(posts[:3]):
                print(f"   [{i+1}] 关键词: {post.get('keyword', 'N/A')}")
                print(f"       平台: {post.get('platform', 'N/A')}")
                print(f"       作者: {post.get('author', 'N/A')}")
                print(f"       内容: {post.get('content', 'N/A')[:50]}...")
                print()
        else:
            print("   ! 没有数据")
    else:
        print(f"   ✗ 获取源数据失败: {response.status_code}")
    
    # 3. 直接查询数据库，验证数据
    print("\n3. 直接查询数据库...")
    import sqlite3
    try:
        conn = sqlite3.connect("trendpulse.db")
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # 获取所有关键词
        cursor.execute("SELECT DISTINCT keyword FROM cleaned_data WHERE keyword != 'unknown'")
        all_keywords = [row[0] for row in cursor.fetchall()]
        print(f"   ✓ 数据库中的关键词: {all_keywords}")
        
        # 获取每个关键词的数据量
        for kw in all_keywords:
            cursor.execute("SELECT COUNT(*) FROM cleaned_data WHERE keyword = ?", (kw,))
            count = cursor.fetchone()[0]
            print(f"   ✓ {kw}: {count} 条数据")
        
        # 获取最新的关键词
        cursor.execute("SELECT keyword FROM cleaned_data WHERE keyword != 'unknown' ORDER BY rowid DESC LIMIT 1")
        result = cursor.fetchone()
        if result:
            latest_keyword = result[0]
            print(f"\n   ✓ 最新关键词: {latest_keyword}")
            
            # 验证这个关键词的数据
            cursor.execute("SELECT COUNT(*) FROM cleaned_data WHERE keyword = ?", (latest_keyword,))
            count = cursor.fetchone()[0]
            print(f"   ✓ 最新关键词数据量: {count}")
        
        conn.close()
    except Exception as e:
        print(f"   ✗ 数据库查询失败: {e}")
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)

if __name__ == "__main__":
    test_source_data_endpoint()
