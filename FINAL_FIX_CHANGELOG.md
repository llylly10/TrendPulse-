# 源数据页面更新问题 - 完整修复记录

## 日期
2026-01-16

## 问题报告
用户反馈：源数据页面的内容不会随着关键词的变化而更新

## 问题分析

### 症状
1. 在仪表盘采集新关键词（例如从 DeepSeek 改为 Gemini）
2. 任务完成后，仪表盘显示新关键词的数据
3. 切换到源数据页面，仍然显示旧关键词的数据
4. 需要手动点击刷新按钮才能看到新数据

### 根本原因
前端使用了页面缓存机制：
- `MainNavigation` 组件在初始化时创建了所有页面实例
- 这些实例保存在 `_pages` 列表中
- 切换标签时只是改变显示哪个页面，不会重新创建页面
- `SourceDataPage` 的 `initState()` 只在首次创建时调用
- 后续切换到该页面时不会触发数据刷新

### 后端验证
通过测试确认后端 API 工作正常：
- `/api/dashboard` 正确返回最新关键词的数据
- `/api/source-data` 自动检测并返回最新关键词的数据
- 数据库中的数据正确按关键词隔离

问题确实出在前端的页面刷新机制。

## 修复方案

### 修改文件 1: `frontend/lib/main.dart`

**修改前：**
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

**修改后：**
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

**改动说明：**
- 移除了 `_pages` 列表
- 添加了 `_getPage()` 方法，根据索引动态创建页面
- 每次 `setState()` 触发重建时，都会调用 `_getPage()` 创建新的页面实例
- 新页面实例的 `initState()` 会被调用，触发数据刷新

### 修改文件 2: `frontend/lib/pages/source_data_page.dart`

**保持不变，但确认逻辑正确：**
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

**逻辑说明：**
- `initState()` 在页面创建时调用 `refreshSourceData()`
- `refreshSourceData()` 调用 `/api/source-data` 获取最新数据
- 后端自动返回最新关键词的数据
- `Consumer<DataProvider>` 监听数据变化并自动重建 UI

## 数据流程（修复后）

### 场景：用户采集新关键词

1. **用户操作**
   - 在仪表盘点击"新建采集任务"
   - 输入关键词：Gemini
   - 点击"开始采集"

2. **后端处理**
   - 采集 Reddit、YouTube、Twitter 数据
   - 清洗数据并保存到 `cleaned_data` 表（keyword = "Gemini"）
   - 运行 AI 分析生成报告
   - 更新 `task_status` 为完成

3. **前端轮询**
   - `DataProvider._pollTaskStatus()` 每 3 秒检查一次
   - 检测到任务完成
   - 调用 `refreshDashboard()` 和 `refreshSourceData()`
   - 更新 `_dashboardData` 和 `_sourcePosts`
   - 调用 `notifyListeners()`

4. **UI 更新**
   - 仪表盘页面（如果可见）自动更新
   - 显示进度提示："完成！"

5. **用户切换到源数据页面**
   - 点击底部导航栏的"源数据"
   - `_MainNavigationState.setState()` 被调用
   - `_getPage(1)` 创建新的 `SourceDataPage` 实例
   - `_SourceDataPageState.initState()` 被调用
   - 调用 `refreshSourceData()`
   - 后端返回最新关键词（Gemini）的数据
   - UI 显示正确的数据

### 场景：用户在页面间切换

1. **从仪表盘切换到源数据**
   - 创建新的 `SourceDataPage`
   - 自动刷新数据

2. **从源数据切换回仪表盘**
   - 创建新的 `DashboardPage`
   - 自动刷新数据

3. **再次切换到源数据**
   - 再次创建新的 `SourceDataPage`
   - 再次刷新数据
   - 确保显示最新数据

## 优点和权衡

### 优点
1. **简单直接**：不需要复杂的状态管理
2. **数据一致性**：每次都显示最新数据
3. **易于维护**：逻辑清晰，容易理解
4. **自动刷新**：用户无需手动操作

### 权衡
1. **页面状态不保留**：滚动位置等状态会丢失
   - 对于这个应用，这不是问题
   - 用户期望看到最新数据，而不是保留旧的浏览位置

2. **性能影响**：每次切换都重新创建页面
   - 对于这个应用，页面很轻量，影响可忽略
   - 数据刷新是必要的，无法避免网络请求

## 测试验证

### 自动化测试
创建了 `test_keyword_switch.py` 脚本：
- 采集两个不同的关键词
- 验证 API 返回正确的数据
- 确认数据隔离正确

### 手动测试步骤
1. 采集关键词 A
2. 查看仪表盘和源数据
3. 采集关键词 B
4. 再次查看仪表盘和源数据
5. 验证数据已更新为关键词 B

## 相关文档

- `SOURCE_DATA_UPDATE_FIX.md` - 详细的技术分析
- `QUICK_FIX_SUMMARY.md` - 快速参考
- `VERIFY_FIX.md` - 验证步骤
- `test_keyword_switch.py` - 自动化测试脚本
- `test_frontend_source_update.py` - API 验证脚本

## 总结

通过将页面创建方式从"缓存模式"改为"动态创建模式"，成功解决了源数据页面不更新的问题。这个方案简单有效，符合应用的使用场景，确保用户每次切换到源数据页面时都能看到最新的数据。

修复后，整个系统的关键词隔离功能完全正常：
- ✓ 后端正确按关键词隔离数据
- ✓ API 正确返回指定关键词的数据
- ✓ 前端正确显示最新关键词的数据
- ✓ 所有页面数据保持一致
