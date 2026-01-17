class SourcePost {
  final String platform;
  final String content;
  final String author;
  final String timestamp;
  final String url;
  final Map<String, dynamic> engagement;

  SourcePost({
    required this.platform,
    required this.content,
    required this.author,
    required this.timestamp,
    required this.url,
    required this.engagement,
  });

  factory SourcePost.fromJson(Map<String, dynamic> json) {
    return SourcePost(
      platform: json['platform'] ?? 'Unknown',
      content: json['content'] ?? '',
      author: json['author'] ?? 'Anonymous',
      timestamp: json['timestamp'] ?? '',
      url: json['url'] ?? '',
      engagement: json['engagement'] ?? {},
    );
  }
}
