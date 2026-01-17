"""测试关键词上下文是否正确传递到 AI 分析"""
import requests
import time
import json

API_BASE = "http://localhost:8888/api"

def print_section(title):
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)

print_section("测试关键词上下文")

# 清空旧数据
print("\n1. 清空旧数据...")
import subprocess
subprocess.run(["python", "clear_old_data.py"], check=False)

# 测试关键词：Claude
print("\n2. 测试关键词：Claude")
print("   启动采集任务...")
response = requests.post(f"{API_BASE}/collect", json={
    "keyword": "Claude",
    "language": "zh",
    "reddit_limit": 5,
    "youtube_limit": 5,
    "twitter_limit": 5
})

if response.status_code not in [200, 202]:
    print(f"✗ 启动失败: {response.text}")
    exit(1)

print("✓ Claude 采集任务已启动")

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
                print(f"\n✓ Claude 任务完成")
                break
            print(f"  [{waited}s] {status.get('progress', '...')}", end='\r')
    except:
        pass

if waited >= max_wait:
    print("\n⚠️ 超时")
    exit(1)

# 检查分析结果
print("\n3. 检查分析结果...")
time.sleep(2)

response = requests.get(f"{API_BASE}/dashboard")
if response.status_code == 200:
    data = response.json()
    
    print(f"\n✓ 仪表盘数据")
    print(f"  关键词: {data.get('keyword', 'N/A')}")
    print(f"  总帖子数: {data.get('total_posts', 0)}")
    
    # 检查思维导图
    mermaid = data.get('mermaid_graph', '')
    print(f"\n✓ 思维导图")
    print(f"  Mermaid 代码: {mermaid[:100]}...")
    
    if 'Claude' in mermaid:
        print(f"  ✓ 核心主题包含 'Claude'")
    else:
        print(f"  ✗ 核心主题不包含 'Claude'")
        print(f"  完整 Mermaid: {mermaid}")
    
    # 检查核心观点
    key_points = data.get('key_points', [])
    print(f"\n✓ 核心观点提取 ({len(key_points)} 条)")
    for i, point in enumerate(key_points, 1):
        print(f"  {i}. {point}")
        if 'Claude' in point or 'claude' in point.lower():
            print(f"     ✓ 包含关键词")
    
    # 检查摘要
    summary = data.get('summary', '')
    print(f"\n✓ AI 深度摘要")
    print(f"  {summary[:200]}...")
    if 'Claude' in summary or 'claude' in summary.lower():
        print(f"  ✓ 摘要包含关键词")
    else:
        print(f"  ✗ 摘要不包含关键词")
    
    # 检查节点情感
    node_sentiments = data.get('node_sentiments', {})
    print(f"\n✓ 节点情感标注 ({len(node_sentiments)} 个节点)")
    for node_id, sentiment in node_sentiments.items():
        print(f"  {node_id}: {sentiment}")
    
    # 总结
    print("\n" + "=" * 60)
    print("验证结果：")
    print("=" * 60)
    
    checks = {
        "关键词正确": data.get('keyword') == 'Claude',
        "思维导图包含关键词": 'Claude' in mermaid,
        "核心观点相关": any('Claude' in p or 'claude' in p.lower() for p in key_points) if key_points else False,
        "摘要相关": 'Claude' in summary or 'claude' in summary.lower(),
        "有节点情感标注": len(node_sentiments) > 0
    }
    
    for check, passed in checks.items():
        status = "✓" if passed else "✗"
        print(f"  {status} {check}")
    
    if all(checks.values()):
        print("\n🎉 所有检查通过！关键词上下文正确传递！")
    else:
        print("\n⚠️ 部分检查未通过，请查看详细信息")
else:
    print(f"✗ 获取数据失败: {response.status_code}")

print("\n测试完成！")
