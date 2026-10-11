"""Source adapter boundary for private portfolio imports.

The only implemented adapter accepts Atlas's normalized JSON contract. Broker
formats remain unimplemented until representative, redacted source evidence is
available.
"""
import json
from typing import Protocol

MAX_SOURCE_BYTES = 1_000_000


class PortfolioSourceAdapter(Protocol):
    """Convert exact source bytes into an Atlas import-envelope mapping."""

    name: str

    def normalize(self, source: bytes) -> dict:
        ...


class NormalizedJsonAdapter:
    """Parse UTF-8 JSON that is already in Atlas's normalized schema."""

    name = 'normalized-json-v1'

    def normalize(self, source: bytes) -> dict:
        if not isinstance(source, bytes) or not source or len(source) > MAX_SOURCE_BYTES:
            raise ValueError('invalid_source_bytes')
        try:
            payload = json.loads(source.decode('utf-8'))
        except (UnicodeDecodeError, json.JSONDecodeError):
            raise ValueError('invalid_source_encoding_or_json') from None
        if not isinstance(payload, dict):
            raise ValueError('invalid_source_root')
        return payload
