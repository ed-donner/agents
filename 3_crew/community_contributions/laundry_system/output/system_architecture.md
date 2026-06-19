# System Architecture Document for Laundry MVP

## Overview

This document outlines the system architecture for the Laundry MVP (Minimum Viable Product). The architecture focuses on a mobile-first approach, ensuring both scalability and security while adhering to component boundary definitions.

## System Components

1. **Mobile Customer App**
2. **Backend API**
3. **Database**
4. **Payment Processor**
5. **Admin Panel**
6. **Staff Dashboard**

## Technology Stack

### Mobile Customer App
- **Frontend Framework**: React Native (for cross-platform mobile development)
- **Authentication**: Firebase Authentication (supports email and social logins)

### Backend API
- **Framework**: Node.js with Express.js 
- **API Protocol**: RESTful API design 
- **Authentication**: JSON Web Tokens (JWT) for session management 

### Database
- **Database System**: PostgreSQL (for relational data storage)
- **ORM**: Sequelize (for database interactions)

### Payment Integration
- **Processor**: Stripe or PayPal (for payment processing)
- **Compliance**: PCI-DSS compliance ensuring secure transaction handling

### Admin and Staff Tools
- **Web Framework**: React.js (for the admin panel and staff dashboard)
- **Real-time Notifications**: Socket.io (for real-time updates)

## Component Diagrams

### 1. High-Level Architecture Diagram

```
+-----------------+           +-----------------+
| Mobile Customer  | <----->  |   Backend API   | <-----> 
|      App        |           |                 |
+-----------------+           +-----------------+
        |                              |
        V                              |
+-----------------+           +-------------------+
|   Payment       |           |       Database     |
|     Gateway     |           |  (PostgreSQL)     |
+-----------------+           +-------------------+
                                    |
+-------------------------------+   |
|           Admin Panel         |   |
+-------------------------------+   |
                                    |
+-------------------------------+   |
|          Staff Dashboard      |   |
+-------------------------------+   |
```

### 2. Data Flow Diagram

1. **User Registration**
   - User inputs data -> Mobile App sends request to Backend API -> API validates and saves data in Database -> User receives confirmation.
  
2. **Order Placement**
   - User selects services -> Mobile App sends order details to Backend API -> API updates Database -> Sends order confirmation back to Mobile App.

3. **Payment Processing**
   - User initiates payment -> Payment details sent to Payment Gateway via Backend API -> Payment Gateway processes request -> Response sent back to Mobile App via Backend API.

4. **Order Management**
   - Staff receives new order notification -> Staff updates order status via Staff Dashboard -> Status is updated in the Database -> Real-time notification sent to Mobile App.

## Detailed Flow and Feature Specifications

### Customer App Features
- **Registration & Authentication**: Supports sign-up with email and social media; uses Firebase for secure authentications.
- **Service Selection & Pricing**: API fetches available services from Database; displays pricing transparently.
- **Order Placement**: Allows scheduling pickups and drop-offs limited by service availability.
- **Real-time Order Tracking**: Fetches updated status using WebSocket connections for real-time alerts.

### Staff Tools
- **Order Management Dashboard**: Provides staff with the list of incoming orders, enables status updates, and allows notifications for timely actions.
- **Analytics (Future Scope)**: Basic data collected for later analysis.

### Admin Panel Features
- **User Management**: Admin can create, read, update, and delete (CRUD) customer records.
- **Service Management**: Admin can update service offerings to reflect current pricing and availability.
- **Order Analytics Overview**: Dashboards available for initial insights into operation.

## Security Considerations
- **GDPR Compliance**: Ensure users are informed on data usage and provide options to delete their information.
- **Data Encryption**: All sensitive data including payment information should be encrypted both in transit (TLS) and at rest.

## Outcome Expectations
By following this architecture, the Laundry MVP is expected to provide:
- A seamless mobile experience for users to place orders and make payments.
- Efficient order management and status updates for staff.
- Strong administrative control over operations and customer interactions.
- Compliance with industry standards for security and data protection.
  
This system will be scalable, enabling future development of advanced features, such as customer loyalty programs and analytical tools, without compromising existing functionalities.