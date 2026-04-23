#!/usr/bin/env python3
"""PC WASD keyboard teleop over WiFi TCP for the wheeleg robot.

Protocol lines (see pc-wifi-keyboard-control-plan.md):
    DRIVE,<speed_milli_mps>,<yaw_mrad_s>    direct teleop, bypasses queue
    YAWRATE,<mrad_s>                        yaw-only direct
    BLE_DISABLE / BLE_ENABLE                arbitration
    QUEUE_STOP                              stop queued actions

Safety:
    - On start:  BLE_DISABLE -> DRIVE,0,0 -> stream
    - On exit:   DRIVE,0,0 -> YAWRATE,0 -> BLE_ENABLE (always, via atexit + signals)
    - If robot has not been standup/BALANCE_ON, DRIVE has no effect — warn user.

Usage:
    python3 keyboard_drive.py                              # uses mDNS wheeleg.local
    python3 keyboard_drive.py --host 192.168.1.23          # fallback if mDNS unavailable
    python3 keyboard_drive.py --host wheeleg.local --rate 20
"""

from __future__ import annotations

import argparse
import atexit
import os
import select
import signal
import socket
import sys
import termios
import time
import tty

SEND_RATE_HZ_DEFAULT = 20
SPEED_PRESETS_MM_S = {"1": 150, "2": 250, "3": 350}  # slow / medium / bench-only
YAW_MRAD_S = 600
HELP = """
Keys:
  W/S    forward / backward
  A/D    turn left / right
  Space  hard stop (DRIVE,0,0 + QUEUE_STOP)
  1/2/3  speed preset: slow / medium / bench-only
  H      reprint help
  Q      quit cleanly
""".strip()


class Teleop:
    def __init__(self, host: str, port: int, rate_hz: int):
        self.host = host
        self.port = port
        self.period = 1.0 / rate_hz
        self.sock: socket.socket | None = None
        self.speed_mm_s = SPEED_PRESETS_MM_S["1"]
        self.active_keys: set[str] = set()
        self._closed = False

    def connect(self):
        print(f"[wifi-teleop] connecting to {self.host}:{self.port} ...")
        self.sock = socket.create_connection((self.host, self.port), timeout=3.0)
        self.sock.settimeout(0.1)
        print("[wifi-teleop] connected")
        # Handshake: disable BLE first, then zero outputs.
        self._send("BLE_DISABLE")
        time.sleep(0.05)
        self._send("DRIVE,0,0")

    def _send(self, line: str):
        if not self.sock:
            return
        try:
            self.sock.sendall((line + "\n").encode("ascii"))
        except OSError as e:
            print(f"[wifi-teleop] send failed: {e}", file=sys.stderr)

    def close(self):
        if self._closed:
            return
        self._closed = True
        print("\n[wifi-teleop] shutting down: DRIVE,0,0 / YAWRATE,0 / BLE_ENABLE")
        try:
            self._send("DRIVE,0,0")
            time.sleep(0.05)
            self._send("YAWRATE,0")
            time.sleep(0.05)
            self._send("BLE_ENABLE")
            time.sleep(0.05)
        finally:
            if self.sock:
                try:
                    self.sock.shutdown(socket.SHUT_RDWR)
                except OSError:
                    pass
                self.sock.close()
                self.sock = None

    def _compute_drive(self) -> tuple[int, int]:
        fwd = ("w" in self.active_keys) - ("s" in self.active_keys)
        yaw = ("a" in self.active_keys) - ("d" in self.active_keys)
        return fwd * self.speed_mm_s, yaw * YAW_MRAD_S

    def handle_key(self, ch: str) -> bool:
        """Return False to quit."""
        low = ch.lower()
        if low == "q":
            return False
        if low == "h":
            print(HELP)
            return True
        if low == " " or ch == " ":
            print("[wifi-teleop] SPACE -> hard stop")
            self.active_keys.clear()
            self._send("DRIVE,0,0")
            self._send("QUEUE_STOP")
            return True
        if low in SPEED_PRESETS_MM_S:
            self.speed_mm_s = SPEED_PRESETS_MM_S[low]
            print(f"[wifi-teleop] speed preset {low} -> {self.speed_mm_s} mm/s")
            return True
        if low in ("w", "a", "s", "d"):
            # Key-repeat toggle: tap once to start, tap again to stop that axis.
            # (Terminal raw mode cannot observe key-up events.)
            if low in self.active_keys:
                self.active_keys.discard(low)
            else:
                # Opposite keys cancel each other on the same axis.
                if low == "w":
                    self.active_keys.discard("s")
                elif low == "s":
                    self.active_keys.discard("w")
                elif low == "a":
                    self.active_keys.discard("d")
                elif low == "d":
                    self.active_keys.discard("a")
                self.active_keys.add(low)
            print(f"[wifi-teleop] active={sorted(self.active_keys)} speed={self.speed_mm_s}")
            return True
        return True

    def run(self):
        fd = sys.stdin.fileno()
        old_attrs = termios.tcgetattr(fd)
        tty.setcbreak(fd)
        try:
            print(HELP)
            print("[wifi-teleop] NOTE: DRIVE only moves the robot if BALANCE is ON.")
            print("[wifi-teleop] If nothing moves, press Xbox A / send BALANCE_ON first.")
            next_tick = time.monotonic()
            while True:
                # Non-blocking key read
                r, _, _ = select.select([sys.stdin], [], [], 0)
                if r:
                    ch = sys.stdin.read(1)
                    if ch == "\x03":  # Ctrl+C
                        break
                    if not self.handle_key(ch):
                        break

                speed, yaw = self._compute_drive()
                self._send(f"DRIVE,{speed},{yaw}")

                next_tick += self.period
                sleep_for = next_tick - time.monotonic()
                if sleep_for > 0:
                    time.sleep(sleep_for)
                else:
                    # Fell behind — realign to now to avoid runaway catch-up.
                    next_tick = time.monotonic()
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_attrs)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--host", default="wheeleg.local",
                    help="Robot IP or mDNS hostname (default: wheeleg.local)")
    ap.add_argument("--port", type=int, default=23)
    ap.add_argument("--rate", type=int, default=SEND_RATE_HZ_DEFAULT, help="Send rate Hz (default 20)")
    args = ap.parse_args()

    teleop = Teleop(args.host, args.port, args.rate)

    # Always clean up: DRIVE,0,0 + YAWRATE,0 + BLE_ENABLE.
    atexit.register(teleop.close)
    for sig in (signal.SIGTERM, signal.SIGHUP):
        try:
            signal.signal(sig, lambda *_: (teleop.close(), os._exit(0)))
        except (ValueError, OSError):
            pass

    try:
        teleop.connect()
        teleop.run()
    except KeyboardInterrupt:
        pass
    except (socket.timeout, ConnectionError, OSError) as e:
        print(f"[wifi-teleop] connection error: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        teleop.close()


if __name__ == "__main__":
    main()
