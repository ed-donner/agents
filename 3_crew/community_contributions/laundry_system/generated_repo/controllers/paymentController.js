const Payment = require('../models/paymentModel');

exports.processPayment = async (req, res) => {
    const { orderId, amount, payment_method } = req.body;
    const payment = await Payment.create({ order_id: orderId, amount, payment_method });
    res.status(200).json({ message: 'Payment successful', payment });
};