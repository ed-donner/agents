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