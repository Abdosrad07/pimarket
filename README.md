# Pi Market - Marketplace for Pi Network

A production-ready Django marketplace application for buying and selling goods/services with Pi Network cryptocurrency and fiat payments. Built for the Pi Network Hackathon.

## 🚀 Features

- **User Authentication**: Phone number-based authentication with OTP verification
- **Multi-currency Support**: Accept both fiat (Stripe) and Pi cryptocurrency payments
- **Escrow System**: Built-in escrow to protect buyers and sellers
- **Shop Management**: Create and manage online stores
- **Product Catalog**: Support for both physical and digital products
- **Order Management**: Complete order lifecycle from creation to delivery
- **Dispute Resolution**: Built-in dispute management system
- **Geolocation**: Location-based product discovery
- **RESTful API**: Complete API with Django REST Framework
- **Async Tasks**: Celery for background processing
- **Docker Ready**: Complete Docker setup for easy deployment

## 📋 Prerequisites

- Docker & Docker Compose
- Python 3.10+ (for local development)
- PostgreSQL 15
- Redis 7

## 🔧 Quick Start

### 1. Clone the Repository

```bash
git clone <your-repo-url>
cd pimarket
```

### 2. Configure Environment Variables

Copy the example environment file and configure it:

```bash
cp .env.example .env
```

**⚠️ IMPORTANT: Fill in the following API keys in `.env`:**

#### Stripe (Fiat Payments)
Get your keys from https://dashboard.stripe.com/test/apikeys
```
STRIPE_SECRET_KEY=sk_test_YOUR_STRIPE_SECRET_KEY_HERE
STRIPE_PUBLISHABLE_KEY=pk_test_YOUR_STRIPE_PUBLISHABLE_KEY_HERE
STRIPE_WEBHOOK_SECRET=whsec_YOUR_WEBHOOK_SECRET_HERE
```

#### Pi Network (Optional - Mock by default)
Get credentials from https://developers.minepi.com/
```
PI_API_KEY=your_pi_api_key_here
PI_API_SECRET=your_pi_api_secret_here
PI_WEBHOOK_SECRET=your_pi_webhook_secret_here
```

#### SMS Provider (Choose one)
**Twilio** (https://console.twilio.com/):
```
SMS_PROVIDER=twilio
TWILIO_ACCOUNT_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_PHONE_NUMBER=+1234567890
```

**MTN API** (Alternative):
```
SMS_PROVIDER=mtn
MTN_API_KEY=your_mtn_api_key
MTN_API_SECRET=your_mtn_api_secret
```

**For Testing** (No real SMS):
```
SMS_PROVIDER=mock
```

### 3. Build and Start Containers

```bash
docker-compose up --build
```

This will start:
- PostgreSQL database (port 5432)
- Redis (port 6379)
- Django application (port 8000)
- Celery worker
- Celery beat (scheduler)
- Nginx (port 80)

### 4. Run Migrations

```bash
docker-compose exec django python manage.py migrate
```

### 5. Create Superuser

```bash
docker-compose exec django python manage.py createsuperuser --phone_number=+1234567890 --display_name="Admin"
```

### 6. Load Demo Data

```bash
docker-compose exec django python manage.py seed_demo_data
```

This creates:
- 2 users (buyer and seller)
- 2 shops
- 6 products (physical and digital)
- Product categories
- 1 sample order

**Demo Credentials:**
- Buyer: `+1234567890` / `password123`
- Seller: `+0987654321` / `password123`

### 7. Access the Application

- **API**: http://localhost:8000/api/
- **API Documentation**: http://localhost:8000/api/docs/
- **Admin Panel**: http://localhost:8000/admin/

## 📚 API Endpoints

### Authentication
- `POST /api/accounts/register/` - Register new user
- `POST /api/accounts/send-otp/` - Send OTP to phone
- `POST /api/accounts/verify-otp/` - Verify OTP and get JWT token
- `POST /api/accounts/token/refresh/` - Refresh JWT token
- `GET/PUT /api/accounts/profile/` - Get/update user profile
- `POST /api/accounts/update-location/` - Update user location

### Shops
- `GET /api/shops/` - List all shops
- `POST /api/shops/` - Create a shop (authenticated)
- `GET /api/shops/{id}/` - Get shop details
- `GET /api/shops/{id}/products/` - List shop products
- `POST /api/shops/{id}/products/` - Create product (shop owner)

### Products
- `GET /api/shops/products/` - List all products (with filters)
  - Query params: `?lat=40.7128&lng=-74.0060&category=1&q=search`
- `GET /api/shops/products/{id}/` - Get product details
- `PUT /api/shops/products/{id}/update/` - Update product (owner)

### Orders
- `POST /api/shops/orders/create/` - Create order
- `GET /api/shops/orders/{id}/` - Get order details
- `GET /api/shops/buyer/orders/` - List buyer's orders
- `GET /api/shops/seller/orders/` - List seller's orders
- `POST /api/shops/orders/{id}/confirm-delivery/` - Buyer confirms delivery
- `POST /api/shops/orders/{id}/mark-shipped/` - Seller marks as shipped

### Payments
- `POST /api/payments/create/{order_id}/` - Create payment for order
- `POST /api/payments/confirm/stripe/` - Confirm Stripe payment
- `GET /api/payments/{id}/status/` - Get payment status

### Disputes
- `POST /api/shops/disputes/open/` - Open a dispute
- `GET /api/shops/disputes/` - List disputes
- `GET /api/shops/disputes/{id}/` - Get dispute details
- `POST /api/shops/disputes/{id}/messages/` - Add message to dispute

### Webhooks (for providers)
- `POST /webhooks/stripe/` - Stripe webhook
- `POST /webhooks/pi/` - Pi Network webhook

## 🧪 Testing Guide

### 1. Test User Registration & OTP

```bash
# Register a new user
curl -X POST http://localhost:8000/api/accounts/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "phone_number": "+1111111111",
    "display_name": "Test User"
  }'

# Check console output for OTP (mock SMS)
# Verify OTP
curl -X POST http://localhost:8000/api/accounts/verify-otp/ \
  -H "Content-Type: application/json" \
  -d '{
    "phone_number": "+1111111111",
    "otp": "123456"
  }'
```

### 2. Test Shop & Product Creation

```bash
# Create a shop (use JWT token from login)
curl -X POST http://localhost:8000/api/shops/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Shop",
    "description": "Test shop",
    "address_text": "123 Main St",
    "latitude": 40.7128,
    "longitude": -74.0060
  }'

# Create a product
curl -X POST http://localhost:8000/api/shops/1/products/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test Product",
    "description": "A test product",
    "price_fiat": "99.99",
    "price_pi": "31.41",
    "stock": 10,
    "is_digital": false
  }'
```

### 3. Test Order Creation (Physical Product)

```bash
# Create an order
curl -X POST http://localhost:8000/api/shops/orders/create/ \
  -H "Authorization: Bearer BUYER_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "items": [
      {
        "product_id": 1,
        "quantity": 2
      }
    ],
    "currency": "fiat",
    "shipping_address": "456 Buyer St, New York, NY",
    "shipping_latitude": 40.7128,
    "shipping_longitude": -74.0060
  }'
```

### 4. Test Payment (Stripe Mock)

```bash
# Create Stripe payment
curl -X POST http://localhost:8000/api/payments/create/1/ \
  -H "Authorization: Bearer BUYER_JWT_TOKEN" \
  -H "Content-Type: application/json"

# Note: In real scenario, client would complete payment via Stripe.js
# For testing, you can use Stripe test cards:
# Card: 4242 4242 4242 4242
# Expiry: Any future date
# CVC: Any 3 digits
```

### 5. Test Pi Payment Simulation

```bash
# Create Pi payment
curl -X POST http://localhost:8000/api/payments/create/1/ \
  -H "Authorization: Bearer BUYER_JWT_TOKEN" \
  -H "Content-Type: application/json"

# Simulate Pi payment completion
docker-compose exec django python manage.py simulate_pi_payment --order 1
```

### 6. Test Digital Product Auto-Release

For digital products, the escrow is automatically released after payment:

```bash
# Order should automatically move to 'released' status
curl -X GET http://localhost:8000/api/shops/orders/1/ \
  -H "Authorization: Bearer BUYER_JWT_TOKEN"
```

### 7. Test Physical Product Workflow

```bash
# Seller marks as shipped
curl -X POST http://localhost:8000/api/shops/orders/1/mark-shipped/ \
  -H "Authorization: Bearer SELLER_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "tracking_number": "TRACK123",
    "carrier": "DHL"
  }'

# Buyer confirms delivery
curl -X POST http://localhost:8000/api/shops/orders/1/confirm-delivery/ \
  -H "Authorization: Bearer BUYER_JWT_TOKEN"

# This triggers escrow release
```

## 🧪 Running Tests

```bash
# Run all tests
docker-compose exec django pytest

# Run with coverage
docker-compose exec django pytest --cov=apps --cov-report=html

# Run specific test file
docker-compose exec django pytest apps/accounts/tests.py

# Run linting
docker-compose exec django flake8 apps/
docker-compose exec django black --check apps/
docker-compose exec django isort --check apps/
```

## 📱 Webhook Setup

### Stripe Webhooks

1. Go to https://dashboard.stripe.com/test/webhooks
2. Click "Add endpoint"
3. URL: `https://your-domain.com/webhooks/stripe/`
4. Select events:
   - `payment_intent.succeeded`
   - `payment_intent.payment_failed`
   - `charge.captured`
   - `charge.refunded`
5. Copy webhook secret to `.env` as `STRIPE_WEBHOOK_SECRET`

### Pi Network Webhooks

1. Go to Pi Network Developer Portal
2. Configure webhook URL: `https://your-domain.com/webhooks/pi/`
3. Copy webhook secret to `.env` as `PI_WEBHOOK_SECRET`

### Testing Webhooks Locally

Use Stripe CLI for local testing:

```bash
# Install Stripe CLI
stripe listen --forward-to localhost:8000/webhooks/stripe/

# Trigger test event
stripe trigger payment_intent.succeeded
```

## 🗄️ Database Schema

```
Users (Custom User Model)
├── phone_number (unique)
├── display_name
├── is_phone_verified
└── avatar

PhoneOTP
├── phone_number
├── otp
├── expires_at
└── attempts

UserLocation
├── user (FK)
├── latitude
├── longitude
└── is_current

Shops
├── owner (FK to User)
├── name
├── latitude/longitude
└── verified

Products
├── shop (FK)
├── category (FK)
├── price_fiat
├── price_pi
├── is_digital
└── stock

Orders
├── buyer (FK to User)
├── shop (FK)
├── status (created → pending_payment → paid_in_escrow → shipped → delivered → released)
└── total_fiat/total_pi

OrderItems
├── order (FK)
├── product (FK)
└── quantity

Payments
├── order (FK)
├── provider (stripe/pi/mock)
├── status
└── metadata

EscrowTransaction
├── payment (FK)
├── status (held/released/refunded)
└── auto_release_date

Disputes
├── order (FK)
├── raised_by (FK to User)
└── status
```

## 🚀 Production Deployment

### Environment Variables for Production

Update `.env` for production:

```bash
DEBUG=False
SECRET_KEY=<generate-strong-secret-key>
ALLOWED_HOSTS=your-domain.com,www.your-domain.com

# Use production database
DATABASE_URL=postgresql://user:password@prod-db:5432/pimarket_prod

# Enable security
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True

# Use live Stripe keys
STRIPE_SECRET_KEY=sk_live_YOUR_LIVE_KEY
STRIPE_PUBLISHABLE_KEY=pk_live_YOUR_LIVE_KEY

# Use real Pi Network credentials
PI_API_KEY=your_production_pi_key
```

### Deployment Steps

1. **Set up server** (Ubuntu 20.04+)
   ```bash
   apt update
   apt install docker docker-compose nginx certbot python3-certbot-nginx
   ```

2. **Clone repository**
   ```bash
   git clone <your-repo> /var/www/pimarket
   cd /var/www/pimarket
   ```

3. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with production values
   nano .env
   ```

4. **Set up SSL with Let's Encrypt**
   ```bash
   certbot --nginx -d your-domain.com
   ```

5. **Start services**
   ```bash
   docker-compose -f docker-compose.prod.yml up -d
   ```

6. **Run migrations**
   ```bash
   docker-compose exec django python manage.py migrate
   docker-compose exec django python manage.py collectstatic --noinput
   ```

7. **Create superuser**
   ```bash
   docker-compose exec django python manage.py createsuperuser
   ```

## 📊 Monitoring & Logs

```bash
# View logs
docker-compose logs -f django
docker-compose logs -f celery_worker

# Check service status
docker-compose ps

# Restart services
docker-compose restart django
```

## 🔒 Security Checklist

- [x] HTTPS enforced in production
- [x] CSRF protection enabled
- [x] Rate limiting on sensitive endpoints
- [x] JWT token authentication
- [x] Webhook signature verification
- [x] SQL injection protection (Django ORM)
- [x] XSS protection
- [x] Input validation

## 🐛 Troubleshooting

### Database connection issues
```bash
docker-compose exec django python manage.py dbshell
```

### Redis connection issues
```bash
docker-compose exec redis redis-cli ping
```

### Celery not processing tasks
```bash
docker-compose logs celery_worker
docker-compose restart celery_worker celery_beat
```

### SMS not sending
Check `SMS_PROVIDER` in `.env` and verify credentials.

## 📝 TODO (The 20% You Need to Complete)

### Required for Production

1. **API Keys Configuration**
   - [ ] Add real Stripe live keys
   - [ ] Add Pi Network production API credentials
   - [ ] Configure SMS provider (Twilio/MTN) credentials

2. **Pi Network Integration**
   - [ ] Replace mock Pi provider with real API implementation
   - [ ] Test Pi payment flow end-to-end
   - [ ] Verify Pi webhook signature logic

3. **Domain & SSL**
   - [ ] Set up domain name
   - [ ] Configure ALLOWED_HOSTS in production
   - [ ] Set up SSL certificate (Let's Encrypt)

4. **Notifications**
   - [ ] Implement email notifications (optional)
   - [ ] Test SMS delivery with real provider

5. **Monitoring**
   - [ ] Set up error tracking (Sentry)
   - [ ] Configure logging aggregation
   - [ ] Set up uptime monitoring

6. **Performance**
   - [ ] Configure CDN for static/media files
   - [ ] Optimize database queries
   - [ ] Set up caching strategy

## 📄 License

MIT License

## 🤝 Contributing

This is a hackathon project. Contributions welcome!

## 💬 Support

For issues, please open a GitHub issue or contact the maintainers.

---

**Built with ❤️ for Pi Network Hackathon**