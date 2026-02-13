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