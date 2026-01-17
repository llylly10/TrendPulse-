#!/usr/bin/env python3
"""
测试分析报告按关键词隔离
验证不同关键词生成不同的分析报告
"""

import requests
import json
import time
import os

API_BASE = "http://localhost:8888/api"

def wait_for_task(timeout=120):
    """等待任务完成"""
    print("   等待任务完成...", end="", flush=True)
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            response = requests.get(f"{API_BASE}/task-status")
            if response.status_code == 200:
                status = response.json()
                if not status.get("is_running", False):
                    print(" ✓")
                    return True
                print(".", end="", flush=True)
        except:
            pass
        time.sleep(3)
    print(" ✗ 超时")
    return False

def collect_keyword(keyword):
    """采集指定关键词的数据"""
    print(f"\n{'='*60}")
    print(f"采集关键词: {keyword}")
    print('='*60)
    
    response = requests.post(
        f"{API_BASE}/collect",
        json={
            "keyword": keyword,
            "language": "zh",
            "reddit_limit": 5,
            "youtube_limit": 5,
            "twitter_limit": 5
        }
    )
    
    if response.status_code in [200, 202]:
        print(f"✓ 任务已启动")
        return wait_for_task()
    else:
        print(f"✗ 启动失败: {response.status_code}")
        return False

def check_dashboard(keyword):
    """检查仪表盘数据"""
    print(f"\n检查仪表盘数据...")
    response = requests.get(f"{API_BASE}/dashboard")
    
    if response.status_code == 200:
        data = response.json()
        print(f"  关键词: {data.get('keyword', 'N/A')}")
        print(f"  数据量: {data.get('total_posts', 0)}")
        print(f"  情感得分: {data.get('sentiment', {}).get('score', 0)}")
        
        # 显示核心观点
        key_points = data.get('key_points', [])
        print(f"  核心观点数量: {len(key_points)}")
        if key_points:
            print("  核心观点:")
            for i, point in enumerate(key_points[:3], 1):
                print(f"    {i}. {point[:60]}...")
        
        # 显示思维导图
        mermaid = data.get('mermaid_graph', '')
        if mermaid:
            # 提取第一行（根节点）
            first_line = mermaid.split('\n')[0] if '\n' in mermaid else mermaid
            print(f"  思维导图根节点: {first_line}")
        
        return data
    else:
        print(f"✗ 获取失败: {response.status_code}")
        return None

def check_report_files():
    """检查生成的报告文件"""
    print(f"\n检查报告文件...")
    
    # 查找所有 analysis_report_*.json 文件
    import glob
    report_files = glob.glob("analysis_report_*.json")
    
    print(f"  找到 {len(report_files)} 个报告文件:")
    for file in report_files:
        print(f"    - {file}")
        
        # 读取并显示关键信息
        try:
            with open(file, 'r', encoding='utf-8') as f:
                report = json.load(f)
                controversies = report.get('final_controversies', [])
                print(f"      争议点数量: {len(controversies)}")
                if controversies:
                    print(f"      第一个争议点: {controversies[0][:50]}...")
        except Exception as e:
            print(f"      读取失败: {e}")

def main():
    print("="*60)
    print("测试分析报告按关键词隔离")
    print("="*60)
    
    keywords = ["Python", "JavaScript"]
    results = {}
    
    for keyword in keywords:
        if collect_keyword(keyword):
            time.sleep(2)  # 等待文件写入
            data = check_dashboard(keyword)
            if data:
                results[keyword] = data
        else:
            print(f"✗ {keyword} 采集失败")
    
    # 检查报告文件
    check_report_files()
    
    # 对比结果
    print(f"\n{'='*60}")
    print("对比分析结果")
    print('='*60)
    
    if len(results) == 2:
        kw1, kw2 = keywords
        
        # 对比关键词
        print(f"\n1. 关键词对比:")
        print(f"   {kw1}: {results[kw1].get('keyword', 'N/A')}")
        print(f"   {kw2}: {results[kw2].get('keyword', 'N/A')}")
        
        # 对比核心观点
        print(f"\n2. 核心观点对比:")
        points1 = results[kw1].get('key_points', [])
        points2 = results[kw2].get('key_points', [])
        
        print(f"   {kw1} 的观点:")
        for i, p in enumerate(points1[:2], 1):
            print(f"     {i}. {p[:50]}...")
        
        print(f"   {kw2} 的观点:")
        for i, p in enumerate(points2[:2], 1):
            print(f"     {i}. {p[:50]}...")
        
        # 检查是否相同
        if points1 == points2:
            print("\n   ⚠️  警告：两个关键词的核心观点完全相同！")
            print("   这说明报告没有正确隔离。")
        else:
            print("\n   ✓ 核心观点不同，报告正确隔离")
        
        # 对比思维导图
        print(f"\n3. 思维导图对比:")
        graph1 = results[kw1].get('mermaid_graph', '')
        graph2 = results[kw2].get('mermaid_graph', '')
        
        if graph1 and graph2:
            line1 = graph1.split('\n')[0] if '\n' in graph1 else graph1
            line2 = graph2.split('\n')[0] if '\n' in graph2 else graph2
            
            print(f"   {kw1}: {line1}")
            print(f"   {kw2}: {line2}")
            
            if kw1 in line1 and kw2 in line2:
                print("\n   ✓ 思维导图根节点正确包含关键词")
            else:
                print("\n   ⚠️  警告：思维导图根节点未包含关键词")
    
    print(f"\n{'='*60}")
    print("测试完成")
    print('='*60)

if __name__ == "__main__":
    main()
