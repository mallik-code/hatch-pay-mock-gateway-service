import asyncio
import time
import uuid

class MockScenarios:
    @staticmethod
    async def get_response(scenario: str, operation: str, request_data: dict):
        """
        Returns a response body and status code based on the requested scenario.
        """
        # Default success response
        response_body = {
            "TRANRESP": {
                "TRANSUCCESS": "TRUE",
                "TRANRESPMESSAGE": "APPROVED",
                "SYSTEMTRACENUM": str(uuid.uuid4())[:8],
                "CCAUTHCODE": "123456",
                "AUTHDATE": time.strftime('%m/%d/%Y %H:%M:%S'),
                "TRANRESPERRCODE": "0"
            }
        }
        
        if scenario == "TIMEOUT":
            print(f"Simulating timeout for {operation}...")
            await asyncio.sleep(70) # Longer than the 60s default timeout
            return response_body # Return success if it manages to finish (though client will have timed out)

        if scenario == "RETRYABLE_ERROR":
            response_body["TRANRESP"]["TRANSUCCESS"] = "FALSE"
            response_body["TRANRESP"]["TRANRESPMESSAGE"] = "UNABLE TO CONNECT TO PROCESSOR"
            response_body["TRANRESP"]["TRANRESPERRCODE"] = "-153"
            return response_body

        if scenario == "GATEWAY_TIMEOUT_RECONCILE":
            response_body["TRANRESP"]["TRANSUCCESS"] = "FALSE"
            response_body["TRANRESP"]["TRANRESPMESSAGE"] = "TIMED OUT WAITING FOR RESPONSE"
            response_body["TRANRESP"]["TRANRESPERRCODE"] = "-155"
            return response_body

        if scenario == "AUTO_REVERSED":
            response_body["TRANRESP"]["TRANSUCCESS"] = "FALSE"
            response_body["TRANRESP"]["TRANRESPMESSAGE"] = "AUTO-REVERSED"
            response_body["TRANRESP"]["TRANRESPERRCODE"] = "-159"
            return response_body

        if scenario == "DECLINED":
            response_body["TRANRESP"]["TRANSUCCESS"] = "FALSE"
            response_body["TRANRESP"]["TRANRESPMESSAGE"] = "DECLINED"
            response_body["TRANRESP"]["TRANRESPERRCODE"] = "100"
            return response_body

        # Special handling for REVERSE (VOID)
        if operation == "CCREVERSE":
            response_body["TRANRESP"]["TRANRESPMESSAGE"] = "REVERSED SUCCESSFULLY"
        
        # Special handling for REFUND
        if operation == "CCCREDIT":
            response_body["TRANRESP"]["TRANRESPMESSAGE"] = "REFUNDED SUCCESSFULLY"

        # Special handling for INQUIRY
        if operation == "CCRECEIPTRETRIEVE":
            response_body["TRANRESP"]["TRANRESPMESSAGE"] = "RECEIPT RETRIEVED"
            # Inquiry often returns more data, but for mock, this is usually enough
            response_body["TRANRESP"]["ORIGINAL_TRANSACTION"] = {
                "TRANSUCCESS": "TRUE",
                "CCAUTHCODE": "123456"
            }
            
        return response_body
