import 'package:flutter/material.dart';

class CustomButton extends StatelessWidget {
  final String label;
  final void Function() onPressed;

  CustomButton({required this.label, required this.onPressed});

  @override
  Widget build(BuildContext context) {
    return ElevatedButton(
      onPressed: onPressed,
      child: Text(label),
    );
  }
}