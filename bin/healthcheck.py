#!/usr/bin/env python3

import os
import logging
import uvicorn
import requests
from datetime import datetime,timedelta
from functools import wraps
from rpcstatus import RpcStatus
from fastapi import FastAPI, HTTPException
from starlette.responses import JSONResponse

# Environment Variables
PORT = os.getenv('PORT', 3301)
DEBUG = os.getenv('DEBUG', False)
PROTOCOL = os.getenv('PROTOCOL', "http")
RPC_HOST = os.getenv('RPC_HOST', "127.0.0.1")
RPC_PORT = os.getenv('RPC_PORT', 26657)
LCD_PORT = os.getenv('LCD_PORT', 1317)
CHAIN_NAME = os.getenv('CHAIN_NAME', None)
DOMAIN = os.getenv('DOMAIN', None)
BASE_URL = f"{PROTOCOL}://{RPC_HOST}"

# Logger Configuration
logging.basicConfig(level=logging.DEBUG if DEBUG else logging.INFO)
logger = logging.getLogger()

# FastAPI App
app = FastAPI()

def cache_response(number_of_seconds: int = 3):
    """
    Decorator that caches the response of a FastAPI async function.

    Example:
    ```
        app = FastAPI()

        @app.get("/")
        @cache_response
        async def example():
            return {"message": "Hello World"}
    ```
    """
    def cache_decorator(func):
        response = None
        last_updated = datetime.fromtimestamp(0)
        @wraps(func)
        def cache_wrapper(*args, **kwargs):
            nonlocal response
            nonlocal last_updated
            
            if last_updated < datetime.now() - timedelta(seconds=number_of_seconds):
                response = func(*args, **kwargs)
                last_updated = datetime.now()

            return response
        return cache_wrapper
    return cache_decorator


# Rpc Health Check
@app.get('/rpc/health')
@cache_response(5)
def rpc_health():
    try:
        status = RpcStatus(f"{BASE_URL}:{RPC_PORT}/status")

        if status.is_catching_up():
            logger.warning("RPC is catching up")
            return JSONResponse(content=status.sync_info.to_dict(), status_code=403)
        elif CHAIN_NAME and DOMAIN and status.is_behind(CHAIN_NAME, DOMAIN):
            logger.warning("RPC is behind")
            return JSONResponse(content=status.sync_info.to_dict(), status_code=403)
        else:
            logger.debug("RPC is caught up")
            return JSONResponse(content=status.sync_info.to_dict(), status_code=200)
    except requests.RequestException as error:
        logger.error(error)
        raise HTTPException(status_code=500, detail=str(error))


# Lcd Health Check
@app.get('/lcd/health')
@cache_response(5)
def lcd_health():
    try:
        # check rpc health first
        response = rpc_health()
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail="rpc status check failed")

        response = requests.get(f"{BASE_URL}:{LCD_PORT}/cosmos/base/tendermint/v1beta1/syncing")
        response.raise_for_status()
        return JSONResponse(content=response.json(), status_code=200)
        
    except requests.RequestException as error:
        logger.error(error)
        raise HTTPException(status_code=error.response.status_code, detail=str(error))


if __name__ == '__main__':
    uvicorn.run("healthcheck:app", host="0.0.0.0", port=int(PORT), reload=DEBUG)