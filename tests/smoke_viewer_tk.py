#!/usr/bin/env python3
"""Short real-Tk smoke using a synthetic white pixel and an injected fake reader.
Not collected by unittest discover. No .env/config read, HTTP, gateway, CLI, QR,
image file, screenshot, focus forcing or application interaction.
The test window remains withdrawn; this tests real Tk decoding/widget state,
not visible layout, phone scanning, Windows ACLs or WhatsApp.

Run from a Windows graphical session with the existing Python:
    python tests/smoke_viewer_tk.py
Exit0 passed; exit2 graphics/Tk unavailable; exit1 failed; exit124 watchdog.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import struct
import sys
import threading
import time
import zlib

LIMIT_SECONDS = 4.5


def synthetic_pixel() -> bytes:
    """One white RGB pixel; deliberately not a QR code."""
    def chunk(kind, data):
        crc = zlib.crc32(kind + data) & 0xffffffff
        return struct.pack('>I', len(data)) + kind + data + struct.pack('>I', crc)
    return (b'\x89PNG\r\n\x1a\n'
            + chunk(b'IHDR', struct.pack('>IIBBBBB', 1, 1, 8, 2, 0, 0, 0))
            + chunk(b'IDAT', zlib.compress(b'\0\xff\xff\xff'))
            + chunk(b'IEND', b''))


def main() -> int:
    started = time.monotonic()
    done = threading.Event()
    steps = []
    root = None
    outcome = {'status': 'failed', 'reason': 'incomplete', 'exit_code': 1}

    def report(status, reason, code):
        data = {'status': status, 'reason': reason, 'exit_code': code,
                'platform': sys.platform, 'steps': list(steps),
                'elapsed_ms': round((time.monotonic() - started) * 1000),
                'watchdog_ms': round(LIMIT_SECONDS * 1000), 'window': 'withdrawn',
                'synthetic_only': True, 'real_qr_generated': False,
                'network_used': False, 'private_config_read': False,
                'screenshot_taken': False}
        # Exception messages/paths, image data and secrets are never reported.
        os.write(1, (json.dumps(data, ensure_ascii=True) + '\n').encode('utf-8'))

    def watchdog():
        if not done.is_set():
            done.set()
            try:
                report('failed', 'hard_timeout', 124)
            finally:
                # Only this dedicated smoke process; never kills other applications.
                os._exit(124)

    timer = threading.Timer(LIMIT_SECONDS, watchdog)
    timer.daemon = True
    timer.start()

    def finish(status, reason, code):
        nonlocal root
        if done.is_set():
            return
        outcome.update(status=status, reason=reason, exit_code=code)
        # Keep watchdog active while Tcl/Tk tears down, in case teardown hangs.
        if root is not None:
            try:
                root.destroy()
            except Exception:
                pass
            root = None
        if not done.is_set():
            done.set()
            timer.cancel()
            report(status, reason, code)

    try:
        if len(sys.argv) != 1:
            finish('failed', 'arguments_not_allowed', 1)
            return 1
        # No graphical attempt in headless Linux. Windows/macOS do not use DISPLAY.
        if sys.platform not in ('win32', 'darwin') and not os.environ.get('DISPLAY'):
            finish('blocked', 'graphical_session_unavailable', 2)
            return 2
        try:
            import tkinter as tk
        except ImportError:
            finish('blocked', 'tkinter_unavailable', 2)
            return 2
        try:
            root = tk.Tk()
            root.withdraw()  # Do not raise, focus or project a window over another app.
        except tk.TclError:
            finish('blocked', 'graphical_session_unavailable', 2)
            return 2
        steps.append({'step': 'real_tk_initialized_withdrawn', 'passed': True,
                      'tk_version': str(tk.TkVersion)})

        sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
        from qr_viewer import PrivateViewer
        from viewer_core import Frame, Result

        pixel = synthetic_pixel()

        class FakeReader:
            calls = 0
            def fetch(self):
                self.calls += 1
                return Result('disconnected')  # No HTTP object is constructed.

        reader = FakeReader()
        viewer = PrivateViewer(root, reader)
        # Production focus/minimize protections stay unchanged; the window is never mapped.
        assert not viewer.enabled and viewer.photo is None
        steps.append({'step': 'private_viewer_fake_reader_injected', 'passed': True})
        generation = 0

        def record(name):
            steps.append({'step': name, 'passed': True})

        def schedule(callback, delay=30):
            def guarded():
                try:
                    callback()
                except Exception as error:
                    steps.append({'step': callback.__name__, 'passed': False,
                                  'error_type': type(error).__name__})
                    finish('failed', 'assertion_or_tk_failure', 1)
            root.after(delay, guarded)

        def display_for(seconds):
            nonlocal generation
            generation += 1
            now = time.monotonic()
            serial = viewer.gate.begin()
            frame = Frame(generation, now + seconds, pixel, now)
            assert viewer.gate.accept(serial, Result('qr_required', frame), now)
            viewer._show(frame)
            assert viewer.photo is not None
            assert viewer.image.cget('image')

        def decode_and_clear():
            display_for(.6)
            assert viewer.photo.width() == viewer.photo.height() == 1
            rgb = viewer.photo.get(0, 0)
            # Real Tcl/Tk returns an RGB tuple; tolerate a Tcl list representation.
            if isinstance(rgb, str):
                rgb = tuple(int(value) for value in rgb.split())
            assert tuple(rgb) == (255, 255, 255)
            record('real_photoimage_png_decode_white_pixel')
            viewer.clear()
            assert viewer.photo is None and not viewer.image.cget('image')
            record('clear_removes_widget_image')
            display_for(.18)
            # Existing production tick must expire the image without another request.
            schedule(check_expired, 260)

        def check_expired():
            assert viewer.photo is None and viewer.gate.frame is None
            assert not viewer.image.cget('image')
            record('production_tick_expires_image')
            display_for(.6)
            viewer.pause()
            assert not viewer.enabled and viewer.photo is None and viewer.gate.frame is None
            record('pause_hides_and_invalidates')
            viewer.resume()
            assert viewer.enabled and viewer.photo is None and viewer.gate.frame is None
            record('resume_starts_hidden')
            # Only the injected fake reader runs; exercise the actual queued worker path.
            schedule(check_disconnected, 160)

        def check_disconnected():
            assert reader.calls >= 1
            assert viewer.photo is None and viewer.gate.frame is None
            assert 'desconectado' in viewer.message.get().casefold()
            record('fake_disconnected_state_is_visible_without_image')
            viewer.pause()
            old_serial = viewer.gate.serial
            viewer.resume()
            now = time.monotonic()
            stale = Frame(generation + 1, now + .5, pixel, now)
            assert not viewer.gate.accept(old_serial, Result('qr_required', stale), now)
            record('late_worker_generation_rejected')
            viewer.pause()
            viewer.close()
            assert viewer.closed and viewer.gate.closed and viewer.photo is None
            record('close_clears_state_and_destroys_window')
            finish('passed', 'synthetic_tk_smoke_complete', 0)

        schedule(decode_and_clear)
        root.after(3500, lambda: finish('failed', 'soft_timeout', 1))
        root.mainloop()
        if not done.is_set():
            finish('failed', 'event_loop_ended_early', 1)
        return outcome['exit_code']
    except Exception as error:
        steps.append({'step': 'unexpected_failure', 'passed': False,
                      'error_type': type(error).__name__})
        finish('failed', 'unexpected_failure', 1)
        return 1
    finally:
        if not done.is_set():
            finish('failed', 'incomplete', 1)


if __name__ == '__main__':
    raise SystemExit(main())
