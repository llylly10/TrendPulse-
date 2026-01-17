"""创建测试数据用于验证思维导图"""
import json

# 创建模拟的分析报告
test_report = {
    "avg_sentiment": 55.5,
    "final_controversies": [
        "技术突破引发行业关注",
        "数据隐私问题引发担忧",
        "成本优势带来竞争力"
    ],
    "human_summary": "DeepSeek 在 AI 领域取得重大突破，模型性能显著提升且成本大幅降低。然而，数据隐私和安全问题引发了广泛担忧。市场反应积极但投资者态度谨慎。",
    "mermaid_graph": "graph TD; A[DeepSeek] --> B[技术进展]; A --> C[质量改善]; A --> D[隐私担忧]; A --> E[成本优势]; A --> F[安全风险]; A --> G[市场反应];",
    "node_sentiments": {
        "B": "positive",
        "C": "positive",
        "D": "negative",
        "E": "positive",
        "F": "negative",
        "G": "neutral"
    }
}

# 保存到文件
with open("analysis_report.json", "w", encoding="utf-8") as f:
    json.dump(test_report, f, ensure_ascii=False, indent=2)

print("✓ 测试数据已创建：analysis_report.json")
print("\n节点情感分布：")
print("  正面：技术进展、质量改善、成本优势")
print("  负面：隐私担忧、安全风险")
print("  中性：市场反应")
