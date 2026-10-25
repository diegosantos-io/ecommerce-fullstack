# E-commerce Full Stack

A full-stack e-commerce application built with **FastAPI, React, PostgreSQL, and Stripe**. This project demonstrates REST API development, authentication, shopping cart management, payment processing, email notifications, database migrations, and automated testing.

The application includes a responsive product catalog, product images, cart management, Stripe Checkout, and payment confirmation workflows.

## Application Screenshots

### Login

User authentication interface.

![E-commerce login page](docs/images/login.png)

### Product Catalog

Browse gaming products, view product details and prices, and add items to the shopping cart.

![E-commerce product catalog](docs/images/catalog.png?v=2)

### Shopping Cart

Review selected products, update quantities, remove items, and check the order subtotal.

![E-commerce shopping cart](docs/images/cart.png?v=2)

### Product Added to Cart

Visual feedback after adding a product to the shopping cart.

![Product added to cart confirmation](docs/images/cart-feedback.png?v=2)

### Stripe Checkout

Secure checkout experience using Stripe test mode.

![Stripe checkout page](docs/images/stripe-checkout.png)

### Payment Confirmation

Payment success page after completing a test transaction.

![Payment success page](docs/images/payment-success.png)

## Features

- User registration and JWT-based authentication
- Product catalog with product images and pricing
- Product and category management
- Shopping cart management and quantity updates
- Order creation and order status tracking
- Stripe Checkout integration
- Stripe webhook processing and idempotency handling
- Email notifications and background email processing
- Password reset workflow
- PostgreSQL database integration
- Database schema migrations with Alembic
- Automated backend and frontend tests
- Responsive user interface

## Tech Stack

### Backend

- Python
- FastAPI
- SQLAlchemy
- PostgreSQL
- Alembic
- Pydantic
- JWT authentication
- Stripe API
- Pytest

### Frontend

- React
- Vite
- JavaScript
- HTML
- CSS
- Automated component tests

### Infrastructure and Integrations

- Docker and Docker Compose
- Stripe test mode
- SMTP email integration
- Git and GitHub

## Project Structure

```text
ecommerce-fullstack/
├── backend/
│   ├── alembic/
│   ├── app/
│   ├── tests/
│   ├── .env.example
│   ├── docker-compose.yml
│   └── requirements.txt
├── frontend/
│   ├── public/
│   │   └── images/
│   ├── src/
│   ├── package.json
│   └── vite.config.js
└── docs/
    └── images/
        ├── login.png
        ├── catalog.png
        ├── cart.png
        ├── cart-feedback.png
        ├── stripe-checkout.png
        └── payment-success.png
```

## Getting Started

### Prerequisites

- Python 3.12 or another version supported by the project dependencies
- Node.js and npm
- Docker Desktop
- A Stripe account for payment testing
- SMTP credentials for email functionality

### 1. Clone the Repository

```bash
git clone https://github.com/diegosantos-io/ecommerce-fullstack.git
cd ecommerce-fullstack
```

### 2. Configure the Backend

Open a terminal in the project root and run:

```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Configure your local `.env` file with the appropriate database connection, JWT secret, Stripe test credentials, and SMTP settings.

Use unique local credentials and keep your `.env` file private. Never commit real secrets to GitHub.

### 3. Start PostgreSQL

From the `backend` directory, validate the Docker Compose configuration:

```bash
docker compose config --quiet
```

Start the database service:

```bash
docker compose up -d db
```

Ensure that the database is running and that the connection settings match your local `.env` configuration.

Apply database migrations:

```bash
alembic upgrade head
```

### 4. Start the Backend API

Keep the backend virtual environment activated and run:

```bash
python -m uvicorn app.main:app --reload
```

The API should be available at:

- API: http://localhost:8000
- Interactive API documentation: http://localhost:8000/docs

### 5. Start the Frontend

Open a separate terminal in the project root:

```powershell
cd frontend
npm install
npm run dev
```

Open the local URL displayed by Vite.

## Stripe Payment Testing

The application integrates with Stripe for checkout and payment processing.

For local testing:

1. Configure Stripe test-mode credentials in the backend environment.
2. Configure a webhook endpoint using the payment webhook route implemented by the backend.
3. Use the Stripe CLI or Stripe Dashboard to deliver test webhook events, according to your setup.
4. Verify the order status and email confirmation after a successful test payment.

The backend includes webhook idempotency handling intended to prevent duplicate processing of the same event.

**Use test credentials and test payment methods during development. Never expose production secret keys or commit credentials to version control.**

## Running Tests

### Backend Tests

From the `backend` directory, activate the virtual environment and run:

```bash
python -m pytest tests -v
```

The backend test suite passed **40 tests** in the latest verified test run.

Some integration tests require a dedicated test database. Configure the test environment according to the project settings and never run tests against a production database.

### Frontend Tests

From the project root, run:

```bash
npm --prefix ./frontend test
```

The frontend test suite passed **10 tests** in the latest verified test run.

### Frontend Quality Checks

Run the linter:

```bash
npm --prefix ./frontend run lint
```

Build the frontend for production:

```bash
npm --prefix ./frontend run build
```

Both checks passed in the latest verified run.

## Security Considerations

- Keep `.env` files and credentials out of version control.
- Use strong, unique secrets for JWT authentication.
- Use Stripe test credentials during development.
- Keep SMTP credentials private.
- Use a dedicated test database for automated tests.
- Review environment variables and production settings before deployment.

## Roadmap

- Configure and validate a production deployment.
- Publish a live demo.
- Expand API documentation where needed.
- Continue improving test coverage and security checks.

## Author

**Diego Santos**

- GitHub: https://github.com/diegosantos-io
- LinkedIn: https://www.linkedin.com/in/diego-santos-3352a92a8/

---

This project was developed for learning and portfolio purposes, demonstrating full-stack development, payment integration, database management, and automated testing.
