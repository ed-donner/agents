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