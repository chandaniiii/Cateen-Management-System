# 🍽️ Campus Canteen Management System

A modern, full-stack, responsive web application for college and university canteens. Built with **Python Flask**, **SQLAlchemy ORM**, **PostgreSQL Relational Database**, and modern **HTML5 / CSS3 / Vanilla JavaScript**.

---

## 🚀 Key Features by User Role

### 🎓 1. Student Portal

- **Browse Menu**: Category filters (Breakfast, Snacks, Main Course, Fast Food, Drinks, Desserts) with live real-time search.
- **Realistic NPR Pricing**: Momo (Rs. 120), Chowmein (Rs. 100), Samosa (Rs. 30), Chiya (Rs. 40), Coffee (Rs. 80), etc.
- **Food Details**: Full dish descriptions, live stock availability indicators, customer review ratings, and dynamic quantity selector.
- **Cart & Checkout**: Real-time cart calculations, subtotal, service charges, customer info auto-fill, pickup scheduling (ASAP or scheduled time), and simulated payment methods (**Cash on Pickup**, **eSewa**, **Khalti**, **Fonepay / QR**).
- **Live Order Tracker**: Visual animated timeline tracker (*Pending → Confirmed → Preparing → Ready → Completed*) with real-time status updates.
- **Order History & Receipts**: Itemized past order receipts with print option.
- **Ratings & Reviews**: 5-star interactive rating system with feedback comments for completed orders.

### 👨‍🍳 2. Canteen Staff Portal

- **Operational Dashboard**: Real-time KPI metrics (Today's Orders, Pending, Preparing, Completed, Today's Revenue).
- **Status Workflow Pipeline**:

  **Pending → Confirmed → Preparing → Ready → Completed**

  **Pending / Confirmed → Cancelled with Auto-Restock**

- **Quick Action Buttons**: Accept order, start preparing, mark ready, and complete with confirmation prompts.
- **Filtered Order Tabs**: Dedicated views for New, Preparing, Ready, Completed, and All orders.

### ⚙️ 3. Administrator Console

- **Executive Analytics Dashboard**: Interactive **Chart.js** graphs for:
  - 📈 *Daily Sales Revenue (Past 7 Days)*
  - 📊 *Weekly Order Volumes*
  - 🍩 *Top Selling Menu Items*
  - 📊 *Revenue Breakdown by Category*
- **Menu Management**: Full CRUD (Add, Edit, Delete) for dishes with price in NPR, stock limits, and image uploads.
- **Category Management**: Create, edit via popup modal, and delete categories.
- **Inventory & Stock Control**: Real-time stock counts, minimum stock alert thresholds, low-stock warnings, and inline restock updates.
- **User Account Management**: Manage student and staff accounts, toggle role assignments (Student / Staff / Admin), and activate/deactivate accounts.
- **Review Moderation**: Moderate student reviews and toggle visibility on public dish pages.

---

## 🛠️ Technology Stack

| Layer | Technologies |
|---|---|
| **Frontend** | HTML5, Modern CSS3 (CSS Variables, Flexbox, CSS Grid), Vanilla JavaScript (ES6+), FontAwesome Icons, Chart.js |
| **Backend** | Python 3.10+, Flask 3.0, Werkzeug (Password Hashing & Security) |
| **Database** | PostgreSQL 17 with psycopg driver and Flask-SQLAlchemy ORM |
| **Authentication** | Flask session-based auth with HTTPOnly cookies, role-based access control (RBAC) decorators |

---

## 📂 Project Structure

```text
canteen-management/

│
├── app.py                      # Flask Application Factory & Database Seeder
├── config.py                   # Environment & PostgreSQL Database Configuration
├── requirements.txt            # Python Dependencies
├── .env.example                # Sample Environment Variables
├── README.md                   # Complete Documentation & Guide
│
├── database/
│   └── schema.sql              # Database DDL Tables & Sample Seed SQL Script
│
├── models/
│   ├── __init__.py             # Database Instance & Model Exporter
│   ├── user.py                 # User Model (Student, Staff, Admin)
│   ├── category.py             # Food Categories Model
│   ├── menu_item.py            # Menu Items & Inventory Model
│   ├── order.py                # Orders & Order Items Model
│   └── review.py               # Reviews & Star Ratings Model
│
├── routes/
│   ├── main.py                 # Public Landing Page & About
│   ├── auth.py                 # Login, Register, Logout
│   ├── student.py              # Student Dashboard, Menu, Cart, Orders, Reviews
│   ├── staff.py                # Kitchen Staff Dashboard & Order Pipeline
│   ├── admin.py                # Admin Dashboard, Menu, Users, Inventory, Reports
│   └── api.py                  # JSON REST Endpoints
│
├── utils/
│   ├── decorators.py           # Login & Role-Based Access Control Decorators
│   └── helpers.py              # File Upload & Image Helper
│
├── templates/
│   ├── base.html               # Master Layout Template
│   ├── dashboard_base.html     # Portal Topbar & Sidebar Layout
│   ├── index.html              # Public Landing Page
│   ├── about.html              # About Canteen Page
│   ├── login.html              # Sign In Page
│   ├── register.html           # Student Registration Page
│   ├── partials/               # Reusable Nav, Sidebar, Footer, Status Actions
│   ├── student/                # Student Dashboard, Menu, Cart, Checkout, Tracking
│   ├── staff/                  # Staff Dashboard, Orders, Order Details
│   ├── admin/                  # Admin Dashboard, Menu CRUD, Inventory, Reports
│   └── errors/                 # 404 & 500 Error Pages
│
└── static/
    ├── css/
    │   └── style.css           # Modern Responsive Food Platform Stylesheet
    ├── js/
    │   └── script.js           # Client-Side Interactivity, Cart & Real-Time Tracking
    └── images/                 # Dedicated Dish SVGs & Uploads Directory
```

---

## ⚙️ Installation & Setup Guide

### 1. Prerequisites

- **Python 3.10+**
- **PostgreSQL 17**
- **pip**
- **git**
- **VS Code** or another code editor

---

### 2. Clone and Setup Virtual Environment

Navigate to the project directory:

```bash
cd "canteen management system"
```

Create a virtual environment:

```bash
python3 -m venv .venv
```

Activate the virtual environment on macOS/Linux:

```bash
source .venv/bin/activate
```

On Windows:

```bash
.venv\Scripts\activate
```

---

### 3. Install Python Dependencies

Install all required Python packages:

```bash
pip install -r requirements.txt
```

The main database dependencies are:

```text
Flask-SQLAlchemy
psycopg[binary]
```

---

### 4. Configure Environment Variables

Create a `.env` file in the project root:

```bash
touch .env
```

Configure it for PostgreSQL:

```ini
SECRET_KEY=your_secret_key_change_in_production

DB_HOST=localhost
DB_PORT=5432
DB_USER=chandani
DB_PASSWORD=
DB_NAME=canteen_management
```

For production, use a strong randomly generated `SECRET_KEY` and a secure PostgreSQL password.

---

### 5. PostgreSQL Database Setup

Make sure PostgreSQL 17 is installed and running.

On macOS with Homebrew:

```bash
brew services start postgresql@17
```

Open PostgreSQL:

```bash
psql postgres
```

Create the application database:

```sql
CREATE DATABASE canteen_management;
```

Connect to the database:

```sql
\c canteen_management
```

Exit PostgreSQL:

```sql
\q
```

The Flask application automatically creates the required database tables and seeds the database with demo data when it starts.

---

### 6. Run the Application

Make sure the virtual environment is activated:

```bash
source .venv/bin/activate
```

Start the Flask application:

```bash
python app.py
```

The application will be available locally at:

```text
http://127.0.0.1:5001
```

For access from another device on the same local network, use the Mac's local IP address:

```text
http://YOUR_LOCAL_IP:5001
```

For example:

```text
http://192.168.212.241:5001
```

The other device must be connected to the same local network as the computer running the Flask application.

---

## 📡 REST API Endpoints

| Method | Endpoint | Access | Description |
|---|---|---|---|
| `GET` | `/api/menu` | Public / Student | Get active menu items and categories with search & filter |
| `GET` | `/api/menu/<id>` | Public / Student | Get details of a single dish |
| `POST` | `/api/menu` | Admin | Create a new food dish |
| `PUT` | `/api/menu/<id>` | Admin | Update dish details and stock |
| `DELETE` | `/api/menu/<id>` | Admin | Delete a food item |
| `GET` | `/student/api/cart` | Student | Get current session cart |
| `POST` | `/student/api/cart/add` | Student | Add item to cart |
| `PUT` | `/student/api/cart/update` | Student | Update item quantity in cart |
| `DELETE` | `/student/api/cart/remove` | Student | Remove item from cart |
| `POST` | `/student/api/reviews` | Student | Submit rating & review for completed order |
| `GET` | `/api/orders` | Auth | List user orders or all orders for Staff/Admin |
| `GET` | `/api/orders/<id>` | Auth | Get order details |
| `PUT` | `/api/orders/<id>/status` | Staff / Admin | Update order status in kitchen pipeline |
| `GET` | `/admin/api/reports` | Admin | Analytics data for Chart.js dashboard |
| `GET` | `/admin/api/users` | Admin | List all registered users |
| `GET` | `/admin/api/inventory` | Admin | Inventory stock data |

---

## 🔒 Security Best Practices Implemented

- **Password Security**: Passwords are hashed with `werkzeug.security`. Plain-text passwords are never stored.
- **Role-Based Authorization**: Distinct decorators (`@login_required`, `@role_required`, `@api_role_required`) enforce student, staff, and admin privilege boundaries.
- **SQL Injection Prevention**: SQLAlchemy parameterized queries are used across database operations.
- **Session Protection**: HTTPOnly cookies with SameSite protection are configured for session security.
- **Input Sanitization**: File upload validation with UUID renaming and secure filename checking.

---

## 🗄️ Database

The application uses **PostgreSQL 17** as its relational database.

Database configuration:

```text
Host:     localhost
Port:     5432
Database: canteen_management
User:     chandani
Driver:   psycopg
```

The application uses **Flask-SQLAlchemy** as the ORM layer and `psycopg` as the PostgreSQL database driver.

Database tables are created automatically through SQLAlchemy when the Flask application starts.

---

## 🌐 Local Network Access

The Flask application is configured to listen on all network interfaces:

```python
app.run(
    debug=True,
    host="0.0.0.0",
    port=5001
)
```

This allows other devices on the same local network to access the application.

For example, if the computer running Flask has the local IP:

```text
192.168.212.241
```

other devices on the same network can open:

```text
http://192.168.212.241:5001
```

The Flask terminal must remain running for other devices to access the application.

---

## 📄 License & Attribution

Designed and built for university campus dining. Open-source educational project.