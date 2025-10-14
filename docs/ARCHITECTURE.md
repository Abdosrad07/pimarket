# Pi Market Architecture

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Client Layer                          │
│  (Web/Mobile App with Geolocation & Payment Integration)    │
└──────────────────┬──────────────────────────────────────────┘
                   │ HTTPS/REST API
┌──────────────────▼──────────────────────────────────────────┐
│                      Nginx (Reverse Proxy)                   │
└──────────────────┬──────────────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────────────┐
│                    Django Application                        │
│  ┌─────────────┬─────────────┬─────────────────────────┐   │
│  │  Accounts   │    Shops    │      Payments           │   │
│  │  - User     │  - Products │  - Stripe Provider      │   │
│  │  - OTP      │  - Orders   │  - Pi Network Provider  │   │
│  │  - Location │  - Disputes │  - Escrow Logic         │   │
│  └─────────────┴─────────────┴─────────────────────────┘   │
└──────────────┬──────────────────────┬───────────────────────┘
               │                      │
               │                      │ Celery Tasks
               │                      │
┌──────────────▼──────────┐  ┌───────▼────────────────────────┐
│   PostgreSQL Database   │  │  Celery Worker + Beat          │
│   - User data           │  │  - Payment checks              │
│   - Orders/Products     │  │  - Escrow auto-release         │
│   - Payment records     │  │  - Notifications               │
└─────────────────────────┘  └────────────────────────────────┘
               │                      │
               │                      │
┌──────────────▼──────────────────────▼─────────────────────┐
│                    Redis Cache                             │
│                    - Session storage                       │
│                    - Celery broker/backend                 │
└────────────────────────────────────────────────────────────┘
               │
┌──────────────▼──────────────────────────────────────────────┐
│              External Services                               │
│  ┌──────────┬──────────┬─────────────┬──────────────────┐  │
│  │  Stripe  │ Pi API   │ Twilio/MTN  │   File Storage   │  │
│  │  (Fiat)  │ (Crypto) │   (SMS)     │   (Media Files)  │  │
│  └──────────┴──────────┴─────────────┴──────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## Application Structure

```
pimarket/
├── apps/
│   ├── accounts/           # User authentication & management
│   │   ├── models.py       # User, PhoneOTP, UserLocation
│   │   ├── views.py        # Registration, OTP, profile
│   │   ├── serializers.py  # API serializers
│   │   └── sms_provider.py # Pluggable SMS integration
│   │
│   ├── shops/              # Shop & product management
│   │   ├── models.py       # Shop, Product, Order, Dispute
│   │   ├── views.py        # CRUD operations
│   │   ├── filters.py      # Product filtering & search
│   │   └── serializers.py  # API serializers
│   │
│   └── payments/           # Payment processing
│       ├── models.py       # Payment, EscrowTransaction
│       ├── views.py        # Payment creation & confirmation
│       ├── webhooks.py     # Webhook handlers
│       ├── tasks.py        # Celery tasks
│       ├── stripe_provider.py  # Stripe integration
│       └── pi_provider.py      # Pi Network integration
│
├── pimarket/               # Project settings
│   ├── settings.py         # Django settings
│   ├── urls.py             # URL routing
│   └── celery.py           # Celery configuration
│
├── docker/                 # Docker configurations
│   ├── django/
│   └── nginx/
│
└── docs/                   # Documentation
```

## Data Flow

### Order Creation Flow

```
1. User selects products → Add to cart
2. User clicks checkout → POST /api/shops/orders/create/
3. Backend validates:
   - Products exist and are active
   - Stock availability
   - All products from same shop
4. Create Order (status: 'created')
5. Create OrderItems
6. Reduce product stock (atomic transaction)
7. Order status → 'pending_payment'
8. Return order details to client
```

### Payment Flow (Stripe)

```
1. Client: POST /api/payments/create/{order_id}/
2. Backend: Create Stripe PaymentIntent (manual capture)
3. Return client_secret to frontend
4. Frontend: Use Stripe.js to confirm payment
5. Stripe webhook: payment_intent.succeeded
6. Backend: Update payment status to 'succeeded'
7. Create EscrowTransaction (status: 'held')
8. Order status → 'paid_in_escrow'
9. Seller can now ship the order
```

### Payment Flow (Pi Network)

```
1. Client: POST /api/payments/create/{order_id}/
2. Backend: Call Pi API to create payment request
3. Return approval_url to frontend
4. User approves in Pi app
5. Pi webhook: payment_completed
6. Backend: Verify and update payment
7. Create EscrowTransaction
8. Order status → 'paid_in_escrow'
```

### Escrow Release Flow

```
Physical Products:
1. Seller marks order as 'shipped'
2. Delivery tracking created
3. Buyer receives and confirms delivery
4. Buyer: POST /api/shops/orders/{id}/confirm-delivery/
5. Order status → 'delivered'
6. Celery task: release_escrow_funds
7. Stripe: Capture payment
8. EscrowTransaction status → 'released'
9. Order status → 'released'
10. Funds available to seller

Digital Products:
1. Payment confirmed
2. Immediate auto-release triggered
3. Digital asset delivered
4. Escrow released automatically
```

### Dispute Flow

```
1. Buyer: POST /api/shops/disputes/open/
2. Order status → 'disputed'
3. Payment held in escrow
4. Buyer/Seller exchange messages
5. Admin reviews and decides
6. Resolution: Either release to seller OR refund to buyer
7. Update order status accordingly
```

## Database Schema Relationships

```
User ──┬── 1:N ──> UserLocation
       ├── 1:N ──> Shop (as owner)
       ├── 1:N ──> Order (as buyer)
       └── 1:N ──> Dispute (as raised_by)

Shop ──┬── 1:N ──> Product
       └── 1:N ──> Order

Product ──> N:1 ──> ProductCategory

Order ──┬── 1:N ──> OrderItem
        ├── 1:1 ──> Delivery (optional)
        ├── 1:1 ──> Dispute (optional)
        └── 1:N ──> Payment

OrderItem ──> N:1 ──> Product

Payment ──> 1:1 ──> EscrowTransaction

Dispute ──> 1:N ──> DisputeMessage
```

## Security Architecture

### Authentication
- Phone-based registration with OTP
- JWT tokens for API authentication
- Session-based auth for web interface
- Token refresh mechanism

### Authorization
- User can only access own data
- Shop owner can manage own products
- Seller can view orders for own shops
- Buyer can view own orders

### Payment Security
- Stripe handles card details (PCI compliant)
- Pi Network handles crypto transfers
- Webhook signature verification
- Escrow protects both parties

### Rate Limiting
- OTP requests: 5/hour per phone
- API requests: 100/hour (anonymous), 1000/hour (authenticated)

## Scalability Considerations

### Current Setup (Hackathon/MVP)
- Single Docker host
- PostgreSQL single instance
- Redis single instance
- Suitable for 100-1000 concurrent users

### Production Scaling

**Horizontal Scaling:**
- Multiple Django instances behind load balancer
- Separate Celery workers for different queues
- Redis cluster for high availability
- PostgreSQL read replicas

**Caching Strategy:**
- Redis for session storage
- Cache product listings
- Cache user locations
- CDN for static/media files

**Database Optimization:**
- Index on frequently queried fields
- Partitioning for large tables (orders, payments)
- Connection pooling

**Background Jobs:**
- Separate Celery queues:
  - High priority: Payment processing
  - Medium: Notifications
  - Low: Analytics, cleanup

## Monitoring & Observability

**Logging:**
- Django logs to stdout (captured by Docker)
- Celery task logs
- Payment transaction logs

**Metrics to Track:**
- Order completion rate
- Payment success rate
- Average order value
- Escrow release time
- API response times
- Database query performance

**Alerts:**
- Failed payments
- Stuck orders
- High error rates
- Celery queue backlog

## Technology Choices

### Why Django?
- Rapid development
- Built-in admin panel
- ORM for database abstraction
- Mature ecosystem

### Why PostgreSQL?
- ACID compliance (critical for payments)
- JSON field support
- Geographic queries support
- Production-proven

### Why Redis?
- Fast in-memory caching
- Celery broker/backend
- Session storage
- Pub/sub for real-time features

### Why Celery?
- Async task processing
- Scheduled tasks (auto-release)
- Retry mechanisms
- Task monitoring

### Why Docker?
- Consistent environments
- Easy deployment
- Service isolation
- Portable across clouds