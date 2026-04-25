### Directory Structure
```plaintext
/laundry-service
├── /controllers
│   ├── authController.js
│   ├── orderController.js
│   └── paymentController.js
├── /models
│   ├── userModel.js
│   ├── orderModel.js
│   ├── serviceModel.js
│   └── paymentModel.js
├── /routes
│   ├── authRoutes.js
│   ├── orderRoutes.js
│   └── paymentRoutes.js
├── /middleware
│   └── authMiddleware.js
├── index.js
└── config.js
```

### Dockerfile for Backend API
**/laundry-service/Dockerfile**
```Dockerfile
# Use official Node.js image
FROM node:14

# Create app directory
WORKDIR /usr/src/app

# Install app dependencies
COPY package*.json ./
RUN npm install

# Bundle app source
COPY . .

# Expose API port
EXPOSE 3000

# Command to run the app
CMD ["node", "index.js"]
```

### GitHub Actions CI/CD Configuration
**/.github/workflows/deploy.yml**
```yaml
name: Deploy Backend API

on:
  push:
    branches:
      - main

jobs:
  build:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout Repository
        uses: actions/checkout@v2
      
      - name: Set up Node.js
        uses: actions/setup-node@v2
        with:
          node-version: '14'

      - name: Install Dependencies
        run: npm install

      - name: Run Tests
        run: npm test

      - name: Build Docker Image
        run: docker build -t laundry-backend .

      - name: Login to Docker Hub
        run: echo "${{ secrets.DOCKER_HUB_TOKEN }}" | docker login -u ${{ secrets.DOCKER_HUB_USERNAME }} --password-stdin

      - name: Push Docker Image
        run: docker tag laundry-backend yourusername/laundry-backend:latest && docker push yourusername/laundry-backend:latest

      - name: Deploy to Kubernetes
        run: kubectl set image deployment/laundry-backend laundry-backend=yourusername/laundry-backend:latest --record
```

### Environment Variables
**/.env**
```plaintext
DATABASE_URL=postgres://user:password@database:5432/laundry_db
JWT_SECRET=your_jwt_secret_key
STRIPE_API_KEY=your_stripe_secret_key
PORT=3000
```

### Kubernetes Deployment Configuration
**/kubernetes/laundry-backend-deployment.yaml**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: laundry-backend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: laundry-backend
  template:
    metadata:
      labels:
        app: laundry-backend
    spec:
      containers:
      - name: backend
        image: yourusername/laundry-backend:latest
        ports:
        - containerPort: 3000
        env:
        - name: DATABASE_URL
          value: "postgres://user:password@database:5432/laundry_db"
        - name: JWT_SECRET
          value: "your_jwt_secret_key"
        - name: STRIPE_API_KEY
          value: "your_stripe_secret_key"
```

### Flutter Application Directory Structure
```plaintext
/laundry_app
├── /lib
│   ├── /models
│   │   ├── user.dart
│   │   ├── order.dart
│   │   └── service.dart
│   ├── /services
│   │   ├── api_service.dart
│   │   ├── auth_service.dart
│   │   └── order_service.dart
│   ├── /screens
│   │   ├── auth_screen.dart
│   │   ├── order_screen.dart
│   │   ├── staff_dashboard.dart
│   │   └── admin_panel.dart
│   ├── /providers
│   │   ├── auth_provider.dart
│   │   └── order_provider.dart
│   ├── /utils
│   │   ├── constants.dart
│   │   └── validators.dart
│   ├── /widgets
│   │   ├── custom_button.dart
│   │   └── service_card.dart
│   └── main.dart
```

### Flutter Code Example
**lib/models/user.dart**
```dart
class User {
  final int id;
  final String email;

  User({required this.id, required this.email});

  factory User.fromJson(Map<String, dynamic> json) {
    return User(
      id: json['id'],
      email: json['email'],
    );
  }
}
```

**lib/services/api_service.dart**
```dart
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
```

This deployment-ready configuration includes Docker setup, CI/CD with GitHub Actions, and application code structured for the Laundry MVP, fulfilling the architecture requirements and ensuring an efficient workflow from development to production.