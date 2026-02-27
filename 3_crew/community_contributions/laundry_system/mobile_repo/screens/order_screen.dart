import 'package:flutter/material.dart';
import '../providers/order_provider.dart';
import '../widgets/custom_button.dart';

class OrderScreen extends StatefulWidget {
  @override
  _OrderScreenState createState() => _OrderScreenState();
}

class _OrderScreenState extends State<OrderScreen> {
  final TextEditingController _serviceController = TextEditingController();
  DateTime? _pickupTime;
  DateTime? _dropoffTime;

  void _createOrder() {
    // Implement create order functionality using OrderProvider
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('Create Order')),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          children: [
            TextField(controller: _serviceController, decoration: InputDecoration(labelText: 'Service')),
            // Add DateTime pickers for pickup and dropoff times
            CustomButton(label: 'Create Order', onPressed: _createOrder),
          ],
        ),
      ),
    );
  }
}