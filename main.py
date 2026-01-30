from fastapi import FastAPI, Request, Header, Response, Path
from fastapi.responses import HTMLResponse
import json
from scenarios import MockScenarios
import uuid
from enum import Enum
from typing import Optional, Annotated

class OperationName(str, Enum):
    CCAUTH = "CCAUTH"
    CCFORCEAUTH = "CCFORCEAUTH"
    CCREVERSE = "CCREVERSE"
    CCCREDIT = "CCCREDIT"
    CCRECEIPTRETRIEVE = "CCRECEIPTRETRIEVE"

class MockScenario(str, Enum):
    TIMEOUT = "TIMEOUT"
    RETRYABLE_ERROR = "RETRYABLE_ERROR"
    GATEWAY_TIMEOUT_RECONCILE = "GATEWAY_TIMEOUT_RECONCILE"
    AUTO_REVERSED = "AUTO_REVERSED"
    DECLINED = "DECLINED"

app = FastAPI(title="Hatch Pay Mock Gateway Service")

@app.get("/")
async def root():
    """
    Root endpoint to verify service is running.
    """
    return {
        "status": "online",
        "service": "Hatch Pay Mock Gateway Service",
        "documentation": "Check /docs for API documentation or docs/configuration_guide.md",
        "endpoints": {
            "payment_operations": "POST /{operation} (e.g. /CCAUTH)",
            "tokenization": "POST /v1/tokenization",
            "iframe_session": "POST /v1/iframe-session",
            "iframe_page": "GET /v1/iframe"
        }
    }

@app.post("/{operation}")
async def handle_payment_operation(
    operation: Annotated[OperationName, Path(description="The Tempus payment operation to perform")],
    request: Request,
    x_mock_scenario: Annotated[Optional[MockScenario], Header(description="Simulate specific gateway scenarios", alias="X-Mock-Scenario")] = None
):
    """
    Handles Tempus payment operations.
    Scenario can be controlled via 'X-Mock-Scenario' header.
    """
    try:
        request_data = await request.json()
    except:
        request_data = {}

    print(f"Received {operation} request. Scenario: {x_mock_scenario}")
    
    response_body = await MockScenarios.get_response(x_mock_scenario, operation, request_data)
    
    return response_body

@app.post("/v1/tokenization")
async def handle_tokenization(
    request: Request,
    x_mock_scenario: Annotated[Optional[MockScenario], Header(description="Simulate specific gateway scenarios", alias="X-Mock-Scenario")] = None
):
    """
    Mocks the tokenization endpoint.
    """
    if x_mock_scenario == "TIMEOUT":
        import asyncio
        await asyncio.sleep(70)
        
    return {
        "cc_token": f"mock_token_{str(uuid.uuid4())[:12]}",
        "last_four": "1111",
        "card_type": "VISA",
        "expiry_month": "12",
        "expiry_year": "2030"
    }

@app.post("/v1/iframe-session")
async def create_iframe_session(request: Request):
    """
    Mocks the Tempus iFrame session creation.
    """
    try:
        request_data = await request.json()
        refer_url = request_data.get("TRANSACTION", {}).get("REFERURL", "http://localhost:8080/callback")
    except:
        refer_url = "http://localhost:8080/callback"

    session_id = str(uuid.uuid4())
    print(f"Created iFrame session: {session_id}, Refer URL: {refer_url}")
    
    return {
        "TRANRESP": {
            "TRANSUCCESS": "TRUE",
            "IFRAME_URL": f"http://localhost:8083/v1/iframe?session_id={session_id}&refer_url={refer_url}",
            "SESSIONID": session_id
        }
    }

@app.get("/v1/iframe", response_class=HTMLResponse)
async def get_iframe(refer_url: str = "http://localhost:8080/callback", session_id: str = "mock-session"):
    """
    Mocks the Tempus iFrame page.
    """
    return f"""
    <html>
        <head>
            <title>Mock Tempus iFrame</title>
            <style>
                body {{ font-family: sans-serif; background: #f0f0f0; display: flex; align-items: center; justify-content: center; height: 100vh; margin: 0; }}
                .card {{ border: 2px solid #ccc; padding: 20px; background: white; border-radius: 8px; width: 350px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
                input {{ width: 100%; margin-bottom: 12px; padding: 10px; border: 1px solid #ddd; border-radius: 4px; box-sizing: border-box; }}
                button {{ width: 100%; background: #007bff; color: white; border: none; padding: 12px; border-radius: 4px; cursor: pointer; font-weight: bold; }}
                button:hover {{ background: #0056b3; }}
                .row {{ display: flex; gap: 10px; }}
            </style>
        </head>
        <body>
            <div class="card">
                <h3>Tempus Mock Payment</h3>
                <p style="font-size: 12px; color: #666;">Session: {session_id}</p>
                <form action="{refer_url}" method="POST">
                    <input type="hidden" name="session_id" value="{session_id}">
                    <input type="text" name="cc_number" placeholder="Card Number (mock)" value="4111 1111 1111 1111">
                    <div class="row">
                        <input type="text" name="expiry" placeholder="MM/YY" value="12/30">
                        <input type="text" name="cvv" placeholder="CVV" value="123">
                    </div>
                    <button type="submit">
                        Complete Payment
                    </button>
                </form>
                <div style="margin-top: 15px; text-align: center;">
                    <a href="{refer_url}?status=cancel" style="font-size: 12px; color: #dc3545; text-decoration: none;">Cancel and Return</a>
                </div>
            </div>
        </body>
    </html>
    """

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8083)
