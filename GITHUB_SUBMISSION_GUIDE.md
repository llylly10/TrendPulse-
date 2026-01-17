# GitHub 提交指南

## 🚫 不应该提交的文件 (已在 .gitignore 中)

### 🔐 敏感信息
- `.env` - **绝对不能提交！** 包含 API Key
- `*.db` - 数据库文件 (包含用户数据)
- `analysis_report_*.json` - 分析报告 (包含采集的数据)

### 🐍 Python 环境
- `__pycache__/` - Python 缓存
- `venv/`, `Lib/`, `Scripts/` - 虚拟环境
- `pyvenv.cfg` - 虚拟环境配置

### 📱 Flutter 构建文件
- `frontend/build/` - 构建输出
- `frontend/.dart_tool/` - Dart 工具缓存
- `frontend/.flutter-plugins*` - Flutter 插件缓存

### 🧪 测试和调试文件
- `test_*.py` - 测试脚本 (可选择性保留)
- `check_*.py` - 检查脚本
- `debug_*.py` - 调试脚本
- `*.log` - 日志文件

### 🔧 临时文件
- `.lock` - 锁文件
- `CACHEDIR.TAG` - 缓存标记
- `*.tmp`, `*.temp` - 临时文件

## ✅ 应该提交的核心文件

### 📋 项目文档
```
README.md                    # 项目主文档 ⭐
TECHNICAL.md                 # 技术文档 ⭐
ANTI_SCRAPING.md            # 反爬文档 ⭐
requirements.txt            # Python 依赖 ⭐
.gitignore                  # Git 忽略文件 ⭐
```

### 🐍 Python 核心代码
```
api.py                      # FastAPI 后端 ⭐
collect.py                  # 数据采集 ⭐
data_cleaning.py            # 数据清洗 ⭐
ai_analysis.py              # AI 分析 ⭐
run_all.py                  # 启动脚本 ⭐
```

### 📱 Flutter 前端
```
frontend/lib/               # Flutter 源码 ⭐
frontend/pubspec.yaml       # Flutter 依赖 ⭐
frontend/web/               # Web 配置 ⭐
frontend/test/              # 测试文件 ⭐
```

### 🔧 工具脚本
```
migrate_add_keyword.py      # 数据库迁移
migrate_subscriptions.py    # 订阅迁移
clear_data.py              # 数据清理
show_schema.py             # 数据库结构
```

## 📝 可选提交的文件

### 📚 详细文档 (可选)
```
FIXES_SUMMARY.md           # 修复总结
DATA_ISOLATION_BUG_FIX.md  # Bug 修复文档
SOURCE_DATA_UPDATE_FIX.md  # 更新修复文档
USER_GUIDE_FINAL.md        # 用户指南
```

### 🧪 测试脚本 (可选)
```
test_keyword_isolation.py  # 关键词隔离测试
test_complete_flow.py      # 完整流程测试
test_system.py             # 系统测试
```

### 🕷️ 备选爬虫 (可选)
```
twitter_scraper_selenium.py # Selenium 爬虫
twitter_scraper_enhanced.py # 增强爬虫
```

## 🚀 提交前检查清单

### 1. 创建 .env.example 文件
```bash
# 创建环境变量示例文件
cp .env .env.example
# 编辑 .env.example，移除真实的 API Key
```

`.env.example` 内容：
```env
OPENAI_API_KEY=your_api_key_here
OPENAI_BASE_URL=https://api.openai.com/v1
```

### 2. 清理敏感数据
```bash
# 删除数据库文件
rm *.db

# 删除分析报告
rm analysis_report*.json

# 删除日志文件
rm *.log
```

### 3. 测试环境
```bash
# 创建新的虚拟环境测试
python -m venv test_env
source test_env/bin/activate  # Linux/Mac
# 或 test_env\Scripts\activate  # Windows

pip install -r requirements.txt
python api.py  # 测试是否能正常启动
```

### 4. 更新 README.md
确保 README.md 中的安装步骤是正确的。

## 📂 推荐的项目结构 (提交后)

```
sentiment-analysis-system/
├── README.md                    # 项目介绍
├── TECHNICAL.md                 # 技术文档
├── ANTI_SCRAPING.md            # 反爬策略
├── requirements.txt            # Python 依赖
├── .gitignore                  # Git 忽略
├── .env.example                # 环境变量示例
│
├── api.py                      # FastAPI 后端
├── collect.py                  # 数据采集
├── data_cleaning.py            # 数据清洗
├── ai_analysis.py              # AI 分析
├── run_all.py                  # 启动脚本
│
├── migrate_add_keyword.py      # 数据库迁移
├── migrate_subscriptions.py    # 订阅迁移
├── clear_data.py              # 数据清理
├── show_schema.py             # 数据库结构
│
├── frontend/                   # Flutter 前端
│   ├── lib/                   # 源码
│   ├── pubspec.yaml           # 依赖
│   ├── web/                   # Web 配置
│   └── test/                  # 测试
│
├── docs/                      # 文档目录 (可选)
│   ├── FIXES_SUMMARY.md
│   ├── USER_GUIDE_FINAL.md
│   └── ...
│
└── tests/                     # 测试目录 (可选)
    ├── test_keyword_isolation.py
    ├── test_complete_flow.py
    └── ...
```

## 🎯 Git 提交命令

```bash
# 1. 初始化 Git 仓库
git init

# 2. 添加所有文件 (.gitignore 会自动过滤)
git add .

# 3. 查看将要提交的文件
git status

# 4. 提交
git commit -m "Initial commit: Multi-source sentiment analysis system"

# 5. 添加远程仓库
git remote add origin https://github.com/yourusername/sentiment-analysis-system.git

# 6. 推送到 GitHub
git push -u origin main
```

## ⚠️ 重要提醒

1. **绝对不要提交 .env 文件** - 包含 API Key
2. **不要提交数据库文件** - 可能包含敏感数据
3. **不要提交虚拟环境** - 文件太多且不必要
4. **检查 .gitignore** - 确保敏感文件被忽略
5. **创建 .env.example** - 让其他人知道需要什么环境变量

## 📊 文件大小建议

- 单个文件 < 100MB
- 总项目大小 < 1GB
- 如果有大文件，考虑使用 Git LFS

按照这个指南，你的项目就可以安全地提交到 GitHub 了！