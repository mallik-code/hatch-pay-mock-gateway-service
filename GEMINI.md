# GEMINI.md - Hatch Pay Mock Gateway Service

## Project Overview

The **Hatch Pay Mock Gateway Service** is a dedicated utility used to simulate the Behavior of the Tempus Technologies payment gateway. It is designed to facilitate testing of edge cases, error handling, and complex transaction flows (like timeout-reversal-retry) that are difficult to reproduce with a live sandbox.

## Technology Stack

- **Framework**: FastAPI
- **Language**: Python 3.11+
- **Containerization**: Docker

## Supported Operations

The service maps internal operation names to the corresponding Tempus endpoint paths:

- `CCAUTH` -> `/CCAUTH` (Authorize, Auth & Capture)
- `CCFORCEAUTH` -> `/CCFORCEAUTH` (Capture)
- `CCREVERSE` -> `/CCREVERSE` (Reversal/Void)
- `CCCREDIT` -> `/CCCREDIT` (Refund)
- `CCRECEIPTRETRIEVE` -> `/CCRECEIPTRETRIEVE` (Inquiry)

## Scenario Simulation

Behaviors are triggered using the `X-Mock-Scenario` HTTP header.

| Header Value                | Description                             | Tempus Code |
| :-------------------------- | :-------------------------------------- | :---------- |
| `TIMEOUT`                   | Simulate persistent network timeout     | (N/A)       |
| `RETRYABLE_ERROR`           | Connection error / Retry allowed        | `-153`      |
| `GATEWAY_TIMEOUT_RECONCILE` | Gateway timeout / Manual reconciliation | `-155`      |
| `AUTO_REVERSED`             | Permanent failure / Auto-reversed       | `-159`      |
| `DECLINED`                  | Transaction declined by processor       | `100`       |

## iFrame Simulation Flow

1. **Session Creation**: `POST /v1/iframe-session`
   - Accepts a JSON payload with `TRANSACTION` object containing `RNID`, `RNCERT`, `REFERURL`, etc.
   - Returns a JSON with `TRANRESP` containing `SESSIONID` and optionally `IFRAME_URL`.
   - **Important**: The backend `SessionIDHandler` specifically looks for `SESSIONID` in the response.
2. **iFrame Render**: `GET /v1/iframe`
   - Renders a mock payment form.
   - Accepts `session_id` and `refer_url` as query parameters.
   - Clicking "Complete Payment" performs a `POST` to the `refer_url` with mock session data.
   - Includes a "Cancel" link for testing abandonment.

## Deployment & Usage

- **Local**: `python main.py` (Port 8083)
- **Docker**: `docker build -t mock-gateway .`
- **Integration**: Update `GATEWAY_URL` in the Payment Proxy Service to point to this mock service.
