import 'api_service.dart';
import '../models/order.dart';

class OrderService {
  final ApiService _apiService = ApiService();

  Future<Order> createOrder(Order order) async {
    return await _apiService.createOrder(order);
  }
}