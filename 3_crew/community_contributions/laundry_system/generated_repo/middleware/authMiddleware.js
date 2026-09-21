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