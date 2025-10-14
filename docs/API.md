# Pi Market API Documentation

Base URL: `http://localhost:8000/api/`

All endpoints require `Content-Type: application/json` header.

Authenticated endpoints require `Authorization: Bearer {token}` header.

## Authentication Endpoints

### Register New User
```http
POST /api/accounts/register/
```

**Request Body:**
```json
{
  "phone_number": "+1234567890",
  "display_name": "John Doe"
}
```

**Response (201):**
```json
{
  "message": "User registered. OTP sent to phone number.",
  "user_id": 1
}
```

### Send OTP
```http
POST /api/accounts/send-otp/
```

**Request Body:**
```json
{
  "phone_number": "+1234567890"
}
```

### Verify OTP
```http
POST /api/accounts/verify-otp/
```

**Request Body:**
```json
{
  "phone_number": "+1234567890",
  "otp": "123456"
}
```

**Response (200):**
```json
{
  "message": "Phone verified successfully",
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user": {
    "id": 1,
    "phone_number": "+1234567890",
    "display_name": "John Doe",
    "is_phone_verified": true
  }
}
```

### Refresh Token
```http
POST /api/accounts/token/refresh/
```

**Request Body:**
```json
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

### Get/Update Profile
```http
GET /api/accounts/profile/
PUT /api/accounts/profile/
```

**Response (GET):**
```json
{
  "id": 1,
  "phone_number": "+1234567890",
  "display_name": "John Doe",
  "avatar": null,
  "is_phone_verified": true,
  "current_location": {
    "latitude": "40.712800",
    "longitude": "-74.006000",
    "city": "New York"
  }
}
```

### Update Location
```http
POST /api/accounts/update-location/
```

**Request Body:**
```json
{
  "latitude": "40.712800",
  "longitude": "-74.006000",
  "city": "New York",
  "country": "USA"
}
```

## Shop Endpoints

### List All Shops
```http
GET /api/shops/
```

**Query Parameters:**
- `search`: Search by name or description
- `ordering`: Sort by field (e.g., `-created_at`)

### Create Shop
```http
POST /api/shops/
```

**Request Body:**
```json
{
  "name": "My Shop",
  "description": "Best products in town",
  "address_text": "123 Main St, New York, NY",
  "latitude": "40.712800",
  "longitude": "-74.006000"
}
```

### Get Shop Details
```http
GET /api/shops/{id}/
```

### Update Shop
```http
PUT /api/shops/{id}/
PATCH /api/shops/{id}/
```

## Product Endpoints

### List All Products
```http
GET /api/shops/products/
```

**Query Parameters:**
- `lat`: User latitude for distance calculation
- `lng`: User longitude for distance calculation
- `category`: Filter by category ID
- `shop`: Filter by shop ID
- `q`: Search in title/description
- `min_price_fiat`: Minimum fiat price
- `max_price_fiat`: Maximum fiat price
- `is_digital`: Filter digital products (true/false)
- `ordering`: Sort by field

**Example:**
```http
GET /api/shops/products/?lat=40.7128&lng=-74.0060&category=1&q=headphones
```

**Response:**
```json
{
  "count": 10,
  "next": "http://localhost:8000/api/shops/products/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "title": "Wireless Headphones",
      "price_fiat": "99.99",
      "price_pi": "31.41",
      "image": "/media/products/headphones.jpg",
      "shop_name": "Tech Paradise",
      "category_name": "Electronics",
      "in_stock": true,
      "distance": 2.5
    }
  ]
}
```

### Get Product Details
```http
GET /api/shops/products/{id}/
```

### List Shop Products
```http
GET /api/shops/{shop_id}/products/
```

### Create Product (Shop Owner)
```http
POST /api/shops/{shop_id}/products/
```

**Request Body:**
```json
{
  "title": "Wireless Headphones",
  "description": "High-quality Bluetooth headphones",
  "price_fiat": "99.99",
  "price_pi": "31.41",
  "stock": 50,
  "is_digital": false,
  "category_id": 1
}
```

### Update Product
```http
PUT /api/shops/products/{id}/update/
```

## Order Endpoints

### Create Order
```http
POST /api/shops/orders/create/
```

**Request Body:**
```json
{
  "items": [
    {
      "product_id": 1,
      "quantity": 2
    },
    {
      "product_id": 2,
      "quantity": 1
    }
  ],
  "currency": "fiat",
  "shipping_address": "456 Buyer St, New York, NY 10001",
  "shipping_latitude": "40.758900",
  "shipping_longitude": "-73.985100",
  "notes": "Please deliver before 5 PM"
}
```

**Response (201):**
```json
{
  "order": {
    "id": 1,
    "order_number": "ORD-A1B2C3D4E5F6",
    "buyer": {...},
    "shop": {...},
    "items": [...],
    "total_fiat": "199.98",
    "total_pi": "62.82",
    "currency": "fiat",
    "status": "pending_payment",
    "created_at": "2024-01-15T10:30:00Z"
  },
  "message": "Order created successfully"
}
```

### Get Order Details
```http
GET /api/shops/orders/{id}/
```

### List Buyer Orders
```http
GET /api/shops/buyer/orders/
```

### List Seller Orders
```http
GET /api/shops/seller/orders/
```

**Query Parameters:**
- `status`: Filter by status
- `ordering`: Sort by field

### Confirm Delivery (Buyer)
```http
POST /api/shops/orders/{id}/confirm-delivery/
```

**Response:**
```json
{
  "message": "Delivery confirmed",
  "order": {...}
}
```

### Mark as Shipped (Seller)
```http
POST /api/shops/orders/{id}/mark-shipped/
```

**Request Body:**
```json
{
  "tracking_number": "TRACK123456",
  "carrier": "DHL Express"
}
```

## Payment Endpoints

### Create Payment
```http
POST /api/payments/create/{order_id}/
```

**Response (Stripe):**
```json
{
  "payment": {
    "id": 1,
    "provider": "stripe",
    "status": "pending",
    "amount_fiat": "199.98"
  },
  "client_secret": "pi_xxx_secret_xxx",
  "publishable_key": "pk_test_xxx"
}
```

**Response (Pi Network):**
```json
{
  "payment": {
    "id": 1,
    "provider": "pi",
    "status": "pending",
    "amount_pi": "62.82"
  },
  "approval_url": "https://pi.app/approve/pi_mock_xxx",
  "message": "Please approve the payment in your Pi app"
}
```

### Confirm Stripe Payment
```http
POST /api/payments/confirm/stripe/
```

**Request Body:**
```json
{
  "payment_id": 1
}
```

**Response:**
```json
{
  "message": "Payment confirmed and held in escrow",
  "payment": {
    "id": 1,
    "status": "succeeded",
    "escrow": {
      "status": "held",
      "auto_release_date": "2024-01-22T10:30:00Z"
    }
  }
}
```

### Get Payment Status
```http
GET /api/payments/{id}/status/
```

## Dispute Endpoints

### Open Dispute
```http
POST /api/shops/disputes/open/
```

**Request Body:**
```json
{
  "order_id": 1,
  "reason": "Product not as described. Item is damaged."
}
```

**Response:**
```json
{
  "message": "Dispute opened",
  "dispute": {
    "id": 1,
    "order": 1,
    "order_number": "ORD-A1B2C3D4E5F6",
    "raised_by": {...},
    "reason": "Product not as described. Item is damaged.",
    "status": "open",
    "created_at": "2024-01-15T12:00:00Z"
  }
}
```

### List Disputes
```http
GET /api/shops/disputes/
```

### Get Dispute Details
```http
GET /api/shops/disputes/{id}/
```

### Add Message to Dispute
```http
POST /api/shops/disputes/{id}/messages/
```

**Request Body:**
```json
{
  "message": "I apologize for the issue. I will send a replacement."
}
```

## Error Responses

### 400 Bad Request
```json
{
  "error": "Invalid input data",
  "details": {
    "phone_number": ["This field is required"]
  }
}
```

### 401 Unauthorized
```json
{
  "detail": "Authentication credentials were not provided."
}
```

### 403 Forbidden
```json
{
  "detail": "You do not have permission to perform this action."
}
```

### 404 Not Found
```json
{
  "detail": "Not found."
}
```

### 429 Too Many Requests
```json
{
  "detail": "Request was throttled. Expected available in 3600 seconds."
}
```

## Webhook Endpoints

### Stripe Webhook
```http
POST /webhooks/stripe/
```

**Headers:**
- `Stripe-Signature`: Webhook signature

**Events Handled:**
- `payment_intent.succeeded`
- `payment_intent.payment_failed`
- `charge.captured`
- `charge.refunded`

### Pi Network Webhook
```http
POST /webhooks/pi/
```

**Headers:**
- `Pi-Signature`: Webhook signature

**Events Handled:**
- `payment_completed`
- `payment_failed`

## Rate Limits

- **OTP Requests**: 5 per hour per phone number
- **Anonymous API**: 100 requests per hour
- **Authenticated API**: 1000 requests per hour

## Pagination

All list endpoints support pagination:

```json
{
  "count": 100,
  "next": "http://localhost:8000/api/products/?page=2",
  "previous": null,
  "results": [...]
}
```

Query parameters:
- `page`: Page number (default: 1)
- `page_size`: Items per page (default: 20, max: 100)

## Filtering & Ordering

### Filtering
Use query parameters to filter:
```
GET /api/shops/products/?category=1&is_digital=true
```

### Ordering
Use `ordering` parameter:
```
GET /api/shops/products/?ordering=-created_at
```

Use `-` prefix for descending order.

## Testing with cURL

### Complete Flow Example

```bash
# 1. Register
curl -X POST http://localhost:8000/api/accounts/register/ \
  -H "Content-Type: application/json" \
  -d '{"phone_number": "+1234567890", "display_name": "Test User"}'

# 2. Verify OTP (check console for OTP)
curl -X POST http://localhost:8000/api/accounts/verify-otp/ \
  -H "Content-Type: application/json" \
  -d '{"phone_number": "+1234567890", "otp": "123456"}'

# Save the token
TOKEN="your_jwt_token_here"

# 3. Create Shop
curl -X POST http://localhost:8000/api/shops/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Shop",
    "description": "Test shop",
    "address_text": "123 Main St",
    "latitude": "40.7128",
    "longitude": "-74.0060"
  }'

# 4. Create Product
curl -X POST http://localhost:8000/api/shops/1/products/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test Product",
    "description": "A test product",
    "price_fiat": "99.99",
    "price_pi": "31.41",
    "stock": 10
  }'

# 5. Create Order
curl -X POST http://localhost:8000/api/shops/orders/create/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "items": [{"product_id": 1, "quantity": 1}],
    "currency": "fiat",
    "shipping_address": "456 Buyer St"
  }'

# 6. Create Payment
curl -X POST http://localhost:8000/api/payments/create/1/ \
  -H "Authorization: Bearer $TOKEN"

# 7. Simulate Pi Payment
docker-compose exec django python manage.py simulate_pi_payment --order 1
```

## Postman Collection

Import this collection for easy API testing:

```json
{
  "info": {
    "name": "Pi Market API",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
  },
  "auth": {
    "type": "bearer",
    "bearer": [{"key": "token", "value": "{{jwt_token}}"}]
  },
  "variable": [
    {"key": "base_url", "value": "http://localhost:8000"},
    {"key": "jwt_token", "value": ""}
  ]
}
```

## WebSocket Support (Future)

Currently not implemented. Future versions may include:
- Real-time order updates
- Chat between buyer/seller
- Live dispute resolution

## API Versioning

Current version: v1 (default)

Future versions will use URL versioning:
```
/api/v2/shops/products/
```