# DashboardData 模型修复

## 问题
编译错误：`The getter 'keyword' isn't defined for the type 'DashboardData'`

## 原因
`DashboardData` 模型缺少 `keyword` 字段，但后端 API 已经返回了这个字段

## 修复
在 `frontend/lib/models/dashboard_data.dart` 中添加 `keyword` 字段：

```dart
class DashboardData {
  final String keyword;  // 新增字段
  
  DashboardData({
    ...
    this.keyword = '',  // 默认值为空字符串
  });
  
  factory DashboardData.fromJson(Map<String, dynamic> json) {
    return DashboardData(
      ...
      keyword: json['keyword'] as String? ?? '',  // 从 JSON 解析
    );
  }
}
```

## 后端 API
`/api/dashboard` 端点已经返回 `keyword` 字段：

```python
return {
    ...
    "keyword": keyword or ""
}
```

## 使用
源数据页面使用这个字段显示当前关键词：

```dart
final currentKeyword = provider.dashboardData?.keyword ?? '未知';
```

## 状态
✅ 已修复，可以正常编译运行
