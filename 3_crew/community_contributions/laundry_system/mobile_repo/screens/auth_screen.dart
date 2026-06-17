import 'package:flutter/material.dart';
import '../providers/auth_provider.dart';
import '../widgets/custom_button.dart';

class AuthScreen extends StatefulWidget {
  @override
  _AuthScreenState createState() => _AuthScreenState();
}

class _AuthScreenState extends State<AuthScreen> {
  final TextEditingController _emailController = TextEditingController();
  final TextEditingController _passwordController = TextEditingController();
  
  void _login() {
    // Implement login functionality using AuthProvider
  }

  void _register() {
    // Implement register functionality using AuthProvider
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('Login/Register')),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          children: [
            TextField(controller: _emailController, decoration: InputDecoration(labelText: 'Email')),
            TextField(controller: _passwordController, decoration: InputDecoration(labelText: 'Password')),
            CustomButton(label: 'Login', onPressed: _login),
            CustomButton(label: 'Register', onPressed: _register),
          ],
        ),
      ),
    );
  }
}