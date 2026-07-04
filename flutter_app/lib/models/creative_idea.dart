class CreativeIdea {
  final int id;
  final String content;
  final DateTime createdAt;

  CreativeIdea({
    required this.id,
    required this.content,
    required this.createdAt,
  });

  factory CreativeIdea.fromJson(Map<String, dynamic> json) {
    return CreativeIdea(
      id: json['id'] as int,
      content: json['content'] as String,
      createdAt: DateTime.parse(json['created_at'] as String),
    );
  }
}
