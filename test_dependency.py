#!/usr/bin/env python3
"""
Simple test to verify FastAPI dependency injection is working
"""
from fastapi import FastAPI, Depends, HTTPException, Header
import uvicorn
import os

app = FastAPI()

call_count = 0

def simple_auth(x_api_key: str = Header(default=None)):
    """Simple auth dependency"""
    global call_count
    call_count += 1
    print(f"[simple_auth #{call_count}] Called! x_api_key={x_api_key}")

    if not x_api_key:
        print(f"[simple_auth #{call_count}] Raising 422 - no header")
        raise HTTPException(status_code=422, detail="API key required")

    if x_api_key != "valid-key":
        print(f"[simple_auth #{call_count}] Raising 403 - invalid key")
        raise HTTPException(status_code=403, detail="Invalid key")

    print(f"[simple_auth #{call_count}] Returning True")
    return True

@app.get("/test")
async def test_endpoint(auth: bool = Depends(simple_auth)):
    """Test endpoint with dependency"""
    print(f"[test_endpoint] Handler called, auth={auth}")
    return {"status": "ok", "auth": auth}

if __name__ == "__main__":
    print("Starting test server...")
    print("ENV:", os.getenv("ENV", "not set"))
    print("API_KEY:", os.getenv("API_KEY", "not set"))
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
