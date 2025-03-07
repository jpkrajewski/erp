# ERP System

## Running the Application
```
docker compose up -f compose.yml up --build
```

Login using admin/admin credentials at http://localhost:8000/accounts/login

## Running Tests
```bash
python manage.py test --settings=erp_system.settings.test
```

## Development Environment
```bash
docker compose -f compose.dev.yml up --build
```

with hotreload

# System Overview

## Technologies Used

- **Celery**: For handling background tasks.
- **Django**: Web framework used for building the application.
- **Django REST Framework**: For API development.
- **Redis**: Used as a message broker for Celery.
- **PostgreSQL**: Database for storing application data.
- **Docker**: For containerization of applications.
- **Docker Compose**: To manage multi-container applications.

## Authentication & Authorization
API is secured using JWT authentication.
App is secured using Django's built-in authentication system. (Session based)

## Product & Inventory Management System

### Product Management
- **API Endpoint**: `/api/products/`
  - **CRUD Operations**: Create, Read, Update, Delete products.
  - **Features**:
    - Display products with their preferred supplier.
    - Show current stock levels for each product.

### Supplier Management
- **API Endpoint**: `/api/suppliers/`
  - **CRUD Operations**: Create, Read, Update, Delete suppliers.
  - **Features**:
    - List suppliers along with their associated products.

### Inventory Movement
- **API Endpoint**: `/api/inventory/move`
  - **Functionality**: Move products between warehouses.
  - **Stock Level Monitoring**:
    - Monitor stock levels in warehouses.
    - Send email alerts if stock falls below the minimum threshold.

### Currency Exchange Rate Updates
- **Functionality**: Regularly fetch and update the system with current exchange rates from an external API.

## Manufacturing Module

### Manufacturing Orders
- **API Endpoint**: `/api/manufacturing-orders/`
  - **CRUD Operations**: Create, Read, Update, Delete manufacturing orders.
  - **Automation**: Assign manufacturing steps automatically based on the ordered product.

### Workstation Management
- **API Endpoint**: `/api/workstations/`
  - **CRUD Operations**: Create, Read, Update, Delete workstations.
  - **Features**:
    - Display workstations with the total number of ongoing shifts and absent workers.
    - Detailed view of workers assigned to each workstation.

### Notifications
- **Functionality**: Send email notifications for completed or canceled manufacturing orders.

## Sales & Order Management Module

### User Authentication
- **Endpoints**:
  - `/accounts/login`: User login functionality.
  - `/accounts/profile`: Manage user profiles.

### Sales Orders
- **Endpoint**: `/app/salesorders/create-form/`
  - **Functionality**: Create and manage sales orders.

### Invoice Management
- **Endpoints**:
  - `/app/invoices/create-form/`: Create invoices and generate PDFs in the background.
  - `/app/invoices/list/`: List all invoices and allow users to download them.

## Middlewares

### Timeout Middleware
- **Functionality**: Automatically log out users after 15 minutes of inactivity.

### Performance Middleware
- **Functionality**: Log any requests that take longer than 15 seconds to process.
