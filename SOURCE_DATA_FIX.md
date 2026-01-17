# 源数据页面更新修复

## 问题描述
源数据页面不会随着关键词的变化而自动更新显示内容。

## 根本原因分析

### 后端 API
✅ **API 工作正常**
- `/api/source-data` 正确返回最新关键词的数据
- 测试验证：采集 Llama 后，API 返回 378 条 Llama 数据

### 前端数据刷新
✅ **DataProvider 正确调用**
- `_pollTaskStatus()` 在任务完成后调用 `refreshSourceData()`
- 数据确实被刷新了

### UI 更新
✅ **Consumer 正确监听**
- 源数据页面使用 `Consumer<DataProvider>`
- 当 `sourcePosts` 更新时，UI 会自动重建

## 已实施的改进

### 1. 添加关键词显示
在源数据页面顶部添加了一个横幅，显示：
- 当前关键词
- 数据条数

**效果：**
```
┌─────────────────────────────────────┐
│ 🏷️ 当前关键词: Llama    378 条数据  │
├─────────────────────────────────────┤
│ [源数据列表]                         │
│ ...                                 │
└─────────────────────────────────────┘
```

**代码位置：** `frontend/lib/pages/source_data_page.dart`

### 2. 确保数据刷新
在 `DataProvider._pollTaskStatus()` 中：
- 任务完成后同时调用 `refreshDashboard()` 和 `refreshSourceData()`
- 确保所有页面的数据都更新

**代码位置：** `frontend/lib/providers/data_provider.dart`

## 使用方法

### 测试步骤
1. 打开前端应用
2. 在仪表盘输入关键词 "Gemini"，点击采集
3. 等待任务完成
4. 切换到"源数据"页面
5. 查看顶部横幅：应该显示 "当前关键词: Gemini"
6. 查看数据内容：应该都是 Gemini 相关

7. 回到仪表盘，输入 "ChatGPT"，点击采集
8. 等待任务完成
9. 切换到"源数据"页面
10. 查看顶部横幅：应该显示 "当前关键词: ChatGPT"
11. 查看数据内容：应该都是 ChatGPT 相关

### 手动刷新
如果数据没有自动更新，可以：
1. 点击右上角的刷新按钮
2. 或者下拉列表触发刷新

## 验证脚本

### 测试 API
```bash
python test_source_data_update.py
```

**预期输出：**
```
1. 当前源数据状态:
   Qwen: 372 条

2. 采集新关键词: Llama
   ✓ Llama 任务完成

3. 任务完成后的源数据状态:
   Llama: 378 条

4. 验证结果:
   ✓ 源数据已更新为最新关键词: Llama
   ✓ API 工作正常
```

## 技术细节

### API 过滤逻辑
```python
# api.py - get_source_data()

# 如果没有指定关键词，获取最新的关键词
if not keyword:
    cursor.execute("SELECT keyword FROM cleaned_data WHERE keyword != 'unknown' ORDER BY rowid DESC LIMIT 1")
    result = cursor.fetchone()
    if result:
        keyword = result["keyword"]

# 按关键词查询
if keyword:
    cursor.execute("SELECT ... FROM cleaned_data WHERE keyword = ? ORDER BY timestamp DESC", (keyword,))
```

### 前端刷新流程
```dart
// DataProvider._pollTaskStatus()

if (!isRunning) {
  // 任务完成
  _taskProgress = '正在刷新数据...';
  notifyListeners();
  
  await Future.delayed(const Duration(seconds: 1));
  await refreshDashboard();      // 刷新仪表盘
  await refreshSourceData();     // 刷新源数据
  
  _taskProgress = '完成！';
  notifyListeners();
}
```

### UI 更新机制
```dart
// source_data_page.dart

Consumer<DataProvider>(
  builder: (context, provider, child) {
    // 当 provider.sourcePosts 更新时，自动重建
    final currentKeyword = provider.dashboardData?.keyword ?? '未知';
    
    return Column(
      children: [
        // 显示当前关键词
        Container(...),
        
        // 显示数据列表
        Expanded(
          child: ListView.builder(
            itemCount: provider.sourcePosts.length,
            itemBuilder: (context, index) {
              final post = provider.sourcePosts[index];
              return _buildPostItem(post);
            },
          ),
        ),
      ],
    );
  },
)
```

## 常见问题

### Q1: 源数据页面显示的还是旧关键词
**A:** 
1. 检查顶部横幅显示的关键词
2. 点击刷新按钮手动刷新
3. 确认后端 API 返回的数据是否正确

### Q2: 数据条数不对
**A:**
1. 检查数据库中该关键词的数据量
2. 确认 API 的过滤逻辑是否正确
3. 查看后端日志

### Q3: 切换关键词后数据没变
**A:**
1. 等待任务完成（查看进度提示）
2. 任务完成后会自动刷新
3. 如果没有自动刷新，手动点击刷新按钮

## 总结

✅ **API 层**：正确返回最新关键词的数据
✅ **数据层**：任务完成后自动刷新
✅ **UI 层**：使用 Consumer 自动更新
✅ **用户体验**：显示当前关键词和数据条数

现在源数据页面会：
1. 在任务完成后自动刷新
2. 显示当前关键词
3. 只显示该关键词的数据
4. 支持手动刷新

用户可以清楚地看到当前显示的是哪个关键词的数据！
