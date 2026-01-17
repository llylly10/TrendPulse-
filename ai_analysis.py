import sqlite3
import os
import json
import tiktoken
from openai import OpenAI
from dotenv import load_dotenv
import pandas as pd
import numpy as np

# =========================
# 1. 初始化 & 配置
# =========================

load_dotenv()

DB_NAME = "multi_source.db"
MODEL = "gpt-5.2"  # 使用你们提供的模型

MAX_TOKENS_PER_BATCH = 4000
SAMPLE_SIZE = 100

# ✅ 关键修复：手动指定 tokenizer（与模型名解耦）
ENCODING = tiktoken.get_encoding("cl100k_base")

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_BASE_URL")
)

# =========================
# 2. 工具函数
# =========================

def get_token_count(text: str) -> int:
    """安全计算 token 数量（不依赖模型名）"""
    return len(ENCODING.encode(text))


def filter_dirty_data(df: pd.DataFrame) -> pd.DataFrame:
    """初步过滤脏数据"""
    initial_count = len(df)

    df = df[df["content"].notna()].copy()
    df = df[df["content"].str.len() > 10].copy()

    ad_keywords = [
        "加微信", "联系方式", "刷单", "兼职",
        "优惠券", "点我领取", "vx", "vx："
    ]
    for kw in ad_keywords:
        df = df[~df["content"].str.contains(kw, na=False)]

    print(f"🧹 脏数据过滤完成: {initial_count} -> {len(df)}")
    return df


# =========================
# 3. Map 阶段
# =========================

def map_phase(batches: list[str], language: str = "zh") -> list[dict]:
    map_results = []

    for i, batch in enumerate(batches):
        print(f"🧠 正在处理第 {i+1}/{len(batches)} 个批次...")

        if language == "en":
            prompt = f"""
You are a professional data analyst. Please analyze the following batch of social media comments.

Task:
1. Give an overall sentiment score (0-100)
2. Extract key points or controversies (max 5 items)
3. Determine if it contains obvious spam

Text to analyze:
\"\"\"
{batch}
\"\"\"

Please return ONLY valid JSON:
{{
  "sentiment_score": 75,
  "key_points": ["Point 1", "Point 2"],
  "spam_info": "None"
}}
"""
        else:
            prompt = f"""
你是一个专业的数据分析师，请分析以下社交媒体评论批次。

任务：
1. 给出整体情感得分（0-100）
2. 提取核心观点或争议点（最多 5 条）
3. 判断是否仍包含明显垃圾信息

待分析文本：
\"\"\"
{batch}
\"\"\"

请仅返回合法 JSON：
{{
  "sentiment_score": 75,
  "key_points": ["观点1", "观点2"],
  "spam_info": "无"
}}
"""

        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": "You are a professional data analysis assistant." if language == "en" else "你是一个专业的数据分析助手。"},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"}
            )

            result = json.loads(response.choices[0].message.content)
            map_results.append(result)

        except Exception as e:
            print(f"❌ 批次 {i+1} 处理失败: {e}")

    return map_results


# =========================
# 4. Reduce 阶段
# =========================

def reduce_phase(map_results: list[dict], language: str = "zh", keyword: str = None) -> dict | None:
    print(f"🔄 正在汇总最终分析结果 (关键词: {keyword or '未指定'})...")

    all_scores = []
    all_points = []

    for r in map_results:
        all_scores.append(r.get("sentiment_score", 50))
        all_points.extend(r.get("key_points", []))

    avg_sentiment = round(float(np.mean(all_scores)), 2)
    points_text = "\n".join(f"- {p}" for p in all_points)
    
    # 确定主题名称
    topic_name = keyword if keyword else "主题"

    if language == "en":
        prompt = f"""
You are a senior public opinion expert. Please complete the final summary based on the following points about "{topic_name}".

List of points:
\"\"\"
{points_text}
\"\"\"

Tasks:
1. Summarize 3 main controversies about {topic_name}
2. Generate a 150-200 word summary about {topic_name}
3. Generate a simple Mermaid.js mindmap (graph TD) with max 8 nodes, using "{topic_name}" as the root node
4. Label sentiment for each node

IMPORTANT for mermaid_graph:
- Root node MUST be: A[{topic_name}]
- Use simple node names (max 10 characters per node)
- Maximum 8 nodes total
- Use format: graph TD; A[{topic_name}] --> B[Point1]; A --> C[Point2]; B --> D[Detail];
- Keep it simple and clear

Node sentiment labeling:
- Judge sentiment for each node (except main topic)
- Return format: {{"NodeID": "positive/neutral/negative"}}
- Example: {{"B": "positive", "C": "negative", "D": "neutral"}}

Return ONLY valid JSON:
{{
  "final_controversies": ["Controversy 1", "Controversy 2", "Controversy 3"],
  "human_summary": "Summary content about {topic_name}",
  "mermaid_graph": "graph TD; A[{topic_name}] --> B[Point1]; A --> C[Point2];",
  "node_sentiments": {{"B": "positive", "C": "negative"}}
}}
"""
    else:
        prompt = f"""
你是高级舆情分析专家，请基于以下关于"{topic_name}"的观点完成最终汇总。

观点列表：
\"\"\"
{points_text}
\"\"\"

任务：
1. 总结 3 个关于 {topic_name} 的主要争议点
2. 生成一段 150-200 字关于 {topic_name} 的通俗摘要
3. 生成一个简洁的 Mermaid.js 思维导图（graph TD），最多 8 个节点，以"{topic_name}"作为根节点
4. 为每个节点标注情感倾向

思维导图要求：
- 根节点必须是：A[{topic_name}]
- 节点名称简短（每个节点最多 6 个汉字）
- 总共最多 8 个节点
- 格式：graph TD; A[{topic_name}] --> B[观点1]; A --> C[观点2]; B --> D[细节];
- 保持简洁清晰

节点情感标注：
- 为每个节点（除了主题节点）判断情感倾向
- 返回格式：{{"节点ID": "positive/neutral/negative"}}
- 例如：{{"B": "positive", "C": "negative", "D": "neutral"}}

仅返回合法 JSON：
{{
  "final_controversies": ["争议点1", "争议点2", "争议点3"],
  "human_summary": "关于{topic_name}的摘要内容",
  "mermaid_graph": "graph TD; A[{topic_name}] --> B[观点1]; A --> C[观点2];",
  "node_sentiments": {{"B": "positive", "C": "negative"}}
}}
"""

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": "You are a senior public opinion expert." if language == "en" else "你是一个高级舆情分析专家。"},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )

        final_result = json.loads(response.choices[0].message.content)
        final_result["avg_sentiment"] = avg_sentiment
        return final_result

    except Exception as e:
        print(f"❌ Reduce 阶段失败: {e}")
        return None


# =========================
# 5. 主流程
# =========================

def run_analysis(language: str = "zh", keyword: str = None):
    print(f"🚀 开始 AI 舆情分析流程 (语言: {language}, 关键词: {keyword or '全部'})...")

    if not os.getenv("OPENAI_API_KEY"):
        print("❌ 未检测到 OPENAI_API_KEY")
        return

    # 读取数据
    conn = sqlite3.connect(DB_NAME)
    if keyword:
        df = pd.read_sql_query("SELECT content FROM cleaned_data WHERE keyword = ?", conn, params=(keyword,))
    else:
        df = pd.read_sql_query("SELECT content FROM cleaned_data", conn)
    conn.close()

    if df.empty:
        print(f"⚠️ 数据库中没有可分析数据 (关键词: {keyword or '全部'})")
        return

    # 清洗
    df = filter_dirty_data(df)

    # 采样控制成本
    if len(df) > SAMPLE_SIZE:
        print(f"📉 数据量过大，采样 {SAMPLE_SIZE} 条")
        df = df.sample(SAMPLE_SIZE, random_state=42)

    # 分批
    batches = []
    current_batch = ""
    current_tokens = 0

    for text in df["content"].tolist():
        tokens = get_token_count(text)

        if current_tokens + tokens > MAX_TOKENS_PER_BATCH:
            batches.append(current_batch.strip())
            current_batch = text
            current_tokens = tokens
        else:
            current_batch += "\n" + text
            current_tokens += tokens

    if current_batch.strip():
        batches.append(current_batch.strip())

    print(f"📦 共生成 {len(batches)} 个批次")

    # Map
    map_results = map_phase(batches, language)
    if not map_results:
        print("❌ Map 阶段无结果")
        return

    # Reduce
    final_report = reduce_phase(map_results, language, keyword)
    if not final_report:
        return

    # 输出
    print("\n" + "=" * 50)
    print("📊 AI 舆情分析报告")
    print("=" * 50)
    print(f"关键词：{keyword or '全部'}")
    print(f"总体情感得分：{final_report['avg_sentiment']} / 100\n")

    print("🔥 三大核心争议点：")
    for i, p in enumerate(final_report["final_controversies"], 1):
        print(f"{i}. {p}")

    print("\n📝 人话摘要：")
    print(final_report["human_summary"])
    print("=" * 50)

    # 保存 - 按关键词保存到不同的文件
    if keyword:
        report_file = f"analysis_report_{keyword}.json"
    else:
        report_file = "analysis_report.json"
    
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(final_report, f, ensure_ascii=False, indent=2)

    print(f"✅ 已保存 {report_file}")
    
    # 同时保存到通用文件（向后兼容）
    with open("analysis_report.json", "w", encoding="utf-8") as f:
        json.dump(final_report, f, ensure_ascii=False, indent=2)
    
    return final_report


if __name__ == "__main__":
    run_analysis()
