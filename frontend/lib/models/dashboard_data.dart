class DashboardData {
  final double heatIndex;
  final int totalPosts;
  final Sentiment sentiment;
  final List<String> keyPoints;
  final String summary;
  final String mermaidGraph;
  final Map<String, String> nodeSentiments;
  final String keyword;

  DashboardData({
    required this.heatIndex,
    required this.totalPosts,
    required this.sentiment,
    required this.keyPoints,
    required this.summary,
    required this.mermaidGraph,
    this.nodeSentiments = const {},
    this.keyword = '',
  });

  factory DashboardData.fromJson(Map<String, dynamic> json) {
    return DashboardData(
      heatIndex: (json['heat_index'] as num).toDouble(),
      totalPosts: json['total_posts'] as int,
      sentiment: Sentiment.fromJson(json['sentiment']),
      keyPoints: List<String>.from(json['key_points']),
      summary: json['summary'] as String,
      mermaidGraph: json['mermaid_graph'] ?? '',
      nodeSentiments: json['node_sentiments'] != null 
          ? Map<String, String>.from(json['node_sentiments'])
          : {},
      keyword: json['keyword'] as String? ?? '',
    );
  }
}

class Sentiment {
  final double score;
  final String label;

  Sentiment({required this.score, required this.label});

  factory Sentiment.fromJson(Map<String, dynamic> json) {
    return Sentiment(
      score: (json['score'] as num).toDouble(),
      label: json['label'] as String,
    );
  }
}
