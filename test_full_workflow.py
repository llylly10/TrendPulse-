"""测试完整的定时任务工作流程"""
import sqlite3
import time
import requests
from datetime import datetime

API_BASE = "http://localhost:8888/api"

print("=" * 60)
print("完整工作流程测试")
print("=" * 60)

# 1. 创建一个1分钟间隔的订阅
print("\n1. 创建测试订阅（1分钟间隔）...")
response = requests.post(f"{API_BASE}/subscriptions", json={
    "keyword": "测试AI",
    "language": "zh",
    "reddit_limit": 5,
    "youtube_limit": 5,
    "twitter_limit": 5,
    "interval_seconds": 60  # 1分钟
})

if response.status_code == 200:
    print("✓ 订阅创建成功")
else:
    print(f"✗ 订阅创建失败: {response.text}")
    exit(1)

# 2. 查询订阅列表
print("\n2. 查询订阅列表...")
response = requests.get(f"{API_BASE}/subscriptions")
subscriptions = response.json()
print(f"✓ 找到 {len(subscriptions)} 个订阅")

if subscriptions:
    sub = subscriptions[0]
    print(f"\n订阅详情:")
    print(f"  ID: {sub['id']}")
    print(f"  关键词: {sub['keyword']}")
    print(f"  间隔: {sub['interval_seconds']} 秒")
    print(f"  下次运行: {datetime.fromtimestamp(sub['next_run'])}")
    
    # 3. 等待任务执行
    print("\n3. 等待定时任务触发（最多等待2分钟）...")
    print("   提示：后端每分钟检查一次")
    
    last_run = sub['last_run']
    max_wait = 120  # 最多等待2分钟
    waited = 0
    
    while waited < max_wait:
        time.sleep(5)
        waited += 5
        
        # 检查订阅状态
        response = requests.get(f"{API_BASE}/subscriptions")
        subscriptions = response.json()
        
        if subscriptions:
            current_sub = subscriptions[0]
            if current_sub['last_run'] != last_run:
                print(f"\n✓ 任务已执行！")
                print(f"  执行时间: {datetime.fromtimestamp(current_sub['last_run'])}")
                print(f"  下次运行: {datetime.fromtimestamp(current_sub['next_run'])}")
                
                # 4. 检查是否有新数据
                print("\n4. 检查仪表盘数据...")
                response = requests.get(f"{API_BASE}/dashboard")
                if response.status_code == 200:
                    data = response.json()
                    print(f"✓ 数据已更新")
                    print(f"  总帖子数: {data['total_posts']}")
                    print(f"  情感得分: {data['sentiment']['score']}")
                    
                    # 5. 检查报警
                    print("\n5. 检查报警...")
                    response = requests.get(f"{API_BASE}/alerts")
                    alerts = response.json()
                    print(f"✓ 找到 {len(alerts)} 条报警")
                    if alerts:
                        for alert in alerts[:3]:
                            print(f"  - {alert['message']}")
                else:
                    print("⚠️ 暂无数据")
                
                break
        
        print(f"  等待中... ({waited}/{max_wait}秒)", end='\r')
    
    if waited >= max_wait:
        print("\n⚠️ 超时：任务未在预期时间内执行")
        print("   请检查后端日志")
    
    # 6. 清理
    print("\n6. 清理测试数据...")
    response = requests.delete(f"{API_BASE}/subscriptions/{sub['id']}")
    if response.status_code == 200:
        print("✓ 测试订阅已删除")
else:
    print("⚠️ 未找到订阅")

print("\n测试完成！")
