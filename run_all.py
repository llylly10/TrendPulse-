import sys
import os
import traceback
from collect import run_collection
from ai_analysis import run_analysis

def get_input(prompt, default):
    try:
        user_input = input(f"{prompt} (默认: {default}): ").strip()
        return user_input if user_input else default
    except EOFError:
        return default

def main():
    print("\n" + "="*50)
    print("   🌐 舆情分析系统 - 全流程启动器 🌐")
    print("="*50 + "\n")
    print("💡 提示: 请确保已使用 'uv pip install -r requirements.txt' 安装依赖")

    # 1. 获取用户输入
    keyword = get_input("🔍 请输入查询关键词", "DeepSeek")
    
    print("\n🌐 请选择搜索语言:")
    print("   1. 英文 (en)")
    print("   2. 中文 (zh)")
    lang_choice = get_input("👉 请输入选择 (1/2)", "1")
    language = "en" if lang_choice == "1" else "zh"

    print("\n📊 请输入各平台抓取条数限制 (输入数字):")
    while True:
        try:
            reddit_limit = int(get_input("   - Reddit 限制", "30"))
            youtube_limit = int(get_input("   - YouTube 限制", "30"))
            twitter_limit = int(get_input("   - Twitter 限制", "30"))
            break
        except ValueError:
            print("❌ 请输入有效的数字！")

    print("\n" + "-"*50)
    print(f"🚀 任务配置确认:")
    print(f"   - 关键词: {keyword}")
    print(f"   - 语  言: {'中文' if language == 'zh' else '英文'}")
    print(f"   - 限  制: Reddit({reddit_limit}), YouTube({youtube_limit}), Twitter({twitter_limit})")
    print("-"*50 + "\n")

    # 2. 执行采集与清洗
    print("📡 正在启动多源数据采集...")
    try:
        run_collection(keyword, language, reddit_limit, youtube_limit, twitter_limit)
    except Exception as e:
        print(f"⚠️ 采集阶段遇到异常 (已跳过): {e}")
        # 根据用户要求，遇到无法解决的异常如连接超时就跳过
        # 这里我们继续执行后续分析，如果采集到了部分数据的话

    # 3. 执行 AI 分析
    print("\n🧠 正在启动 AI 舆情分析...")
    try:
        run_analysis(language=language)
    except Exception as e:
        print(f"❌ AI 分析阶段出错: {e}")
        # traceback.print_exc()

    print("\n" + "="*50)
    print("✅ 所有流程已完成！")
    print("📄 请查看 analysis_report.json 获取最终报告。")
    print("="*50 + "\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 用户取消操作，程序退出。")
        sys.exit(0)
