there are avaialble  opensource libs on pypi


What is websockets?
websockets is a library for building WebSocket servers and clients in Python with a focus on correctness, simplicity, robustness, and performance.

Built on top of asyncio, Python's standard asynchronous I/O framework, the default implementation provides an elegant coroutine-based API.

An implementation on top of threading and a Sans-I/O implementation are also available.

Documentation is available on Read the Docs.

Here's an echo server with the asyncio API:

#!/usr/bin/env python

import asyncio
from websockets.asyncio.server import serve

async def echo(websocket):
    async for message in websocket:
        await websocket.send(message)

async def main():
    async with serve(echo, "localhost", 8765) as server:
        await server.serve_forever()

asyncio.run(main())
Here's how a client sends and receives messages with the threading API:

#!/usr/bin/env python

from websockets.sync.client import connect

def hello():
    with connect("ws://localhost:8765") as websocket:
        websocket.send("Hello world!")
        message = websocket.recv()
        print(f"Received: {message}")

hello()
Does that look good?

Get started with the tutorial!



websockets for enterprise
Available as part of the Tidelift Subscription

The maintainers of websockets and thousands of other packages are working with Tidelift to deliver commercial support and maintenance for the open source dependencies you use to build your applications. Save time, reduce risk, and improve code health, while paying the maintainers of the exact dependencies you use. Learn more.

(If you contribute to websockets and would like to become an official support provider, let me know.)

Why should I use websockets?
The development of websockets is shaped by four principles:

Correctness: websockets is heavily tested for compliance with RFC 6455. Continuous integration fails under 100% branch coverage.
Simplicity: all you need to understand is msg = await ws.recv() and await ws.send(msg). websockets takes care of managing connections so you can focus on your application.
Robustness: websockets is built for production. For example, it was the only library to handle backpressure correctly before the issue became widely known in the Python community.
Performance: memory usage is optimized and configurable. A C extension accelerates expensive operations. It's pre-compiled for Linux, macOS and Windows and packaged in the wheel format for each system and Python version.
Documentation is a first class concern in the project. Head over to Read the Docs and see for yourself.

Why shouldn't I use websockets?
If you prefer callbacks over coroutines: websockets was created to provide the best coroutine-based API to manage WebSocket connections in Python. Pick another library for a callback-based API.

If you're looking for a mixed HTTP / WebSocket library: websockets aims at being an excellent implementation of RFC 6455: The WebSocket Protocol and RFC 7692: Compression Extensions for WebSocket. Its support for HTTP is minimal — just enough for an HTTP health check.

If you want to do both in the same server, look at HTTP + WebSocket servers that build on top of websockets to support WebSocket connections, like uvicorn or Sanic.

What else?
Bug reports, patches and suggestions are welcome!

To report a security vulnerability, please use the Tidelift security contact. Tidelift will coordinate the fix and disclosure.

For anything else, please open an issue or send a pull request.

Participants must uphold the Contributor Covenant code of conduct.

websockets is released under the BSD license.






another one 



docs Build Status codecov PyPI Downloads PyPI version License Code style: black

websocket-client
websocket-client is a WebSocket client for Python. It provides access to low level APIs for WebSockets. websocket-client implements version hybi-13 of the WebSocket protocol. This client does not currently support the permessage-deflate extension from RFC 7692.

Documentation
This project's documentation can be found at https://websocket-client.readthedocs.io/

Contributing
Please see the contribution guidelines

Installation
You can use pip install websocket-client to install, or pip install -e . to install from a local copy of the code. This module is tested on Python 3.10+.

There are several optional dependencies that can be installed to enable specific websocket-client features.

To install python-socks for proxy usage and wsaccel for a minor performance boost, use: pip install websocket-client[optional]
To install websockets to run unit tests using the local echo server, use: pip install websocket-client[test]
To install Sphinx and sphinx_rtd_theme to build project documentation, use: pip install websocket-client[docs]
While not a strict dependency, rel is useful when using run_forever with automatic reconnect. Install rel with pip install rel.

Footnote: Some shells, such as zsh, require you to escape the [ and ] characters with a \.

Usage Tips
Check out the documentation's FAQ for additional guidelines: https://websocket-client.readthedocs.io/en/latest/faq.html

Known issues with this library include lack of WebSocket Compression support (RFC 7692) and minimal threading documentation/support.

Performance
The send and validate_utf8 methods can sometimes be bottleneck. You can disable UTF8 validation in this library (and receive a performance enhancement) with the skip_utf8_validation parameter. If you want to get better performance, install wsaccel. While websocket-client does not depend on wsaccel, it will be used if available. wsaccel doubles the speed of UTF8 validation and offers a very minor 10% performance boost when masking the payload data as part of the send process. Numpy used to be a suggested performance enhancement alternative, but issue #687 found it didn't help.

Examples
Many more examples are found in the examples documentation.

Long-lived Connection
Most real-world WebSockets situations involve longer-lived connections. The WebSocketApp run_forever loop will automatically try to reconnect to an open WebSocket connection when a network connection is lost if it is provided with:

a dispatcher argument (async dispatcher like rel or pyevent)
a non-zero reconnect argument (delay between disconnection and attempted reconnection)
run_forever provides a variety of event-based connection controls using callbacks like on_message and on_error. run_forever does not automatically reconnect if the server closes the WebSocket gracefully (returning a standard websocket close code). This is the logic behind the decision. Customizing behavior when the server closes the WebSocket should be handled in the on_close callback. This example uses rel for the dispatcher to provide automatic reconnection.

import websocket
import _thread
import time
import rel

def on_message(ws, message):
    print(message)

def on_error(ws, error):
    print(error)

def on_close(ws, close_status_code, close_msg):
    print("### closed ###")

def on_open(ws):
    print("Opened connection")

if __name__ == "__main__":
    websocket.enableTrace(True)
    ws = websocket.WebSocketApp("wss://api.gemini.com/v1/marketdata/BTCUSD",
                              on_open=on_open,
                              on_message=on_message,
                              on_error=on_error,
                              on_close=on_close)

    ws.run_forever(dispatcher=rel, reconnect=5)  # Set dispatcher to automatic reconnection, 5 second reconnect delay if connection closed unexpectedly
    rel.signal(2, rel.abort)  # Keyboard Interrupt
    rel.dispatch()
Short-lived Connection
This is if you want to communicate a short message and disconnect immediately when done. For example, if you want to confirm that a WebSocket server is running and responds properly to a specific request.

from websocket import create_connection

ws = create_connection("ws://echo.websocket.events/")
print(ws.recv())
print("Sending 'Hello, World'...")
ws.send("Hello, World")
print("Sent")
print("Receiving...")
result =  ws.recv()
print("Received '%s'" % result)
ws.close()