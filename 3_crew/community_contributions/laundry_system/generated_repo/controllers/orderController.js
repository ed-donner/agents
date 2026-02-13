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