import 'package:flutter/material.dart';
import '../services/order_service.dart';
import '../models/order.dart';

class OrderProvider with ChangeNotifier {
  final OrderService _orderService = OrderService();
  
  Future<Order> createOrder(Order order) async {
    return await _orderService.createOrder(order);
  }
}