### Entity-Relationship Diagram (ERD)

```
[Users] 1 ------< [Transactions]
    |                 |
    |                 |
    |                 |
   1|                 |*   
    |                 |
    V                 V
[Watchlists] 1 ------< [Stocks] >------* [MarketData]
    |                 |
    |                 |
   *|                 |*
    |                 |
    V                 V
  [News]           [Transactions]
```

### SQL DDL Scripts

```sql
CREATE TABLE Users (
    UserID INT PRIMARY KEY AUTO_INCREMENT,
    FirstName VARCHAR(50) NOT NULL,
    LastName VARCHAR(50) NOT NULL,
    EmailAddress VARCHAR(100) UNIQUE NOT NULL,
    Password VARCHAR(255) NOT NULL,
    AccountType ENUM('Retail', 'Institutional') NOT NULL,
    PhoneNumber VARCHAR(15),
    CreatedDate DATETIME DEFAULT CURRENT_TIMESTAMP,
    LastLoginDate DATETIME,
    Status ENUM('Active', 'Inactive') NOT NULL
);

CREATE TABLE Stocks (
    StockID INT PRIMARY KEY AUTO_INCREMENT,
    TickerSymbol VARCHAR(10) UNIQUE NOT NULL,
    CompanyName VARCHAR(255) NOT NULL,
    Exchange ENUM('NYSE', 'NASDAQ') NOT NULL,
    Sector VARCHAR(100),
    Industry VARCHAR(100),
    MarketCap DECIMAL(20, 2),
    Price DECIMAL(10, 2),
    PriceChangePercentage DECIMAL(5, 2),
    CreatedDate DATETIME DEFAULT CURRENT_TIMESTAMP,
    Status ENUM('Active', 'Delisted') NOT NULL
);

CREATE TABLE Transactions (
    TransactionID INT PRIMARY KEY AUTO_INCREMENT,
    UserID INT,
    StockID INT,
    TransactionType ENUM('Buy', 'Sell') NOT NULL,
    Quantity INT NOT NULL,
    PriceAtTransaction DECIMAL(10, 2) NOT NULL,
    TransactionDate DATETIME DEFAULT CURRENT_TIMESTAMP,
    TotalAmount DECIMAL(15, 2) NOT NULL,
    CommissionFee DECIMAL(10, 2),
    NetAmount DECIMAL(15, 2) NOT NULL,
    FOREIGN KEY (UserID) REFERENCES Users(UserID),
    FOREIGN KEY (StockID) REFERENCES Stocks(StockID)
);

CREATE TABLE Watchlists (
    WatchlistID INT PRIMARY KEY AUTO_INCREMENT,
    UserID INT,
    StockID INT,
    CreatedDate DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (UserID) REFERENCES Users(UserID),
    FOREIGN KEY (StockID) REFERENCES Stocks(StockID)
);

CREATE TABLE MarketData (
    MarketDataID INT PRIMARY KEY AUTO_INCREMENT,
    StockID INT,
    Date DATE NOT NULL,
    OpenPrice DECIMAL(10, 2) NOT NULL,
    ClosePrice DECIMAL(10, 2) NOT NULL,
    HighPrice DECIMAL(10, 2) NOT NULL,
    LowPrice DECIMAL(10, 2) NOT NULL,
    Volume BIGINT NOT NULL,
    AdjustedClosePrice DECIMAL(10, 2),
    FOREIGN KEY (StockID) REFERENCES Stocks(StockID)
);

CREATE TABLE News (
    NewsID INT PRIMARY KEY AUTO_INCREMENT,
    StockID INT,
    Title VARCHAR(255) NOT NULL,
    Content TEXT NOT NULL,
    Source VARCHAR(100) NOT NULL,
    PublicationDate DATETIME DEFAULT CURRENT_TIMESTAMP,
    URL VARCHAR(255),
    FOREIGN KEY (StockID) REFERENCES Stocks(StockID)
);
```

### Schema Documentation (schema_doc.md)

# Stock Exchange Database Schema Documentation

## Overview

This document provides a detailed explanation of the database schema designed for the Stock Exchange system. It is constructed to handle user data, stock transactions, watchlists, market data, and stock-related news efficiently.

## Core Entities

1. **Users**
   - Manage user details such as personal information, account type, and authentication data.
   - Passwords are stored as hashed values for security.

2. **Stocks**
   - Stores information about the stocks available in the market, including their current price and trading status.
   - Each stock entry is associated with various attributes to provide a comprehensive overview.

3. **Transactions**
   - Records buy/sell transactions performed by users.
   - Contains foreign keys to link to users and stocks, allowing tracking of activities for each stock.

4. **Watchlists**
   - Facilitates the creation of user-specific lists containing stocks of interest.
   - Links users to multiple stocks, allowing personalized monitoring.

5. **MarketData**
   - Captures historical market information for stocks, including open, close, high, low prices, and trading volume.
   - Provides essential data for performance analysis.

6. **News**
   - Stores articles related to stocks, enhancing user awareness of market influences.
   - Each article is associated with its relevant stock.

## Relationships

- Defined relationships maintain data integrity and reflect real-world associations:
  - A user can have multiple transactions and watchlists (1-to-Many).
  - A stock can be involved in multiple transactions, included in many watchlists, and have multiple market data entries and news articles (1-to-Many).

## Design Choices

- **Normalization**: The database schema follows normalization principles to eliminate data redundancy and improve data integrity.
- **Indices**: It is recommended to create indices on frequently accessed columns, such as `EmailAddress`, `TickerSymbol`, and `TransactionDate`, to enhance performance.
- **Security**: Special attention has been paid to the secure handling of user passwords through hashing and using ENUMs for status fields to ensure data consistency.

This schema provides a robust foundation for scaling, accommodating future implementations such as audit trails and advanced reporting functionalities.

``` 

All files above can be saved appropriately for later use as specified in your requirements.