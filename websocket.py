import asyncio
import json

import websockets

from arbitrage_engine import process_data
from config import URL


async def WebSocket(handler=process_data, message_limit=None):
    async with websockets.connect(URL) as ws:
        request = {
            "method": "SUBSCRIBE",
            "params": [
                "btcusdt@optionMarkPrice"
            ],
            "id": 1
        }

        await ws.send(json.dumps(request))

        print("Connected")
        print("Subscribed to BTC option mark-price stream")
        print()
        limit = 0

        async for message in ws:
            json_data = json.loads(message)

            if "result" in json_data:
                print("Initiating..")
                if json_data["result"] is None:
                    print("Initiated..")
                continue

            if "stream" not in json_data:
                continue

            limit = limit + 1
            print(limit)

            #
            data = json_data["data"]
            print("Received is: ", len(data) if isinstance(data, list) else 1)
            handler(data)

            if message_limit is not None and limit >= message_limit:
                break


def run_websocket(handler=process_data, message_limit=None):
    asyncio.run(WebSocket(handler=handler, message_limit=message_limit))
