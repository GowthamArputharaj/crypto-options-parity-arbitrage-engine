from arbitrage_engine import process_data
from websocket import run_websocket


def main():
    print("Initializing Live Stream Real-Time Parity Check...")
    print("-" * 10)
    run_websocket(handler=process_data)


if __name__ == "__main__":
    main()
