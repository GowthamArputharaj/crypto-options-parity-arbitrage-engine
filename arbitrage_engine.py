from ParityArbitrageScanner import ParityArbitrageScanner
from config import LATENCY_THRESHOLD_MS, MIN_PROFIT_USD


class ArbitrageEngine:
    """Owns one scanner instance so option pair cache survives across websocket ticks."""

    def __init__(self, latency_threshold_ms=LATENCY_THRESHOLD_MS, min_profit_usd=MIN_PROFIT_USD):
        self.scanner = ParityArbitrageScanner(
            latency_threshold_ms=latency_threshold_ms,
            min_profit_usd=min_profit_usd,
        )

    def process_data(self, stream_payload):
        """Process one Binance payload or a list of payloads from the stream."""
        packets = stream_payload if isinstance(stream_payload, list) else [stream_payload]

        for packet in packets:
            self.scanner.process_packet(packet)


_default_engine = ArbitrageEngine()


def process_data(stream_payload):
    """Compatibility function used by websocket.py."""
    _default_engine.process_data(stream_payload)
