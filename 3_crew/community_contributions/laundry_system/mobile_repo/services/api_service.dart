import 'dart:convert';
import 'package:http/http.dart' as http;
import '../models/user.dart';
import '../models/order.dart';
import '../models/service.dart';

class ApiService {
  static const String baseUrl = 'http://localhost:3000/api';

  Future<User> register(String email, String password) async {
    final response = await http.post(
      Uri.parse('$baseUrl/auth/register'),
      headers: {'Content-Type': 'application/json'},
      body: json.encode({'email': email, 'password': password}),
    );
    return User.fromJson(json.decode(response.body));
  }

  Future<User> login(String email, String password) async {
    final response = await http.post(
      Uri.parse('$baseUrl/auth/login'),
      headers: {'Content-Type': 'application/json'},
      body: json.encode({'email': email, 'password': password}),
    );
    return User.fromJson(json.decode(response.body));
  }

  Future<List<Service>> fetchServices() async {
    final response = await http.get(Uri.parse('$baseUrl/services'));
    final List<dynamic> servicesJson = json.decode(response.body);
    return servicesJson.map((json) => Service.fromJson(json)).toList();
  }

  Future<Order> createOrder(Order order) async {
    final response = await http.post(
      Uri.parse('$baseUrl/orders'),
      headers: {'Content-Type': 'application/json'},
      body: json.encode({
        'service': order.service,
        'pickup_time': order.pickupTime.toIso8601String(),
        'dropoff_time': order.dropoffTime.toIso8601String(),
      }),
    );
    return Order.fromJson(json.decode(response.body));
  }
}