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

**index.js**
```javascript
const express = require('express');
const bodyParser = require('body-parser');
const authRoutes = require('./routes/authRoutes');
const orderRoutes = require('./routes/orderRoutes');
const paymentRoutes = require('./routes/paymentRoutes');
const { Sequelize } = require('sequelize');
const config = require('./config');

const app = express();
const PORT = process.env.PORT || 3000;

const sequelize = new Sequelize(config.database, config.username, config.password, {
    host: config.host,
    dialect: 'postgres',
});

app.use(bodyParser.json());
app.use('/api/auth', authRoutes);
app.use('/api/orders', orderRoutes);
app.use('/api/payments', paymentRoutes);

sequelize.authenticate()
    .then(() => {
        console.log('Database connection established.');
        app.listen(PORT, () => {
            console.log(`Server is running on port ${PORT}`);
        });
    })
    .catch(err => {
        console.error('Unable to connect to the database:', err);
    });
```

**routes/authRoutes.js**
```javascript
const express = require('express');
const { register, login } = require('../controllers/authController');
const router = express.Router();

router.post('/register', register);
router.post('/login', login);

module.exports = router;
```

**routes/orderRoutes.js**
```javascript
const express = require('express');
const { createOrder, getOrder } = require('../controllers/orderController');
const { authenticate } = require('../middleware/authMiddleware');
const router = express.Router();

router.post('/', authenticate, createOrder);
router.get('/:id', authenticate, getOrder);

module.exports = router;
```

**routes/paymentRoutes.js**
```javascript
const express = require('express');
const { processPayment } = require('../controllers/paymentController');
const { authenticate } = require('../middleware/authMiddleware');
const router = express.Router();

router.post('/', authenticate, processPayment);

module.exports = router;
```

**controllers/authController.js**
```javascript
const User = require('../models/userModel');
const bcrypt = require('bcrypt');
const jwt = require('jsonwebtoken');

exports.register = async (req, res) => {
    const { email, password } = req.body;
    const hashedPassword = await bcrypt.hash(password, 10);
    await User.create({ email, password_hash: hashedPassword });
    res.status(201).json({ message: 'User registered successfully' });
};

exports.login = async (req, res) => {
    const { email, password } = req.body;
    const user = await User.findOne({ where: { email } });
    if (user && await bcrypt.compare(password, user.password_hash)) {
        const token = jwt.sign({ id: user.id }, 'secretKey');
        return res.status(200).json({ token });
    }
    res.status(401).json({ message: 'Unauthorized' });
};
```

**controllers/orderController.js**
```javascript
const Order = require('../models/orderModel');

exports.createOrder = async (req, res) => {
    const { service, pickup_time, dropoff_time } = req.body;
    const order = await Order.create({
        user_id: req.user.id,
        service_id: service,
        pickup_time,
        dropoff_time
    });
    res.status(201).json({ message: 'Order created', order });
};

exports.getOrder = async (req, res) => {
    const order = await Order.findByPk(req.params.id);
    if (!order) return res.status(404).json({ message: 'Order not found' });
    res.status(200).json(order);
};
```

**controllers/paymentController.js**
```javascript
const Payment = require('../models/paymentModel');

exports.processPayment = async (req, res) => {
    const { orderId, amount, payment_method } = req.body;
    const payment = await Payment.create({ order_id: orderId, amount, payment_method });
    res.status(200).json({ message: 'Payment successful', payment });
};
```

**middleware/authMiddleware.js**
```javascript
const jwt = require('jsonwebtoken');
const User = require('../models/userModel');

exports.authenticate = async (req, res, next) => {
    const token = req.headers.authorization?.split(' ')[1];
    if (!token) return res.status(401).json({ message: 'Unauthorized' });
    try {
        const decoded = jwt.verify(token, 'secretKey');
        req.user = await User.findByPk(decoded.id);
        next();
    } catch (err) {
        res.status(401).json({ message: 'Unauthorized' });
    }
};
```

**models/userModel.js**
```javascript
const { Sequelize, DataTypes } = require('sequelize');
const sequelize = new Sequelize('your_database', 'your_username', 'your_password', {
    host: 'your_host',
    dialect: 'postgres',
});

const User = sequelize.define('User', {
    email: {
        type: DataTypes.STRING,
        unique: true,
        allowNull: false,
    },
    password_hash: {
        type: DataTypes.STRING,
        allowNull: false,
    },
}, {
    timestamps: true,
});

module.exports = User;
```

**models/orderModel.js**
```javascript
const { Sequelize, DataTypes } = require('sequelize');
const sequelize = new Sequelize('your_database', 'your_username', 'your_password', {
    host: 'your_host',
    dialect: 'postgres',
});

const Order = sequelize.define('Order', {
    user_id: {
        type: DataTypes.INTEGER,
        references: {
            model: 'Users',
            key: 'id',
        },
    },
    service_id: {
        type: DataTypes.INTEGER,
        allowNull: true,
    },
    pickup_time: {
        type: DataTypes.DATE,
        allowNull: false,
    },
    dropoff_time: {
        type: DataTypes.DATE,
        allowNull: false,
    },
    status: {
        type: DataTypes.STRING,
        defaultValue: 'pending',
    },
}, {
    timestamps: true,
});

module.exports = Order;
```

**models/paymentModel.js**
```javascript
const { Sequelize, DataTypes } = require('sequelize');
const sequelize = new Sequelize('your_database', 'your_username', 'your_password', {
    host: 'your_host',
    dialect: 'postgres',
});

const Payment = sequelize.define('Payment', {
    order_id: {
        type: DataTypes.INTEGER,
        references: {
            model: 'Orders',
            key: 'id',
        },
    },
    amount: {
        type: DataTypes.DECIMAL(10, 2),
        allowNull: false,
    },
    payment_method: {
        type: DataTypes.STRING,
        allowNull: false,
    },
}, {
    timestamps: true,
});

module.exports = Payment;
```

**config.js**
```javascript
module.exports = {
    host: 'localhost',
    username: 'your_username',
    password: 'your_password',
    database: 'your_database',
};
```

**SQL Database Schema**
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

This complete backend code structure caters to user authentication, order management, and payment processing for the Laundry MVP, ensuring a robust, secure, and efficient system.