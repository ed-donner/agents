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