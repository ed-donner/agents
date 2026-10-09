class Service {
  final int id;
  final String name;
  final double price;

  Service({required this.id, required this.name, required this.price});

  factory Service.fromJson(Map<String, dynamic> json) {
    return Service(
      id: json['id'],
      name: json['name'],
      price: json['price'].toDouble(),
    );
  }
}