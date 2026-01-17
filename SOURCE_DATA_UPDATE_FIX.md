# 源数据页面更新问题修复

## 问题描述

用户报告：源数据页面的内容不会随着关键词的变化而更新。

具体表现：
1. 在仪表盘页面采集新关键词的数据
2. 任务完成后，仪表盘显示新关键词的数据
3. 切换到源数据页面，仍然显示旧关键词的数据
4. 需要手动点击刷新按钮才能看到新数据

## 根本原因

### 1. 页面缓存问题

原来的 `MainNavigation` 实现：
```dart
class _MainNavigationState extends State<MainNavigation> {
  int _selectedIndex = 0;
  final List<Widget> _pages = [
    DashboardPage(),
    SourceDataPage(),
    SubscriptionPage(),
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: _pages[_selectedIndex],
      ...
    );
  }
}
```

问题：
- 三个页面在 `_pages` 列表中被创建一次后就一直保存在内存中
- 切换标签页时，只是改变显示哪个页面，不会重新创建页面
- `SourceDataPage` 的 `initState()` 只在页面首次创建时调用一次
- 后续切换到源数据页面时，不会触发数据刷新

### 2. 数据流程

正确的数据流程应该是：
1. 用户在仪表盘启动采集任务（关键词：Gemini）
2. 后台任务完成，数据保存到数据库（keyword = "Gemini"）
3. `DataProvider._pollTaskStatus()` 检测到任务完成
4. 调用 `refreshDashboard()` 和 `refreshSourceData()`
5. 更新 `_dashboardData` 和 `_sourcePosts`
6. 调用 `notifyListeners()` 通知所有监听者
7. **问题**：如果用户还在仪表盘页面，源数据页面不会重新构建
8. 用户切换到源数据页面，看到的是旧数据（因为页面没有重新加载）

## 解决方案

### 修改 1: 动态创建页面

修改 `main.dart` 中的 `_MainNavigationState`：

```dart
class _MainNavigationState extends State<MainNavigation> {
  int _selectedIndex = 0;
  
  // 创建页面实例的方法，每次切换都会调用
  Widget _getPage(int index) {
    switch (index) {
      case 0:
        return DashboardPage();
      case 1:
        return SourceDataPage();
      case 2:
        return SubscriptionPage();
      default:
        return DashboardPage();
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: _getPage(_selectedIndex), // 每次切换都重新创建页面
      ...
    );
  }
}
```

优点：
- 每次切换标签页时，都会重新创建页面实例
- 页面的 `initState()` 会被调用
- 自动触发数据刷新
- 简单直接，不需要额外的状态管理

缺点：
- 页面状态不会保留（例如滚动位置）
- 对于这个应用来说，这不是问题，因为我们希望每次都显示最新数据

### 修改 2: 保持源数据页面简洁

`source_data_page.dart` 保持原有的简单实现：

```dart
class _SourceDataPageState extends State<SourceDataPage> {
  @override
  void initState() {
    super.initState();
    // 页面加载时刷新数据
    Future.microtask(() =>
        Provider.of<DataProvider>(context, listen: false).refreshSourceData());
  }
  
  @override
  Widget build(BuildContext context) {
    return Consumer<DataProvider>(
      builder: (context, provider, child) {
        // 使用 provider.sourcePosts 显示数据
        ...
      },
    );
  }
}
```

## 数据流程（修复后）

1. 用户在仪表盘启动采集任务（关键词：Gemini）
2. 后台任务完成，数据保存到数据库（keyword = "Gemini"）
3. `DataProvider._pollTaskStatus()` 检测到任务完成
4. 调用 `refreshDashboard()` 和 `refreshSourceData()`
5. 更新 `_dashboardData` 和 `_sourcePosts`
6. 调用 `notifyListeners()` 通知所有监听者
7. 仪表盘页面（如果可见）自动更新显示
8. **修复**：用户切换到源数据页面时
9. `_getPage(1)` 创建新的 `SourceDataPage` 实例
10. `initState()` 被调用
11. 调用 `refreshSourceData()` 获取最新数据
12. 后端 API 自动返回最新关键词的数据
13. 页面显示正确的数据

## 后端 API 验证

后端 `/api/source-data` 端点已经正确实现了关键词过滤：

```python
@app.get("/api/source-data")
async def get_source_data(keyword: str = None):
    # 如果没有指定关键词，获取最新的关键词
    if not keyword:
        cursor.execute("SELECT keyword FROM cleaned_data WHERE keyword != 'unknown' ORDER BY rowid DESC LIMIT 1")
        result = cursor.fetchone()
        if result:
            keyword = result["keyword"]
    
    # 按关键词查询
    if keyword:
        cursor.execute("SELECT * FROM cleaned_data WHERE keyword = ? ORDER BY timestamp DESC", (keyword,))
    ...
```

这确保了每次调用 API 时，都会返回最新关键词的数据。

## 测试验证

运行测试脚本验证修复：

```bash
python test_keyword_switch.py
```

测试流程：
1. 采集关键词 "Python" 的数据
2. 验证仪表盘和源数据都显示 "Python"
3. 采集关键词 "JavaScript" 的数据
4. 验证仪表盘和源数据都更新为 "JavaScript"

## 用户操作指南

修复后的正确使用流程：

1. **启动采集任务**
   - 在仪表盘页面点击"新建采集任务"
   - 输入关键词（例如：Gemini）
   - 点击"开始采集"

2. **等待任务完成**
   - 页面底部会显示进度提示
   - "任务启动中..." → "数据采集中..." → "正在刷新数据..." → "完成！"

3. **查看数据**
   - 仪表盘会自动刷新，显示新关键词的分析结果
   - 切换到"源数据"标签页
   - 页面会自动加载最新关键词的数据
   - 顶部横幅显示当前关键词和数据量

4. **切换关键词**
   - 返回仪表盘，启动新的采集任务（例如：ChatGPT）
   - 等待任务完成
   - 切换到源数据页面，自动显示新关键词的数据

## 总结

通过修改页面创建方式，从"缓存页面实例"改为"动态创建页面"，解决了源数据页面不更新的问题。这个方案简单有效，符合应用的使用场景，确保用户每次切换到源数据页面时都能看到最新的数据。
