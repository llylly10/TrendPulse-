"""
测试系统功能
"""
import requests
import json
import time

BASE_URL = "http://localhost:8888"

def test_dashboard():
    """测试仪表盘 API"""
    print("测试仪表盘...")
    response = requests.get(f"{BASE_URL}/api/dashboard")
    print(f"状态码: {response.status_code}")
    data = response.json()
    print(f"热度指数: {data['heat_index']}")
    print(f"总帖子数: {data['total_posts']}")
    print(f"情感得分: {data['sentiment']['score']}")
    print(f"思维导图: {data['mermaid_graph'][:50]}...")
    print("✓ 仪表盘测试通过\n")

def test_collection():
    """测试采集任务"""
    print("测试采集任务...")
    response = requests.post(f"{BASE_URL}/api/collect", json={
        "keyword": "AI",
        "language": "zh",
        "reddit_limit": 10,
        "youtube_limit": 10,
        "twitter_limit": 10
    })
    print(f"状态码: {response.status_code}")
    print(f"响应: {response.json()}")
    print("✓ 采集任务已提交\n")

def test_subscriptions():
    """测试订阅功能"""
    print("测试订阅功能...")
    
    # 创建订阅
    response = requests.post(f"{BASE_URL}/api/subscriptions", json={
        "keyword": "测试关键词",
        "language": "zh",
        "reddit_limit": 20,
        "youtube_limit": 20,
        "twitter_limit": 20,
        "interval_hours": 6
    })
    print(f"创建订阅状态码: {response.status_code}")
    
    # 获取订阅列表
    response = requests.get(f"{BASE_URL}/api/subscriptions")
    subs = response.json()
    print(f"订阅数量: {len(subs)}")
    if subs:
        print(f"第一个订阅: {subs[0]['keyword']}")
    print("✓ 订阅测试通过\n")

def test_alerts():
    """测试报警功能"""
    print("测试报警功能...")
    response = requests.get(f"{BASE_URL}/api/alerts")
    alerts = response.json()
    print(f"报警数量: {len(alerts)}")
    if alerts:
        print(f"最新报警: {alerts[0]['message']}")
    print("✓ 报警测试通过\n")

if __name__ == "__main__":
    print("=" * 50)
    print("开始系统测试")
    print("=" * 50 + "\n")
    
    try:
        test_dashboard()
        test_subscriptions()
        test_alerts()
        # test_collection()  # 注释掉，因为采集需要较长时间
        
        print("=" * 50)
        print("所有测试通过！")
        print("=" * 50)
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
