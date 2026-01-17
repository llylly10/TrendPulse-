# 分析报告隔离修复

## 问题描述

用户报告了两个问题：

1. **源数据显示问题**：新关键词采集后，源数据应该只显示新关键词的数据
2. **思维导图观点重复**：不同关键词的思维导图显示相同的观点

## 根本原因

### 问题 1：报告文件不隔离

**之前的实现：**
```python
# ai_analysis.py
def run_analysis(language: str = "zh", keyword: str = None):
    ...
    # 所有关键词都保存到同一个文件
    with open("analysis_report.json", "w", encoding="utf-8") as f:
        json.dump(final_report, f, ensure_ascii=False, indent=2)
```

**问题：**
- 所有关键词共用一个 `analysis_report.json` 文件
- 新关键词的分析会覆盖旧关键词的报告
- 导致仪表盘显示的分析结果不匹配当前关键词

### 问题 2：API 读取报告不验证关键词

**之前的实现：**
```python
# api.py
@app.get("/api/dashboard")
async def get_dashboard(keyword: str = None):
    ...
    # 总是读取同一个文件
    if os.path.exists(REPORT_FILE):
        with open(REPORT_FILE, "r", encoding="utf-8") as f:
            report = json.load(f)
```

**问题：**
- 即使数据库数据按关键词过滤了
- 但读取的报告可能是其他关键词的
- 导致数据和分析结果不匹配

## 解决方案

### 修复 1：按关键词保存报告文件

**ai_analysis.py**

```python
def run_analysis(language: str = "zh", keyword: str = None):
    ...
    # 按关键词保存到不同的文件
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
```

**效果：**
- 关键词 "Python" → `analysis_report_Python.json`
- 关键词 "JavaScript" → `analysis_report_JavaScript.json`
- 每个关键词有独立的分析报告
- 不会互相覆盖

### 修复 2：API 按关键词读取报告

**api.py**

```python
@app.get("/api/dashboard")
async def get_dashboard(keyword: str = None):
    ...
    # 按关键词读取对应的报告文件
    report = {}
    if keyword:
        report_file = f"analysis_report_{keyword}.json"
    else:
        report_file = REPORT_FILE
    
    if os.path.exists(report_file):
        try:
            with open(report_file, "r", encoding="utf-8") as f:
                report = json.load(f)
            logger.info(f"Dashboard: 读取报告文件 {report_file}")
        except Exception as e:
            logger.error(f"Error reading report file {report_file}: {e}")
    else:
        logger.warning(f"Dashboard: 报告文件 {report_file} 不存在")
```

**效果：**
- 查询关键词 "Python" → 读取 `analysis_report_Python.json`
- 查询关键词 "JavaScript" → 读取 `analysis_report_JavaScript.json`
- 确保数据和分析结果完全匹配

## 数据流程（修复后）

### 采集关键词 "Python"

```
1. 用户输入 "Python"
   ↓
2. 采集数据 → 保存到 cleaned_data (keyword = "Python")
   ↓
3. AI 分析
   - 只分析 keyword = "Python" 的数据
   - 生成报告保存到 analysis_report_Python.json
   ↓
4. 前端查询仪表盘
   - API 检测最新关键词 = "Python"
   - 读取 analysis_report_Python.json
   - 返回 Python 的分析结果
   ↓
5. 显示
   - 思维导图：A[Python] --> ...
   - 核心观点：关于 Python 的观点
   - AI 摘要：关于 Python 的摘要
```

### 采集关键词 "JavaScript"

```
1. 用户输入 "JavaScript"
   ↓
2. 采集数据 → 保存到 cleaned_data (keyword = "JavaScript")
   ↓
3. AI 分析
   - 只分析 keyword = "JavaScript" 的数据
   - 生成报告保存到 analysis_report_JavaScript.json
   - analysis_report_Python.json 仍然保留
   ↓
4. 前端查询仪表盘
   - API 检测最新关键词 = "JavaScript"
   - 读取 analysis_report_JavaScript.json
   - 返回 JavaScript 的分析结果
   ↓
5. 显示
   - 思维导图：A[JavaScript] --> ...
   - 核心观点：关于 JavaScript 的观点
   - AI 摘要：关于 JavaScript 的摘要
```

### 切换回 "Python"

```
1. 用户手动查询或切换到 Python
   ↓
2. 前端查询仪表盘 (keyword = "Python")
   ↓
3. API 读取 analysis_report_Python.json
   ↓
4. 返回之前保存的 Python 分析结果
   ↓
5. 显示 Python 的数据和分析
```

## 文件结构

修复后的文件结构：

```
项目根目录/
├── multi_source.db                    # 数据库（所有关键词的数据）
├── analysis_report.json               # 通用报告（最新关键词）
├── analysis_report_Python.json        # Python 的分析报告
├── analysis_report_JavaScript.json    # JavaScript 的分析报告
├── analysis_report_Gemini.json        # Gemini 的分析报告
└── ...
```

## 优点

1. **完全隔离**：每个关键词有独立的分析报告
2. **不会覆盖**：新关键词不会覆盖旧关键词的报告
3. **可以切换**：可以随时查看任何关键词的历史分析
4. **向后兼容**：仍然保存通用的 `analysis_report.json`

## 测试验证

运行测试脚本：

```bash
python test_report_isolation.py
```

测试流程：
1. 采集关键词 "Python"
2. 检查生成 `analysis_report_Python.json`
3. 采集关键词 "JavaScript"
4. 检查生成 `analysis_report_JavaScript.json`
5. 验证两个报告的内容不同
6. 验证思维导图根节点包含对应关键词

## 预期结果

✓ 每个关键词生成独立的报告文件
✓ 思维导图根节点匹配关键词
✓ 核心观点与关键词相关
✓ AI 摘要围绕关键词展开
✓ 源数据只显示当前关键词的数据

## 总结

通过按关键词保存和读取分析报告，彻底解决了报告混淆的问题。现在每个关键词都有完全独立的分析结果，不会互相干扰。
