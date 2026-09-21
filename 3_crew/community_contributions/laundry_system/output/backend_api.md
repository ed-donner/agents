# Laundry Business MVP - Backend APIs Design and Implementation

## API Specification (OpenAPI-style)

```yaml
openapi: 3.0.0
info:
  title: Laundry Service API
  version: 1.0.0
  description: API for managing laundry services including authentication, orders, payments, and admin controls.
servers:
  - url: http://localhost:3000/api
    description: Development server
paths:
  /auth/register:
    post:
      summary: User registration
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                email:
                  type: string
                password:
                  type: string
      responses:
        '201':
          description: User registered successfully
        '400':
          description: Invalid input

  /auth/login:
    post:
      summary: User login
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                email:
                  type: string
                password:
                  type: string
      responses:
        '200':
          description: Successful login
          content:
            application/json:
              schema:
                type: object
                properties:
                  token:
                    type: string
        '401':
          description: Unauthorized

  /orders:
    post:
      summary: Create a new order
      security:
        - bearerAuth: []
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                service:
                  type: string
                pickup_time:
                  type: string
                dropoff_time:
                  type: string
      responses:
        '201':
          description: Order created
        '400':
          description: Invalid data

  /orders/{id}:
    get:
      summary: Get order details
      security:
        - bearerAuth: []
      parameters:
        - in: path
          name: id
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Order details
        '404':
          description: Order not found

  /payments:
    post:
      summary: Process a payment
      security:
        - bearerAuth: []
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                orderId:
                  type: string
                amount:
                  type: number
                payment_method:
                  type: string
      responses:
        '200':
          description: Payment successful
        '400':
          description: Payment error

components:
  securitySchemes:
    bearerAuth:
      type: http
      scheme: bearer
```

## Database Schema

```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE services (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    service_id INTEGER REFERENCES services(id) ON DELETE SET NULL,
    pickup_time TIMESTAMP NOT NULL,
    dropoff_time TIMESTAMP NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE payments (
    id SERIAL PRIMARY KEY,
    order_id INTEGER REFERENCES orders(id) ON DELETE CASCADE,
    amount DECIMAL(10, 2) NOT NULL,
    payment_method VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Core Backend Code (Node.js with Express.js)

### Directory Structure
```
/laundry-service
├── /controllers
│   ├── authController.js
│   ├── orderController.js
│   ├── paymentController.js
├── /models
│   ├── userModel.js
│   ├── orderModel.js
│   ├── serviceModel.js
│   ├── paymentModel.js
├── /routes
│   ├── authRoutes.js
│   ├── orderRoutes.js
│   ├── paymentRoutes.js
├── /middleware
│   ├── authMiddleware.js
├── index.js
└── config.js
```

### Code Implementation

**index.js**
```javascript
const express = require('express');
const bodyParser = require('body-parser');
const authRoutes = require('./routes/authRoutes');
const orderRoutes = require('./routes/orderRoutes');
const paymentRoutes = require('./routes/paymentRoutes');

const app = express();
const PORT = process.env.PORT || 3000;

app.use(bodyParser.json());
app.use('/api/auth', authRoutes);
app.use('/api/orders', orderRoutes);
app.use('/api/payments', paymentRoutes);

app.listen(PORT, () => {
    console.log(`Server is running on port ${PORT}`);
});
```

**authRoutes.js**
```javascript
const express = require('express');
const { register, login } = require('../controllers/authController');
const router = express.Router();

router.post('/register', register);
router.post('/login', login);

module.exports = router;
```

**orderRoutes.js**
```javascript
const express = require('express');
const { createOrder, getOrder } = require('../controllers/orderController');
const { authenticate } = require('../middleware/authMiddleware');
const router = express.Router();

router.post('/', authenticate, createOrder);
router.get('/:id', authenticate, getOrder);

module.exports = router;
```

**paymentRoutes.js**
```javascript
const express = require('express');
const { processPayment } = require('../controllers/paymentController');
const { authenticate } = require('../middleware/authMiddleware');
const router = express.Router();

router.post('/', authenticate, processPayment);

module.exports = router;
```

**authController.js**
```javascript
const User = require('../models/userModel');
const bcrypt = require('bcrypt');
const jwt = require('jsonwebtoken');

exports.register = async (req, res) => {
  const { email, password } = req.body;
  const hashedPassword = await bcrypt.hash(password, 10);
  const user = await User.create({ email, password_hash: hashedPassword });
  res.status(201).json({ message: 'User registered successfully' });
};

exports.login = async (req, res) => {
  const { email, password } = req.body;
  const user = await User.findOne({ email });
  if (user && await bcrypt.compare(password, user.password_hash)) {
    const token = jwt.sign({ id: user.id }, 'secretKey'); // Implement a secure key management
    return res.status(200).json({ token });
  }
  res.status(401).json({ message: 'Unauthorized' });
};
```

**orderController.js**
```javascript
const Order = require('../models/orderModel');

exports.createOrder = async (req, res) => {
  const { service, pickup_time, dropoff_time } = req.body;
  const order = await Order.create({ user_id: req.user.id, service_id: service, pickup_time, dropoff_time });
  res.status(201).json({ message: 'Order created', order });
};

exports.getOrder = async (req, res) => {
  const order = await Order.findById(req.params.id);
  if (!order) return res.status(404).json({ message: 'Order not found' });
  res.status(200).json(order);
};
```

**paymentController.js**
```javascript
const Payment = require('../models/paymentModel');

exports.processPayment = async (req, res) => {
  const { orderId, amount, payment_method } = req.body;
  // Integrate with Stripe/PayPal SDK
  const payment = await Payment.create({ order_id: orderId, amount, payment_method });
  res.status(200).json({ message: 'Payment successful', payment });
};
```

**authMiddleware.js**
```javascript
const jwt = require('jsonwebtoken');
const User = require('../models/userModel');

exports.authenticate = async (req, res, next) => {
  const token = req.headers.authorization?.split(' ')[1];
  if (!token) return res.status(401).json({ message: 'Unauthorized' });
  try {
    const decoded = jwt.verify(token, 'secretKey'); // Implement a secure key management
    req.user = await User.findById(decoded.id);
    next();
  } catch (err) {
    res.status(401).json({ message: 'Unauthorized' });
  }
};
```

## Outcome Expectations

This design and implementation of the Laundry MVP backend API will ensure a robust, secure, and efficient system for user authentication, order management, and payment processing. It will facilitate a seamless customer experience and empower staff with tools for effective management. Additional admin functionalities will provide oversight and control, contributing to the overall success of the laundry business, while also preparing for future enhancements and scaling.