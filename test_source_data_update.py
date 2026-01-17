"""测试源数据是否正确更新"""
import requests
import time

API_BASE = "http://localhost:8888/api"

def check_source_data():
    response = requests.get(f"{API_BASE}/source-data")
    if response.status_code == 200:
        data = response.json()
        if data:
            keywords = {}
            for post in data:
                kw = post.get('keyword', 'unknown')
                keywords[kw] = keywords.get(kw, 0) + 1
            
            print(f"源数据 API 返回: {len(data)} 条")
            print(f"关键词分布:")
            for kw, count in sorted(keywords.items(), key=lambda x: -x[1]):
                print(f"  {kw}: {count} 条")
            
            # 返回最多的关键词
            if keywords:
                return max(keywords.items(), key=lambda x: x[1])[0]
        else:
            print("源数据为空")
            return None
    else:
        print(f"API 错误: {response.status_code}")
        return None

print("=" * 60)
print("测试源数据更新")
print("=" * 60)

print("\n1. 当前源数据状态:")
current_keyword = check_source_data()

print(f"\n2. 采集新关键词: Llama")
response = requests.post(f"{API_BASE}/collect", json={
    "keyword": "Llama",
    "language": "en",
    "reddit_limit": 3,
    "youtube_limit": 3,
    "twitter_limit": 3
})

if response.status_code not in [200, 202]:
    print(f"✗ 启动失败: {response.text}")
    exit(1)

print("✓ Llama 采集任务已启动")

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
                print(f"\n✓ Llama 任务完成")
                break
            print(f"  [{waited}s] {status.get('progress', '...')}", end='\r')
    except:
        pass

if waited >= max_wait:
    print("\n⚠️ 超时")
    exit(1)

print("\n3. 任务完成后的源数据状态:")
time.sleep(2)
new_keyword = check_source_data()

print("\n4. 验证结果:")
if new_keyword == 'Llama':
    print(f"✓ 源数据已更新为最新关键词: {new_keyword}")
    print(f"✓ API 工作正常")
else:
    print(f"✗ 源数据未更新")
    print(f"  期望: Llama")
    print(f"  实际: {new_keyword}")
    print(f"  可能原因：")
    print(f"    1. API 的最新关键词逻辑有问题")
    print(f"    2. 数据库查询顺序不正确")

print("\n5. 测试前端是否能看到更新:")
print("   请在浏览器中：")
print("   1. 打开源数据页面")
print("   2. 点击刷新按钮")
print("   3. 检查显示的数据是否都是 Llama 相关")
print("   4. 如果不是，说明前端有缓存问题")

print("\n测试完成！")
