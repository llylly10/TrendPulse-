import 'dart:convert';
import 'package:http/http.dart' as http;
import '../models/dashboard_data.dart';
import '../models/source_post.dart';

import '../models/subscription.dart';
import '../models/alert.dart';

class ApiService {
  static const String baseUrl = 'http://localhost:8888/api';

  Future<DashboardData> fetchDashboardData() async {
    final response = await http.get(Uri.parse('$baseUrl/dashboard'));
    if (response.statusCode == 200) {
      return DashboardData.fromJson(
          json.decode(utf8.decode(response.bodyBytes)));
    } else {
      throw Exception('Failed to load dashboard data');
    }
  }

  Future<List<SourcePost>> fetchSourceData() async {
    final response = await http.get(Uri.parse('$baseUrl/source-data'));
    if (response.statusCode == 200) {
      List<dynamic> body = json.decode(utf8.decode(response.bodyBytes));
      return body.map((dynamic item) => SourcePost.fromJson(item)).toList();
    } else {
      throw Exception('Failed to load source data');
    }
  }

  Future<void> startCollection(String keyword, String language, int redditLimit,
      int youtubeLimit, int twitterLimit) async {
    final response = await http.post(
      Uri.parse('$baseUrl/collect'),
      headers: {'Content-Type': 'application/json'},
      body: json.encode({
        'keyword': keyword,
        'language': language,
        'reddit_limit': redditLimit,
        'youtube_limit': youtubeLimit,
        'twitter_limit': twitterLimit,
      }),
    );
    if (response.statusCode != 200 && response.statusCode != 202) {
      throw Exception('Failed to start collection: ${response.body}');
    }
  }

  Future<Map<String, dynamic>> fetchTaskStatus() async {
    final response = await http.get(Uri.parse('$baseUrl/task-status'));
    if (response.statusCode == 200) {
      return json.decode(utf8.decode(response.bodyBytes));
    } else {
      throw Exception('Failed to fetch task status');
    }
  }

  Future<List<Subscription>> fetchSubscriptions() async {
    final response = await http.get(Uri.parse('$baseUrl/subscriptions'));
    if (response.statusCode == 200) {
      List<dynamic> body = json.decode(utf8.decode(response.bodyBytes));
      return body.map((dynamic item) => Subscription.fromJson(item)).toList();
    } else {
      throw Exception('Failed to load subscriptions');
    }
  }

  Future<void> createSubscription(
      String keyword,
      String language,
      int redditLimit,
      int youtubeLimit,
      int twitterLimit,
      int intervalSeconds) async {
    final response = await http.post(
      Uri.parse('$baseUrl/subscriptions'),
      headers: {'Content-Type': 'application/json'},
      body: json.encode({
        'keyword': keyword,
        'language': language,
        'reddit_limit': redditLimit,
        'youtube_limit': youtubeLimit,
        'twitter_limit': twitterLimit,
        'interval_seconds': intervalSeconds,
      }),
    );
    if (response.statusCode != 200) {
      throw Exception('Failed to create subscription: ${response.body}');
    }
  }

  Future<void> deleteSubscription(int id) async {
    final response = await http.delete(Uri.parse('$baseUrl/subscriptions/$id'));
    if (response.statusCode != 200) {
      throw Exception('Failed to delete subscription');
    }
  }

  Future<List<Alert>> fetchAlerts() async {
    final response = await http.get(Uri.parse('$baseUrl/alerts'));
    if (response.statusCode == 200) {
      List<dynamic> body = json.decode(utf8.decode(response.bodyBytes));
      return body.map((dynamic item) => Alert.fromJson(item)).toList();
    } else {
      throw Exception('Failed to load alerts');
    }
  }

  Future<void> clearAllData() async {
    final response = await http.post(Uri.parse('$baseUrl/clear-data'));
    if (response.statusCode != 200) {
      throw Exception('Failed to clear data: ${response.body}');
    }
  }
}
