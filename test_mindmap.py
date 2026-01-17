"""测试思维导图节点情感标注"""
import json

# 模拟测试 reduce_phase
from ai_analysis import reduce_phase

# 模拟 map 阶段的结果
test_map_results = [
    {
        "key_points": [
            "技术进展：DeepSeek 在 AI 领域取得突破",
            "质量改善：模型性能显著提升",
            "争议问题：数据隐私引发担忧",
        ]
    },
    {
        "key_points": [
            "成本优势：训练成本大幅降低",
            "安全风险：可能被滥用",
            "市场反应：投资者态度谨慎",
        ]
    }
]

print("=" * 60)
print("测试 AI 分析 - 节点情感标注")
print("=" * 60)

result = reduce_phase(test_map_results, language="zh")

if result:
    print("\n✓ AI 分析成功\n")
    print("争议点：")
    for i, point in enumerate(result.get("final_controversies", []), 1):
        print(f"  {i}. {point}")
    
    print(f"\n摘要：\n  {result.get('human_summary', '')[:100]}...")
    
    print(f"\nMermaid 图：\n  {result.get('mermaid_graph', '')}")
    
    print("\n节点情感标注：")
    node_sentiments = result.get("node_sentiments", {})
    if node_sentiments:
        for node_id, sentiment in node_sentiments.items():
            print(f"  {node_id}: {sentiment}")
    else:
        print("  ⚠️ 没有返回节点情感数据！")
    
    print("\n完整 JSON：")
    print(json.dumps(result, ensure_ascii=False, indent=2))
else:
    print("\n✗ AI 分析失败")

