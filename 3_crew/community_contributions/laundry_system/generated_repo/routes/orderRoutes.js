const express = require('express');
const { createOrder, getOrder } = require('../controllers/orderController');
const { authenticate } = require('../middleware/authMiddleware');
const router = express.Router();

router.post('/', authenticate, createOrder);
router.get('/:id', authenticate, getOrder);

module.exports = router;