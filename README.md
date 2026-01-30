# Hatch Pay Mock Gateway Service

A lightweight service to mock the Tempus Gateway for testing edge cases like timeouts and specific error codes.

## Endpoints

- **Payment Operations**: `POST /{operation}`
  - Supported: `/CCAUTH`, `/CCFORCEAUTH` (Capture), `/CCREVERSE` (Void), `/CCCREDIT` (Refund), `/CCRECEIPTRETRIEVE` (Inquiry)
- **Tokenization**: `POST /v1/tokenization`
- **iFrame Session**: `POST /v1/iframe-session` (Returns a session ID and iFrame URL)
- **iFrame Page**: `GET /v1/iframe` (Renders a mock payment form that posts back to the `REFERURL`)

## Simulating Scenarios

You can control the behavior of the API by passing the `X-Mock-Scenario` header in your request.

| Scenario                    | Behavior                                                          |
| :-------------------------- | :---------------------------------------------------------------- |
| `TIMEOUT`                   | Sleeps for 70 seconds before responding (simulates HTTP timeout). |
| `RETRYABLE_ERROR`           | Returns error code `-153` (Unable to connect to processor).       |
| `GATEWAY_TIMEOUT_RECONCILE` | Returns error code `-155` (Timed out waiting for response).       |
| `AUTO_REVERSED`             | Returns error code `-159` (Permanent failure).                    |
| `DECLINED`                  | Returns a standard '100 Declined' response.                       |
| (None / Other)              | Returns a standard 'TRUE' success response.                       |

## Running Locally

```bash
pip install -r requirements.txt
python main.py
```

The service runs on port `8083` by default.

## Docker

```bash
docker build -t mock-gateway .
docker run -p 8083:8083 mock-gateway
```

## Documentation

- [Configuration Guide](docs/configuration_guide.md) - Detailed setup and database configuration.
