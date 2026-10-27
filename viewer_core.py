"""Read-only, loopback-only QR transport and fail-closed clock policy.
No Tk imports: safety logic can be tested without a display.
"""
from __future__ import annotations

import base64
from dataclasses import dataclass, field
import http.client
import json
from pathlib import Path
import re
import stat
import struct
import time

HOST = '127.0.0.1'
PORT = 3210
FRAME_PATH = '/qr/frame'
MAX_RESPONSE = 300_000
MAX_PNG = 200_000
MAX_QR_MS = 15_000
MAX_ROUNDTRIP = 0.75
DISPLAY_LEASE = 0.75
SAFETY_MARGIN = 0.20
REQUEST_TIMEOUT = 1.0
POLL_INTERVAL = 0.50
PNG_SIGNATURE = b'\x89PNG\r\n\x1a\n'
TOKEN_RE = re.compile(r'[a-f0-9]{64}\Z')

class ViewerError(Exception):
    """Static safe error codes only; never include upstream exception details."""

@dataclass(frozen=True)
class Frame:
    generation: int
    deadline: float
    png: bytes = field(repr=False)
    valid_from: float = 0.0

@dataclass(frozen=True)
class Result:
    state: str
    frame: Frame | None = None


def load_token(path: Path) -> str:
    """Read only GATEWAY_TOKEN from the existing private .env; never execute it."""
    try:
        if path.is_symlink() or not path.is_file() or path.stat().st_size > 16_384:
            raise ViewerError('config_unavailable')
        mode = path.stat().st_mode
        # Windows ACLs are not represented by chmod bits; document local ACL verification.
        import os
        if os.name != 'nt' and stat.S_IMODE(mode) & 0o077:
            raise ViewerError('config_permissions')
        values = []
        for line in path.read_text(encoding='utf-8-sig').splitlines():
            if not line.strip() or line.lstrip().startswith('#'):
                continue
            key, separator, value = line.partition('=')
            if key.strip() == 'GATEWAY_TOKEN':
                if not separator:
                    raise ViewerError('config_invalid')
                values.append(value.strip())
        if len(values) != 1 or not TOKEN_RE.fullmatch(values[0]):
            raise ViewerError('config_invalid')
        return values[0]
    except ViewerError:
        raise
    except (OSError, ValueError):
        raise ViewerError('config_unavailable') from None


def validate_png(data: bytes) -> bytes:
    # Bound compressed bytes and decoded dimensions before handing bytes to Tk.
    if not 33 <= len(data) <= MAX_PNG or data[:8] != PNG_SIGNATURE:
        raise ViewerError('invalid_frame')
    length, chunk = struct.unpack('>I4s', data[8:16])
    if length != 13 or chunk != b'IHDR':
        raise ViewerError('invalid_frame')
    width, height, depth, color, compression, filtering, interlace = struct.unpack('>IIBBBBB', data[16:29])
    if not (1 <= width <= 768 and 1 <= height <= 768 and depth in (1,2,4,8,16)
            and color in (0,2,3,4,6) and compression == filtering == 0 and interlace in (0,1)):
        raise ViewerError('invalid_frame')
    return data


def parse_result(payload: bytes, *, started: float, received: float) -> Result:
    """Lease starts BEFORE request, never on arrival, and cannot outlive a poll."""
    if not 0 <= received - started <= MAX_ROUNDTRIP:
        raise ViewerError('slow_response')
    try:
        data = json.loads(payload)
        if not isinstance(data, dict) or type(data.get('protocol')) is not int or data.get('protocol') != 1:
            raise ValueError()
        status = data.get('status')
        if not isinstance(status, str):
            raise ValueError()
        if status != 'qr_required':
            return Result(status if status in {'connected','starting','pairing_in_progress','disconnected','consent_required','allowlist_required','session_review_required','restarting_transport','qr_unavailable','startup_error','storage_error'} else 'unavailable')
        expiry, generation, encoded = data.get('expires_in_ms'), data.get('generation'), data.get('png_base64')
        if type(expiry) is not int or not 0 < expiry <= MAX_QR_MS or type(generation) is not int or not 0 < generation < 2**53:
            return Result('unavailable')
        if not isinstance(encoded, str) or len(encoded) > (MAX_PNG + 2) // 3 * 4:
            raise ValueError()
        png = validate_png(base64.b64decode(encoded, validate=True))
        deadline = min(started + expiry / 1000 - SAFETY_MARGIN, started + DISPLAY_LEASE)
        if received >= deadline:
            return Result('expired')
        return Result('qr_required', Frame(generation, deadline, png, received))
    except ViewerError:
        raise
    except (ValueError, TypeError, KeyError, OverflowError):
        raise ViewerError('invalid_frame') from None


class GatewayReader:
    """Direct HTTPConnection: no proxy handling, redirects, cookies or browser."""
    def __init__(self, token: str, *, clock=time.monotonic, connection_factory=http.client.HTTPConnection):
        if not TOKEN_RE.fullmatch(token):
            raise ViewerError('config_invalid')
        self._token = token
        self._clock = clock
        self._connection_factory = connection_factory

    def fetch(self) -> Result:
        started = self._clock()
        connection = self._connection_factory(HOST, PORT, timeout=REQUEST_TIMEOUT)
        try:
            connection.request('GET', FRAME_PATH, headers={
                'Authorization': 'Bearer ' + self._token, 'Accept': 'application/json',
                'Cache-Control': 'no-store', 'Pragma': 'no-cache', 'Connection': 'close'})
            response = connection.getresponse()
            # http.client does not follow redirects; do not read redirect bodies.
            if response.status in (401, 403):
                raise ViewerError('unauthorized')
            if response.status == 409:
                return Result('unavailable')
            if response.status != 200:
                raise ViewerError('http_unavailable')
            if response.getheader('Content-Type', '').split(';')[0].strip().lower() != 'application/json':
                raise ViewerError('invalid_frame')
            if 'no-store' not in response.getheader('Cache-Control', '').lower():
                raise ViewerError('cache_policy_rejected')
            length = response.getheader('Content-Length')
            if length is not None and (not length.isdecimal() or int(length) > MAX_RESPONSE):
                raise ViewerError('invalid_frame')
            parts, size = [], 0
            while True:
                if self._clock() - started > MAX_ROUNDTRIP:
                    raise ViewerError('slow_response')
                part = response.read1(min(65_536, MAX_RESPONSE + 1 - size))
                if not part:
                    break
                size += len(part)
                if size > MAX_RESPONSE:
                    raise ViewerError('invalid_frame')
                parts.append(part)
            payload = b''.join(parts)
            return parse_result(payload, started=started, received=self._clock())
        except ViewerError:
            raise
        except (OSError, http.client.HTTPException, ValueError):
            raise ViewerError('transport_unavailable') from None
        finally:
            connection.close()


class DisplayGate:
    """Invalidate before each request; reject delayed/stale worker completions."""
    def __init__(self):
        self.serial = 0
        self.frame = None
        self.closed = False
        self.highest_generation = 0

    def begin(self) -> int:
        self.serial += 1
        self.frame = None
        return self.serial

    def accept(self, serial: int, result: Result, now: float) -> bool:
        if self.closed or serial != self.serial:
            return False
        candidate = result.frame
        self.frame = candidate if candidate and candidate.generation >= self.highest_generation and candidate.valid_from <= now < candidate.deadline else None
        if self.frame:
            self.highest_generation = self.frame.generation
        return self.frame is not None

    def visible(self, now: float) -> bool:
        if self.closed or (self.frame and not self.frame.valid_from <= now < self.frame.deadline):
            self.frame = None
        return self.frame is not None

    def hide(self):
        self.begin()

    def close(self):
        self.closed = True
        self.begin()
