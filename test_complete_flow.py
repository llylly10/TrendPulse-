"""完整流程测试：创建订阅、等待执行、验证结果"""
import requests
import time
from datetime import datetime
import json

API_BASE = "http://localhost:8888/api"

def print_section(title):
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)

def check_api_health():
    try:
        response = requests.get(f"{API_BASE}/../")
        return response.status_code == 200
    except:
        return False

print_section("完整流程测试")

# 0. 检查 API 是否运行
print("\n0. 检查 API 状态...")
if not check_api_health():
    print("✗ API 未运行，请先启动后端：python -m uvicorn api:app --port 8888")
    exit(1)
print("✓ API 正常运行")

# 1. 清空现有订阅
print("\n1. 清理现有订阅...")
response = requests.get(f"{API_BASE}/subscriptions")
existing_subs = response.json()
for sub in existing_subs:
    requests.delete(f"{API_BASE}/subscriptions/{sub['id']}")
print(f"✓ 已清理 {len(existing_subs)} 个订阅")

# 2. 创建测试订阅（1分钟间隔）
print("\n2. 创建测试订阅（1分钟间隔）...")
response = requests.post(f"{API_BASE}/subscriptions", json={
    "keyword": "AI测试",
    "language": "zh",
    "reddit_limit": 5,
    "youtube_limit": 5,
    "twitter_limit": 5,
    "interval_seconds": 60
})

if response.status_code != 200:
    print(f"✗ 创建失败: {response.text}")
    exit(1)

print("✓ 订阅创建成功")

# 3. 查询订阅详情
print("\n3. 查询订阅详情...")
response = requests.get(f"{API_BASE}/subscriptions")
subs = response.json()

if not subs:
    print("✗ 未找到订阅")
    exit(1)

sub = subs[0]
print(f"  ID: {sub['id']}")
print(f"  关键词: {sub['keyword']}")
print(f"  间隔: {sub['interval_seconds']} 秒")
print(f"  last_run: {sub['last_run']}")
print(f"  next_run: {sub['next_run']}")
print(f"  当前时间: {int(time.time())}")

next_run_time = datetime.fromtimestamp(sub['next_run'])
now = datetime.now()
wait_seconds = (next_run_time - now).total_seconds()

print(f"  下次运行: {next_run_time}")
print(f"  需要等待: {max(0, wait_seconds):.0f} 秒")

# 4. 等待任务执行
print("\n4. 等待任务执行...")
print("   提示：后端每分钟检查一次")
print("   最多等待 150 秒")

last_run = sub['last_run']
max_wait = 150
waited = 0
check_interval = 5

while waited < max_wait:
    time.sleep(check_interval)
    waited += check_interval
    
    # 检查订阅状态
    response = requests.get(f"{API_BASE}/subscriptions")
    current_subs = response.json()
    
    if current_subs:
        current_sub = current_subs[0]
        
        # 检查任务状态
        try:
            status_response = requests.get(f"{API_BASE}/task-status")
            if status_response.status_code == 200:
                status = status_response.json()
                if status['is_running']:
                    print(f"  [{waited}s] 任务执行中: {status.get('progress', '...')}")
                    continue
        except:
            pass
        
        if current_sub['last_run'] != last_run and current_sub['last_run'] > 0:
            print(f"\n✓ 任务已执行！")
            print(f"  执行时间: {datetime.fromtimestamp(current_sub['last_run'])}")
            print(f"  下次运行: {datetime.fromtimestamp(current_sub['next_run'])}")
            
            # 5. 验证数据
            print("\n5. 验证数据更新...")
            time.sleep(2)  # 等待数据写入
            
            response = requests.get(f"{API_BASE}/dashboard")
            if response.status_code == 200:
                data = response.json()
                print(f"✓ 仪表盘数据已更新")
                print(f"  总帖子数: {data.get('total_posts', 0)}")
                print(f"  情感得分: {data.get('sentiment', {}).get('score', 0)}")
                print(f"  情感标签: {data.get('sentiment', {}).get('label', '')}")
            else:
                print("⚠️ 仪表盘暂无数据")
            
            # 6. 检查报警
            print("\n6. 检查报警...")
            response = requests.get(f"{API_BASE}/alerts")
            if response.status_code == 200:
                alerts = response.json()
                print(f"✓ 找到 {len(alerts)} 条报警")
                for alert in alerts[:3]:
                    print(f"  - {alert['message']}")
            
            break
    
    print(f"  [{waited}s] 等待中... (next_run: {datetime.fromtimestamp(current_sub['next_run'])})", end='\r')

if waited >= max_wait:
    print(f"\n⚠️ 超时：任务未在 {max_wait} 秒内执行")
    print("   可能原因：")
    print("   1. next_run 时间设置不正确")
    print("   2. 调度器未正常运行")
    print("   3. 任务执行时间过长")
    print("\n   请检查后端日志")

# 7. 清理
print("\n7. 清理测试数据...")
response = requests.delete(f"{API_BASE}/subscriptions/{sub['id']}")
if response.status_code == 200:
    print("✓ 测试订阅已删除")

print("\n测试完成！")
print("\n提示：")
print("  - 前端应该会自动刷新显示新数据")
print("  - 如果有负面舆情，会在通知图标显示")
print("  - 可以在前端查看完整的分析结果")
