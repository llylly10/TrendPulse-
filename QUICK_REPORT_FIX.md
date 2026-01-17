# 分析报告隔离问题 - 快速修复

## 问题
1. 新关键词的源数据应该只显示新关键词的内容
2. 不同关键词的思维导图显示相同的观点

## 原因
所有关键词共用一个 `analysis_report.json` 文件，新分析会覆盖旧的

## 修复

### 1. ai_analysis.py - 按关键词保存报告
```python
# 之前：所有关键词用同一个文件
with open("analysis_report.json", "w") as f:
    json.dump(final_report, f)

# 现在：每个关键词独立文件
if keyword:
    report_file = f"analysis_report_{keyword}.json"
else:
    report_file = "analysis_report.json"

with open(report_file, "w") as f:
    json.dump(final_report, f)
```

### 2. api.py - 按关键词读取报告
```python
# 之前：总是读同一个文件
if os.path.exists(REPORT_FILE):
    with open(REPORT_FILE, "r") as f:
        report = json.load(f)

# 现在：根据关键词读取对应文件
if keyword:
    report_file = f"analysis_report_{keyword}.json"
else:
    report_file = REPORT_FILE

if os.path.exists(report_file):
    with open(report_file, "r") as f:
        report = json.load(f)
```

## 效果
- ✓ Python → `analysis_report_Python.json`
- ✓ JavaScript → `analysis_report_JavaScript.json`
- ✓ 每个关键词独立分析，不会覆盖
- ✓ 思维导图和观点完全匹配关键词

## 测试
```bash
python test_report_isolation.py
```

## 文件
- `ai_analysis.py` - 修改保存逻辑
- `api.py` - 修改读取逻辑
- `REPORT_ISOLATION_FIX.md` - 详细说明
