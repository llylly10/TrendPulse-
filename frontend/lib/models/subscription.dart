class Subscription {
  final int id;
  final String keyword;
  final String language;
  final int intervalSeconds;
  final int lastRun;
  final int nextRun;
  final int executionCount;

  Subscription({
    required this.id,
    required this.keyword,
    required this.language,
    required this.intervalSeconds,
    required this.lastRun,
    required this.nextRun,
    required this.executionCount,
  });

  factory Subscription.fromJson(Map<String, dynamic> json) {
    return Subscription(
      id: json['id'],
      keyword: json['keyword'],
      language: json['language'],
      intervalSeconds: json['interval_seconds'] ?? json['interval_hours'] * 3600,
      lastRun: json['last_run'],
      nextRun: json['next_run'],
      executionCount: json['execution_count'] ?? 0,
    );
  }
  
  // 格式化显示间隔时间
  String get intervalDisplay {
    if (intervalSeconds < 60) {
      return '$intervalSeconds 秒';
    } else if (intervalSeconds < 3600) {
      final minutes = intervalSeconds ~/ 60;
      final seconds = intervalSeconds % 60;
      return seconds > 0 ? '$minutes 分 $seconds 秒' : '$minutes 分';
    } else {
      final hours = intervalSeconds ~/ 3600;
      final minutes = (intervalSeconds % 3600) ~/ 60;
      final seconds = intervalSeconds % 60;
      if (minutes > 0 && seconds > 0) {
        return '$hours 时 $minutes 分 $seconds 秒';
      } else if (minutes > 0) {
        return '$hours 时 $minutes 分';
      } else if (seconds > 0) {
        return '$hours 时 $seconds 秒';
      } else {
        return '$hours 小时';
      }
    }
  }
  
  // 格式化显示下次执行时间
  String get nextRunDisplay {
    if (nextRun == 0) {
      return '未运行';
    }
    final nextDateTime = DateTime.fromMillisecondsSinceEpoch(nextRun * 1000);
    final now = DateTime.now();
    final diff = nextDateTime.difference(now);
    
    if (diff.isNegative) {
      return '即将执行';
    }
    
    if (diff.inSeconds < 60) {
      return '${diff.inSeconds} 秒后';
    } else if (diff.inMinutes < 60) {
      return '${diff.inMinutes} 分钟后';
    } else if (diff.inHours < 24) {
      return '${diff.inHours} 小时后';
    } else {
      return nextDateTime.toString().split('.')[0];
    }
  }
}
