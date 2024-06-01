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
import uuid
import asyncio
import websockets
from quart import Quart, request, make_response
import requests_async as requests
from prometheus_client import Counter, Histogram, Gauge, generate_latest

# Initialize the Quart application
app = Quart(__name__)

DEBUG = os.getenv("DEBUG", "false").lower() in ("true", "1", "t")

# Retrieve the Headscale URL from the environment variable or use the default value
HEADSCALE_URL = os.getenv("HEADSCALE_URL", "http://headscale")
TS2021_URL = f'http://{HEADSCALE_URL}:80/ts2021'

# Generate a unique ID for this script run
SCRIPT_RUN_ID = str(uuid.uuid4())

# Prometheus metrics
REQUEST_COUNT = Counter('tailscale_proxy_requests_total', 'Total number of requests', ['script_run_id'])
REQUEST_LATENCY = Histogram('tailscale_proxy_request_latency_seconds', 'Request latency in seconds', ['script_run_id'])
WEBSOCKET_MESSAGES = Counter('tailscale_proxy_websocket_messages_total', 'Total number of WebSocket messages relayed', ['script_run_id'])
WEBSOCKET_MESSAGES_SUCCESS = Counter('tailscale_proxy_websocket_messages_success', 'Total number of WebSocket messages successfully relayed', ['script_run_id'])
WEBSOCKET_CONNECTIONS = Counter('tailscale_proxy_websocket_connections_total', 'Total number of WebSocket connections', ['script_run_id'])
USER_AGENT_COUNT = Counter('tailscale_proxy_user_agent_requests_total', 'Total number of requests by user agent', ['user_agent', 'script_run_id'])
REQUEST_SIZE = Histogram('tailscale_proxy_request_size_bytes', 'Size of HTTP requests in bytes', ['script_run_id'])
RESPONSE_SIZE = Histogram('tailscale_proxy_response_size_bytes', 'Size of HTTP responses in bytes', ['script_run_id'])
ERROR_COUNT = Counter('tailscale_proxy_error_count_total', 'Total number of errors', ['script_run_id'])
STATUS_COUNT = Counter('tailscale_proxy_status_count_total', 'Total number of responses by status code', ['status_code', 'script_run_id'])
SCRIPT_RUN_GAUGE = Gauge('tailscale_proxy_script_run_id', 'Unique ID for this script run', ['script_run_id'])

# Set the gauge to indicate the script is running
SCRIPT_RUN_GAUGE.labels(script_run_id=SCRIPT_RUN_ID).set(1)

@app.route('/metrics')
async def metrics():
    """Endpoint to serve Prometheus metrics."""
    response = await make_response(generate_latest())
    response.headers['Content-Type'] = 'text/plain; version=0.0.4; charset=utf-8'
    return response

@app.route('/ts2021', methods=['POST'])
@REQUEST_COUNT.count_exceptions()
@REQUEST_LATENCY.time()
async def proxy_upgrade():
    """
    Function to proxy the Tailscale client WebSocket Upgrade POST request.

    This function captures POST requests made to the /ts2021 path, modifies the headers,
    and forwards the request to the target server. The response from the target server
    is then returned to the client.
    """

    # Increment request count
    REQUEST_COUNT.labels(script_run_id=SCRIPT_RUN_ID).inc()

    # Start request latency timer
    with REQUEST_LATENCY.labels(script_run_id=SCRIPT_RUN_ID).time():
        # Get request headers
        headers = {key: value for key, value in request.headers.items()}

        # Count user agent occurrences
        user_agent = headers.get('User-Agent', 'unknown')
        USER_AGENT_COUNT.labels(user_agent=user_agent, script_run_id=SCRIPT_RUN_ID).inc()

        # Replace the Upgrade header that Cloudflare changes to Upgrade: WebSocket
        headers['Upgrade'] = 'tailscale-control-protocol'

        try:
            # Measure request size
            request_data = await request.data
            request_size = len(request_data)
            REQUEST_SIZE.labels(script_run_id=SCRIPT_RUN_ID).observe(request_size)

            # Forward the request to the target server
            response = await requests.post(TS2021_URL, headers=headers, data=request_data)

            # Measure response size
            response_size = len(response.content)
            RESPONSE_SIZE.labels(script_run_id=SCRIPT_RUN_ID).observe(response_size)

            # Count the status code
            STATUS_COUNT.labels(status_code=response.status_code, script_run_id=SCRIPT_RUN_ID).inc()
        except Exception as e:
            # Increment error count
            ERROR_COUNT.labels(script_run_id=SCRIPT_RUN_ID).inc()
            raise e

        # Create a Quart Response object with the proxied response
        return response.content, response.status_code, response.headers.items()

@app.websocket('/ts2021')
@WEBSOCKET_CONNECTIONS.count_exceptions()
async def proxy_ws():
    """
    Function to proxy Tailscale WebSocket messages.

    This function captures WebSocket connections made to the /ts2021 path and
    creates a WebSocket connection to the target server. It forwards messages
    between the client and the target server.
    """
    # Create a WebSocket connection to the target server
    try:
        # Increment websocket connection count
        WEBSOCKET_CONNECTIONS.labels(script_run_id=SCRIPT_RUN_ID).inc()
        async with websockets.connect(TS2021_URL) as target_ws:
            async def forward_message():
                async for message in target_ws:
                    WEBSOCKET_MESSAGES.labels(script_run_id=SCRIPT_RUN_ID).inc()
                    await target_ws.send(message)
                    WEBSOCKET_MESSAGES_SUCCESS.labels(script_run_id=SCRIPT_RUN_ID).inc()
            await asyncio.gather(forward_message())
    except Exception as e:
        # Increment error count
        ERROR_COUNT.labels(script_run_id=SCRIPT_RUN_ID).inc()
        raise e

if __name__ == '__main__':
    # Run the Quart application
    app.run(host='0.0.0.0', port=6969, debug=DEBUG)
