class Alert {
  final int id;
  final int subscriptionId;
  final String message;
  final int createdAt;
  final bool isRead;

  Alert({
    required this.id,
    required this.subscriptionId,
    required this.message,
    required this.createdAt,
    required this.isRead,
  });

  factory Alert.fromJson(Map<String, dynamic> json) {
    return Alert(
      id: json['id'],
      subscriptionId: json['subscription_id'],
      message: json['message'],
      createdAt: json['created_at'],
      isRead: json['is_read'] == 1,
    );
  }
}
