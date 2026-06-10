# 🚀 Darine Backend

Backend service for **Darine**, a modern trading platform for **Gold (Melted), Silver, and Cryptocurrencies**.

---

## 📌 About the Project

Darine is a financial platform that allows users to:

* Buy & Sell Gold (Melted), Silver
* Trade based on real-time market prices
* Manage wallet balance (IRR)
* Store physical gold in warehouse
* Track transactions securely

---

## 🧠 Core Features

* 🔐 User Authentication & KYC Verification
* 💰 Wallet System (IRR balance + blocked funds)
* 🪙 Gold Inventory Management
* 📈 Market Orders & Limit Orders
* 🔄 Transaction Engine (Buy/Sell Matching)
* 🏦 Warehouse Management
* 📊 Real-time Market Price Tracking
* 🧾 Full Audit Logging System

---

## 🏗️ Architecture

* RESTful API
* Modular Design
* Scalable Transaction Handling
* Secure Financial Operations

---

## 🗂️ Main Modules

* Users
* Wallet
* Orders (Buy/Sell)
* Transactions
* Inventory (Gold/Silver)
* Market Price
* Audit Logs
* Warehouse

---

## ⚙️ Tech Stack (Suggested)

* Backend: Laravel / Django
* Database: MySQL / PostgreSQL
* Queue: Redis
* Authentication: JWT / Sanctum
* Storage: Local / S3

---

## 📦 Installation

```bash
git clone https://github.com/Asajadafsar/darine-backend.git
cd darine-backend
```

```bash
# install dependencies
composer install
# or
pip install -r requirements.txt
```

```bash
# run migrations
php artisan migrate
# or
python manage.py migrate
```

```bash
# run server
php artisan serve
# or
python manage.py runserver
```

---

## 🔐 Security Considerations

* KYC Verification required
* Transaction validation layers
* Wallet balance locking system
* Audit logging for all sensitive actions

---

## 📊 Database Design

The system is built around key entities:

* User
* Wallet
* GoldInventory
* BuyOrder
* SellOrder
* Transaction
* WalletTransaction
* MarketPrice
* Warehouse
* AuditLog

---

## 🔄 Business Logic

### Buy Flow

1. Create Buy Order
2. Lock wallet balance
3. Match with Sell Order
4. Execute Transaction
5. Update inventory
6. Release extra funds

### Sell Flow

1. Create Sell Order
2. Validate inventory
3. Execute Transaction
4. Update wallet balance

---

## 🧪 Testing

```bash
php artisan test
# or
pytest
```

---

## 👨‍💻 Author

Developed with ❤️ by Sajad Afsar

---

## 📄 License

MIT License
