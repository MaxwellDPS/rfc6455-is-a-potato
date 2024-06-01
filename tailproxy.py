"""
Module: tailscale_proxy

This module initializes a Quart application to proxy HTTP POST and WebSocket connections
to a Tailscale server. It provides two main functionalities:
1. Proxying POST requests to the Tailscale control server.
2. Proxying WebSocket connections to the Tailscale control server.

The target server URL is retrieved from an environment variable (`HEADSCALE_URL`) or uses a default value.

Functions:
- proxy_upgrade(): Proxies the Tailscale client WebSocket Upgrade POST request.
- proxy_ws(): Proxies Tailscale WebSocket messages.

Usage:
Run the script to start the Quart application, which will listen on all available IP addresses
(`0.0.0.0`) and port `5000` in debug mode.

Environment Variables:
- HEADSCALE_URL: URL of the Headscale server (default: "http://controlplane.tailscale.com")

Example:
    $ HEADSCALE_URL="http://example.com" python tailscale_proxy.py
"""

import os
import asyncio
import websockets
from quart import Quart, request
import requests_async as requests

# Initialize the Quart application
app = Quart(__name__)

DEBUG = os.getenv("DEBUG", "false").lower() in ("true", "1", "t")

# Retrieve the Headscale URL from the environment variable or use the default value
HEADSCALE_URL = os.getenv("HEADSCALE_URL", "http://controlplane.tailscale.com")
TS2021_URL = f'http://{HEADSCALE_URL}:80/ts2021'

@app.route('/ts2021', methods=['POST'])
async def proxy_upgrade():
    """
    Function to proxy the Tailscale client WebSocket Upgrade POST request.

    This function captures POST requests made to the /ts2021 path, modifies the headers,
    and forwards the request to the target server. The response from the target server
    is then returned to the client.
    """
    # Get request headers
    headers = {key: value for key, value in request.headers.items()}

    # Replace the Upgrade header that Cloudflare changes to Upgrade: WebSocket
    headers['Upgrade'] = 'tailscale-control-protocol'

    # Forward the request to the target server
    response = await requests.post(TS2021_URL, headers=headers, data=await request.data)

    # Create a Quart Response object with the proxied response
    return response.content, response.status_code, response.headers.items()

@app.websocket('/ts2021')
async def proxy_ws():
    """
    Function to proxy Tailscale WebSocket messages.

    This function captures WebSocket connections made to the /ts2021 path and
    creates a WebSocket connection to the target server. It forwards messages
    between the client and the target server.
    """
    # Create a WebSocket connection to the target server
    async with websockets.connect(TS2021_URL) as target_ws:
        async def forward_message():
            async for message in target_ws:
                await target_ws.send(message)

        await asyncio.gather(forward_message())

if __name__ == '__main__':
    # Run the Quart application
    app.run(host='0.0.0.0', port=5000, debug=True)
