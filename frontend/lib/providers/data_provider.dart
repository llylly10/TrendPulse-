import 'package:flutter/material.dart';
import '../models/dashboard_data.dart';
import '../models/source_post.dart';
import '../services/api_service.dart';

import '../models/subscription.dart';
import '../models/alert.dart';

class DataProvider with ChangeNotifier {
  final ApiService _apiService = ApiService();

  DashboardData? _dashboardData;
  List<SourcePost> _sourcePosts = [];
  List<Subscription> _subscriptions = [];
  List<Alert> _alerts = [];
  bool _isLoading = false;
  String? _error;
  
  // 任务状态
  bool _isTaskRunning = false;
  String _taskProgress = '';

  DashboardData? get dashboardData => _dashboardData;
  List<SourcePost> get sourcePosts => _sourcePosts;
  List<Subscription> get subscriptions => _subscriptions;
  List<Alert> get alerts => _alerts;
  bool get isLoading => _isLoading;
  String? get error => _error;
  bool get isTaskRunning => _isTaskRunning;
  String get taskProgress => _taskProgress;

  Future<void> refreshDashboard() async {
    _isLoading = true;
    _error = null;
    notifyListeners();
    try {
      _dashboardData = await _apiService.fetchDashboardData();
      _alerts = await _apiService.fetchAlerts();
    } catch (e) {
      _error = e.toString();
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  Future<void> refreshSourceData() async {
    _isLoading = true;
    _error = null;
    notifyListeners();
    try {
      _sourcePosts = await _apiService.fetchSourceData();
    } catch (e) {
      _error = e.toString();
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  Future<void> startCollection(String keyword, String language, int redditLimit,
      int youtubeLimit, int twitterLimit) async {
    _isLoading = true;
    _error = null;
    notifyListeners();
    try {
      await _apiService.startCollection(
          keyword, language, redditLimit, youtubeLimit, twitterLimit);
      
      // 启动轮询检查任务状态
      _pollTaskStatus();
    } catch (e) {
      _error = e.toString();
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  void _pollTaskStatus() {
    // 每3秒检查一次任务状态，最多检查40次（2分钟）
    int pollCount = 0;
    const maxPolls = 40;
    
    _isTaskRunning = true;
    _taskProgress = '任务启动中...';
    notifyListeners();
    
    Future.delayed(const Duration(seconds: 3), () async {
      while (pollCount < maxPolls) {
        try {
          final status = await _apiService.fetchTaskStatus();
          final isRunning = status['is_running'] as bool;
          final progress = status['progress'] as String? ?? '';
          
          _isTaskRunning = isRunning;
          _taskProgress = progress;
          notifyListeners();
          
          if (!isRunning) {
            // 任务完成，刷新所有数据
            _taskProgress = '正在刷新数据...';
            notifyListeners();
            
            await Future.delayed(const Duration(seconds: 1));
            await refreshDashboard();
            await refreshSourceData(); // 同时刷新源数据
            
            _taskProgress = '完成！';
            notifyListeners();
            
            // 2秒后清除状态
            await Future.delayed(const Duration(seconds: 2));
            _isTaskRunning = false;
            _taskProgress = '';
            notifyListeners();
            
            break;
          }
          
          pollCount++;
          if (pollCount < maxPolls) {
            await Future.delayed(const Duration(seconds: 3));
          }
        } catch (e) {
          _isTaskRunning = false;
          _taskProgress = '';
          notifyListeners();
          break;
        }
      }
      
      if (pollCount >= maxPolls) {
        _isTaskRunning = false;
        _taskProgress = '';
        notifyListeners();
      }
    });
  }

  Future<void> fetchSubscriptions() async {
    _isLoading = true;
    _error = null;
    notifyListeners();
    try {
      _subscriptions = await _apiService.fetchSubscriptions();
    } catch (e) {
      _error = e.toString();
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  Future<void> createSubscription(
      String keyword,
      String language,
      int redditLimit,
      int youtubeLimit,
      int twitterLimit,
      int intervalSeconds) async {
    _isLoading = true;
    _error = null;
    notifyListeners();
    try {
      await _apiService.createSubscription(keyword, language, redditLimit,
          youtubeLimit, twitterLimit, intervalSeconds);
      await fetchSubscriptions();
      
      // 启动轮询检查任务状态（定时任务会立即执行）
      _pollTaskStatusForSubscription();
    } catch (e) {
      _error = e.toString();
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  void _pollTaskStatusForSubscription() {
    // 每3秒检查一次任务状态，最多检查40次（2分钟）
    int pollCount = 0;
    const maxPolls = 40;
    
    _isTaskRunning = true;
    _taskProgress = '定时任务启动中...';
    notifyListeners();
    
    Future.delayed(const Duration(seconds: 3), () async {
      while (pollCount < maxPolls) {
        try {
          final status = await _apiService.fetchTaskStatus();
          final isRunning = status['is_running'] as bool;
          final progress = status['progress'] as String? ?? '';
          
          _isTaskRunning = isRunning;
          _taskProgress = progress;
          notifyListeners();
          
          if (!isRunning) {
            // 任务完成，刷新所有数据
            _taskProgress = '正在刷新数据...';
            notifyListeners();
            
            await Future.delayed(const Duration(seconds: 1));
            await refreshDashboard();
            await refreshSourceData();
            await fetchSubscriptions(); // 刷新订阅列表以更新执行次数
            
            _taskProgress = '完成！';
            notifyListeners();
            
            // 2秒后清除状态
            await Future.delayed(const Duration(seconds: 2));
            _isTaskRunning = false;
            _taskProgress = '';
            notifyListeners();
            
            break;
          }
          
          pollCount++;
          if (pollCount < maxPolls) {
            await Future.delayed(const Duration(seconds: 3));
          }
        } catch (e) {
          _isTaskRunning = false;
          _taskProgress = '';
          notifyListeners();
          break;
        }
      }
      
      if (pollCount >= maxPolls) {
        _isTaskRunning = false;
        _taskProgress = '';
        notifyListeners();
      }
    });
  }

  Future<void> deleteSubscription(int id) async {
    _isLoading = true;
    _error = null;
    notifyListeners();
    try {
      await _apiService.deleteSubscription(id);
      await fetchSubscriptions();
    } catch (e) {
      _error = e.toString();
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  Future<void> clearAllData() async {
    _isLoading = true;
    _error = null;
    notifyListeners();
    try {
      await _apiService.clearAllData();
      // 清空本地状态
      _dashboardData = null;
      _sourcePosts = [];
    } catch (e) {
      _error = e.toString();
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }
}
