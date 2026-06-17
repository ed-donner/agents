class Order {
  final int id;
  final int userId;
  final String service;
  final DateTime pickupTime;
  final DateTime dropoffTime;
  final String status;

  Order({
    required this.id,
    required this.userId,
    required this.service,
    required this.pickupTime,
    required this.dropoffTime,
    required this.status,
  });

  factory Order.fromJson(Map<String, dynamic> json) {
    return Order(
      id: json['id'],
      userId: json['user_id'],
      service: json['service'],
      pickupTime: DateTime.parse(json['pickup_time']),
      dropoffTime: DateTime.parse(json['dropoff_time']),
      status: json['status'],
    );
  }
}