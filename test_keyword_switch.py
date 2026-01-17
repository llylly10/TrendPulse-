#!/usr/bin/env python3
"""
测试关键词切换后前端数据更新
模拟用户操作流程：
1. 采集关键词A的数据
2. 查看仪表盘和源数据
3. 采集关键词B的数据
4. 再次查看仪表盘和源数据，验证数据已更新
"""

import requests
import json
import time

API_BASE = "http://localhost:8888/api"

def wait_for_task_completion(timeout=120):
    """等待任务完成"""
    print("   等待任务完成...", end="", flush=True)
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            response = requests.get(f"{API_BASE}/task-status")
            if response.status_code == 200:
                status = response.json()
                if not status.get("is_running", False):
                    print(" ✓ 完成")
                    return True
                print(".", end="", flush=True)
        except:
            pass
        time.sleep(3)
    print(" ✗ 超时")
    return False

def check_data(expected_keyword):
    """检查仪表盘和源数据是否匹配预期关键词"""
    print(f"\n   检查数据是否为关键词: {expected_keyword}")
    
    # 检查仪表盘
    response = requests.get(f"{API_BASE}/dashboard")
    if response.status_code == 200:
        dashboard = response.json()
        keyword = dashboard.get("keyword", "")
        total = dashboard.get("total_posts", 0)
        print(f"   仪表盘 - 关键词: {keyword}, 数据量: {total}")
        
        if keyword != expected_keyword:
            print(f"   ✗ 仪表盘关键词不匹配！期望: {expected_keyword}, 实际: {keyword}")
            return False
    else:
        print(f"   ✗ 获取仪表盘失败")
        return False
    
    # 检查源数据
    response = requests.get(f"{API_BASE}/source-data")
    if response.status_code == 200:
        posts = response.json()
        print(f"   源数据 - 数据量: {len(posts)}")
        
        if posts:
            # 检查前5条数据的关键词
            keywords = set()
            for post in posts[:5]:
                keywords.add(post.get("keyword", ""))
            
            print(f"   源数据 - 关键词: {keywords}")
            
            if expected_keyword not in keywords or len(keywords) > 1:
                print(f"   ✗ 源数据关键词不匹配！期望: {expected_keyword}, 实际: {keywords}")
                return False
        else:
            print(f"   ✗ 源数据为空")
            return False
    else:
        print(f"   ✗ 获取源数据失败")
        return False
    
    print(f"   ✓ 数据验证通过")
    return True

def main():
    print("=" * 60)
    print("测试关键词切换后数据更新")
    print("=" * 60)
    
    # 测试关键词
    keyword1 = "Python"
    keyword2 = "JavaScript"
    
    # 1. 采集第一个关键词
    print(f"\n1. 采集关键词: {keyword1}")
    try:
        response = requests.post(
            f"{API_BASE}/collect",
            json={
                "keyword": keyword1,
                "language": "zh",
                "reddit_limit": 5,
                "youtube_limit": 5,
                "twitter_limit": 5
            }
        )
        if response.status_code in [200, 202]:
            print(f"   ✓ 任务已启动")
            if not wait_for_task_completion():
                print("   ✗ 任务超时")
                return
        else:
            print(f"   ✗ 启动失败: {response.status_code}")
            return
    except Exception as e:
        print(f"   ✗ 请求失败: {e}")
        return
    
    # 2. 检查第一个关键词的数据
    print(f"\n2. 验证关键词 {keyword1} 的数据")
    if not check_data(keyword1):
        print("   ✗ 第一次数据验证失败")
        return
    
    # 等待一下
    print("\n   等待3秒...")
    time.sleep(3)
    
    # 3. 采集第二个关键词
    print(f"\n3. 采集关键词: {keyword2}")
    try:
        response = requests.post(
            f"{API_BASE}/collect",
            json={
                "keyword": keyword2,
                "language": "zh",
                "reddit_limit": 5,
                "youtube_limit": 5,
                "twitter_limit": 5
            }
        )
        if response.status_code in [200, 202]:
            print(f"   ✓ 任务已启动")
            if not wait_for_task_completion():
                print("   ✗ 任务超时")
                return
        else:
            print(f"   ✗ 启动失败: {response.status_code}")
            return
    except Exception as e:
        print(f"   ✗ 请求失败: {e}")
        return
    
    # 4. 检查第二个关键词的数据
    print(f"\n4. 验证关键词 {keyword2} 的数据")
    if not check_data(keyword2):
        print("   ✗ 第二次数据验证失败")
        print("\n   ⚠️  这说明数据没有正确更新！")
        print("   前端需要在切换到源数据页面时重新获取数据")
        return
    
    print("\n" + "=" * 60)
    print("✓ 测试通过！关键词切换后数据正确更新")
    print("=" * 60)
    print("\n前端使用说明：")
    print("1. 在仪表盘页面启动采集任务")
    print("2. 等待任务完成（会显示进度提示）")
    print("3. 切换到源数据页面，数据会自动刷新")
    print("4. 切换回仪表盘，数据也会自动刷新")

if __name__ == "__main__":
    main()
