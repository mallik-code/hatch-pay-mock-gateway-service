# Mock Gateway Configuration Guide

This guide explains how to configure the Hatch Pay Mock Gateway Service to simulate the Tempus payment gateway in your local development environment.

## Overview

The Mock Gateway Service replicates the Tempus Technologies payment gateway behavior, allowing you to test edge cases, error scenarios, and complex transaction flows without connecting to the actual gateway.

---

## Service URLs

The mock gateway runs on **port 8083** by default and provides the following endpoints:

### **Gateway URL** (Payment Operations)

```
http://localhost:8083
```

**Available Operations:**

- `POST /CCAUTH` - Authorization / Auth & Capture
- `POST /CCFORCEAUTH` - Capture (Force Auth)
- `POST /CCREVERSE` - Reversal / Void
- `POST /CCCREDIT` - Refund
- `POST /CCRECEIPTRETRIEVE` - Inquiry / Receipt Retrieval

### **iFrame URL**

```
http://localhost:8083/v1/iframe
```

**Session Creation Endpoint:**

```
POST http://localhost:8083/v1/iframe-session
```

**Response Format:**

```json
{
  "TRANRESP": {
    "TRANSUCCESS": "TRUE",
    "IFRAME_URL": "http://localhost:8083/v1/iframe?session_id={session_id}&refer_url={refer_url}",
    "SESSIONID": "{session_id}"
  }
}
```

### **Tokenizer API URL**

```
POST http://localhost:8083/v1/tokenization
```

**Response Format:**

```json
{
  "cc_token": "mock_token_{uuid}",
  "last_four": "1111",
  "card_type": "VISA",
  "expiry_month": "12",
  "expiry_year": "2030"
}
```

---

## Database Configuration

### Payment Orchestrator Setup

To configure the mock gateway in your local database, insert the following record into the `hatch_pay.payment_orchestrators` table:

```sql
INSERT INTO hatch_pay.payment_orchestrators (
    id,
    business_unit_id,
    name,
    payment_gateway,
    gateway_url,
    iframe_url,
    tokenizer_api_url,
    gateway_authentication,
    accepted_payment_methods,
    is_active,
    created_at,
    updated_at
) VALUES (
    '5841ba94-97c1-4e6a-93fe-d6f494a9a33f',
    '{your_business_unit_id}',               -- Replace with your BU ID
    'Mock Tempus Orchestrator',
    'TEMPUS',
    'http://localhost:8083',
    'http://localhost:8083/v1/iframe',
    'http://localhost:8083/v1/tokenization',
    'Tempus Custom Auth',
    ARRAY['CC'],
    true,
    NOW(),
    NOW()
)
ON CONFLICT (id) DO UPDATE SET
    gateway_url = EXCLUDED.gateway_url,
    iframe_url = EXCLUDED.iframe_url,
    tokenizer_api_url = EXCLUDED.tokenizer_api_url,
    updated_at = NOW();
```

### Complete Seed Script

For a complete local setup, use this seed script:

```sql
-- Ensure tenant exists
INSERT INTO hatch_pay.tenants (id, name, is_active)
VALUES ('test-tenant-001', 'Test Tenant', true)
ON CONFLICT (id) DO NOTHING;

-- Ensure business unit exists
INSERT INTO hatch_pay.business_units (
    id,
    tenant_id,
    name,
    is_active
) VALUES (
    'test-bu-001',
    'test-tenant-001',
    'Test Business Unit',
    true
)
ON CONFLICT (id) DO NOTHING;

-- Insert mock gateway orchestrator
INSERT INTO hatch_pay.payment_orchestrators (
    id,
    business_unit_id,
    name,
    payment_gateway,
    gateway_url,
    iframe_url,
    tokenizer_api_url,
    gateway_authentication,
    accepted_payment_methods,
    is_active,
    created_at,
    updated_at
) VALUES (
    '5841ba94-97c1-4e6a-93fe-d6f494a9a33f',
    'test-bu-001',
    'Mock Tempus Orchestrator',
    'TEMPUS',
    'http://localhost:8083',
    'http://localhost:8083/v1/iframe',
    'http://localhost:8083/v1/tokenization',
    'Tempus Custom Auth',
    ARRAY['CC'],
    true,
    NOW(),
    NOW()
)
ON CONFLICT (id) DO UPDATE SET
    gateway_url = EXCLUDED.gateway_url,
    iframe_url = EXCLUDED.iframe_url,
    tokenizer_api_url = EXCLUDED.tokenizer_api_url,
    updated_at = NOW();
```

---

## Environment Configuration

### Payment Proxy Service

Configure your `payment-proxy-service` to use the mock gateway:

```bash
# Mock Gateway Configuration
TEMPUS_GATEWAY_URL=http://localhost:8083
TEMPUS_IFRAME_URL=http://localhost:8083/v1/iframe
TEMPUS_TOKENIZER_URL=http://localhost:8083/v1/tokenization
TEMPUS_GATEWAY_AUTHENTICATION=Tempus Custom Auth

# Timeout Configuration (optional)
TEMPUS_TIMEOUT_SECONDS=60
TEMPUS_MAX_RETRY_ATTEMPTS=3
```

### Docker Compose

Add the mock gateway service to your `docker-compose.yml`:

```yaml
services:
  mock-gateway:
    build:
      context: ./hatch-pay-mock-gateway-service
      dockerfile: Dockerfile
    ports:
      - "8083:8083"
    networks:
      - hatch-pay-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8083/CCAUTH"]
      interval: 10s
      timeout: 5s
      retries: 3
```

---

## UAT vs Mock Comparison

| Field                        | UAT Value                                                      | Mock Value                              |
| ---------------------------- | -------------------------------------------------------------- | --------------------------------------- |
| **Name**                     | Tempus Orchestrator                                            | Mock Tempus Orchestrator                |
| **Payment Gateway**          | TEMPUS                                                         | TEMPUS                                  |
| **Gateway URL**              | `https://QA1.spectrumretailnet.com/PPSAPI`                     | `http://localhost:8083`                 |
| **iFrame URL**               | `https://aaahatchpay-pp-prtldev.spectrumretailnet.com/PP?PAGE` | `http://localhost:8083/v1/iframe`       |
| **Tokenizer API URL**        | `https://AAAHatchPay-PP-PRTLDEV.SPECTRUMRETAILNET.COM`         | `http://localhost:8083/v1/tokenization` |
| **Gateway Authentication**   | Tempus Custom Auth                                             | Tempus Custom Auth                      |
| **Accepted Payment Methods** | CC                                                             | CC                                      |

---

## Test Scenarios

The mock gateway supports various test scenarios controlled via the `X-Mock-Scenario` HTTP header:

| Scenario Header             | Behavior              | Tempus Code | Use Case                           |
| --------------------------- | --------------------- | ----------- | ---------------------------------- |
| `TIMEOUT`                   | Sleeps for 70 seconds | N/A         | Test timeout handling and recovery |
| `RETRYABLE_ERROR`           | Connection error      | `-153`      | Test retry logic                   |
| `GATEWAY_TIMEOUT_RECONCILE` | Gateway timeout       | `-155`      | Test manual reconciliation flow    |
| `AUTO_REVERSED`             | Permanent failure     | `-159`      | Test auto-reversal handling        |
| `DECLINED`                  | Transaction declined  | `100`       | Test declined transaction flow     |
| (None)                      | Success response      | N/A         | Test happy path                    |

### Example Request

```bash
curl -X POST http://localhost:8083/CCAUTH \
  -H "Content-Type: application/json" \
  -H "X-Mock-Scenario: TIMEOUT" \
  -d '{
    "TRANSACTION": {
      "TRANSID": "test-123",
      "AMOUNT": "10.00"
    }
  }'
```

---

## Running the Mock Gateway

### Local Python

```bash
cd C:\projects\hatch-pay\backend\hatch-pay-mock-gateway-service
pip install -r requirements.txt
python main.py
```

The service will start on `http://localhost:8083`.

### Docker

```bash
cd C:\projects\hatch-pay\backend\hatch-pay-mock-gateway-service
docker build -t mock-gateway .
docker run -p 8083:8083 mock-gateway
```

### Verify Service

```bash
# Health check
curl http://localhost:8083/CCAUTH

# Test tokenization
curl -X POST http://localhost:8083/v1/tokenization \
  -H "Content-Type: application/json" \
  -d '{}'
```

---

## Integration Testing

### Testing Timeout Recovery

```python
import requests

# Trigger timeout scenario
response = requests.post(
    "http://localhost:8083/CCAUTH",
    headers={"X-Mock-Scenario": "TIMEOUT"},
    json={"TRANSACTION": {"TRANSID": "test-timeout", "AMOUNT": "10.00"}},
    timeout=5  # Will timeout before 70s sleep completes
)
```

### Testing iFrame Flow

```python
# 1. Create session
session_response = requests.post(
    "http://localhost:8083/v1/iframe-session",
    json={
        "TRANSACTION": {
            "REFERURL": "http://localhost:8080/callback"
        }
    }
)

session_id = session_response.json()["TRANRESP"]["SESSIONID"]
iframe_url = session_response.json()["TRANRESP"]["IFRAME_URL"]

# 2. Open iframe_url in browser or automated test
print(f"iFrame URL: {iframe_url}")
```

---

## Troubleshooting

### Port Already in Use

If port 8083 is already in use:

```bash
# Find process using port 8083
netstat -ano | findstr :8083

# Kill the process (Windows)
taskkill /PID <process_id> /F
```

Or change the port in `main.py`:

```python
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8084)  # Changed to 8084
```

### Connection Refused

Ensure the mock gateway is running:

```bash
curl http://localhost:8083/CCAUTH
```

If not running, start it:

```bash
python main.py
```

### Database Connection Issues

Verify your payment orchestrator configuration:

```sql
SELECT id, name, gateway_url, iframe_url, tokenizer_api_url
FROM hatch_pay.payment_orchestrators
WHERE payment_gateway = 'TEMPUS';
```

---

## Best Practices

1. **Always use the mock gateway for local development** to avoid hitting real gateway limits
2. **Test all scenarios** (success, timeout, errors) before deploying
3. **Keep the orchestrator ID consistent** (`5841ba94-97c1-4e6a-93fe-d6f494a9a33f`) across environments for easier debugging
4. **Use Docker Compose** for consistent multi-service testing
5. **Review logs** in both mock gateway and payment proxy service for troubleshooting

---

## Additional Resources

- [README.md](../README.md) - Service overview and quick start
- [scenarios.py](../scenarios.py) - Mock scenario implementation details
- [main.py](../main.py) - Service endpoint definitions
- [Postman Collection](../postman-collection/) - Pre-configured API tests
