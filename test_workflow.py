from collect import run_collection
from ai_analysis import run_analysis
import os

def test():
    print("🚀 开始测试采集流程 (关键词: DeepSeek, 限制: 1)...")
    try:
        # 使用极小的限制以快速测试
        run_collection("DeepSeek", language="en", reddit_limit=1, youtube_limit=1, twitter_limit=1)
        print("✅ 采集测试完成。")
    except Exception as e:
        print(f"⚠️ 采集测试遇到异常 (预期内可跳过): {e}")

    print("\n🚀 开始测试 AI 分析流程...")
    if os.path.exists("multi_source.db"):
        try:
            run_analysis()
            print("✅ AI 分析测试完成。")
        except Exception as e:
            print(f"❌ AI 分析测试失败: {e}")
    else:
        print("⚠️ 数据库不存在，跳过 AI 分析测试。")

if __name__ == "__main__":
    test()
