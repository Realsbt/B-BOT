#!/usr/bin/env python3
"""Collect E6 TCP-close and direct-command watchdog evidence for B-BOT."""

from __future__ import annotations

import argparse
import csv
import os
import queue
import socket
import statistics
import threading
import time
from dataclasses import dataclass

import serial


@dataclass
class SerialEvent:
    t_ns: int
    line: str


def percentile(values: list[float], p: float) -> float:
    ordered = sorted(values)
    if not ordered:
        return float("nan")
    k = (len(ordered) - 1) * p / 100.0
    lo = int(k)
    hi = min(lo + 1, len(ordered) - 1)
    frac = k - lo
    return ordered[lo] * (1.0 - frac) + ordered[hi] * frac


def recv_tcp_line(sock: socket.socket, timeout: float = 3.0) -> str:
    sock.settimeout(timeout)
    data = bytearray()
    while True:
        b = sock.recv(1)
        if not b:
            raise RuntimeError("TCP connection closed before newline")
        data.extend(b)
        if b == b"\n":
            return data.decode(errors="replace").strip()


def connect_with_retry(host: str, port: int, attempts: int = 20) -> socket.socket:
    last_exc: Exception | None = None
    for _ in range(attempts):
        try:
            return socket.create_connection((host, port), timeout=3.0)
        except Exception as exc:
            last_exc = exc
            time.sleep(0.5)
    raise RuntimeError(f"Could not connect to {host}:{port}") from last_exc


def serial_reader(ser: serial.Serial, out_q: queue.Queue[SerialEvent], stop: threading.Event) -> None:
    while not stop.is_set():
        raw = ser.readline()
        if not raw:
            continue
        out_q.put(SerialEvent(time.monotonic_ns(), raw.decode(errors="replace").strip()))


def drain_serial_events(q: queue.Queue[SerialEvent], sink: list[SerialEvent]) -> None:
    while True:
        try:
            sink.append(q.get_nowait())
        except queue.Empty:
            return


def wait_for_line(
    q: queue.Queue[SerialEvent],
    sink: list[SerialEvent],
    pattern: str,
    timeout_s: float,
) -> SerialEvent | None:
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        try:
            event = q.get(timeout=0.1)
        except queue.Empty:
            continue
        sink.append(event)
        if pattern in event.line:
            return event
    return None


def send_command(sock: socket.socket, command: str) -> tuple[int, int, str]:
    payload = (command + "\n").encode()
    t_send = time.monotonic_ns()
    sock.sendall(payload)
    ack = recv_tcp_line(sock, timeout=3.0)
    t_ack = time.monotonic_ns()
    return t_send, t_ack, ack


def run_tcp_close_trials(args, q: queue.Queue[SerialEvent], serial_events: list[SerialEvent]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for trial in range(1, args.trials + 1):
        drain_serial_events(q, serial_events)
        with connect_with_retry(args.host, args.port) as sock:
            hello = recv_tcp_line(sock, timeout=3.0)
            t_send, t_ack, ack = send_command(sock, args.close_command)
            t_close = time.monotonic_ns()
        event = wait_for_line(q, serial_events, "client_drop", timeout_s=3.0)
        rows.append(
            {
                "trial": trial,
                "command": args.close_command,
                "hello": hello,
                "ack": ack,
                "pc_send_ns": t_send,
                "pc_ack_ns": t_ack,
                "pc_close_ns": t_close,
                "serial_event_ns": event.t_ns if event else "",
                "close_to_client_drop_ms": (event.t_ns - t_close) / 1e6 if event else "",
                "event_found": bool(event),
                "event_line": event.line if event else "",
            }
        )
        time.sleep(0.4)
    return rows


def run_direct_watchdog_trials(args, q: queue.Queue[SerialEvent], serial_events: list[SerialEvent]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for trial in range(1, args.trials + 1):
        drain_serial_events(q, serial_events)
        with connect_with_retry(args.host, args.port) as sock:
            hello = recv_tcp_line(sock, timeout=3.0)
            t_send, t_ack, ack = send_command(sock, args.watchdog_command)
            event = wait_for_line(q, serial_events, "DRIVE watchdog: direct teleop stopped", timeout_s=2.0)
            # End each trial safely and avoid waiting for the TCP idle watchdog.
            try:
                send_command(sock, "DRIVE,0,0")
                send_command(sock, "YAWRATE,0")
                send_command(sock, "QUEUE_STOP")
            except Exception:
                pass
        rows.append(
            {
                "trial": trial,
                "command": args.watchdog_command,
                "hello": hello,
                "ack": ack,
                "pc_send_ns": t_send,
                "pc_ack_ns": t_ack,
                "serial_event_ns": event.t_ns if event else "",
                "send_to_watchdog_ms": (event.t_ns - t_send) / 1e6 if event else "",
                "ack_to_watchdog_ms": (event.t_ns - t_ack) / 1e6 if event else "",
                "event_found": bool(event),
                "event_line": event.line if event else "",
            }
        )
        time.sleep(0.4)
    return rows


def write_dict_csv(path: str, rows: list[dict[str, object]], header_comment: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="") as f:
        f.write(header_comment + "\n")
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def build_summary(close_rows: list[dict[str, object]], watchdog_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    close_lat = [float(r["close_to_client_drop_ms"]) for r in close_rows if r["event_found"]]
    watchdog_send_lat = [float(r["send_to_watchdog_ms"]) for r in watchdog_rows if r["event_found"]]
    watchdog_ack_lat = [float(r["ack_to_watchdog_ms"]) for r in watchdog_rows if r["event_found"]]

    rows: list[dict[str, object]] = [
        {"case": "tcp_close", "metric": "n", "value": len(close_rows), "unit": "trials"},
        {"case": "tcp_close", "metric": "events_found", "value": len(close_lat), "unit": "count"},
        {"case": "tcp_close", "metric": "median_close_to_client_drop", "value": statistics.median(close_lat), "unit": "ms"},
        {"case": "tcp_close", "metric": "p95_close_to_client_drop", "value": percentile(close_lat, 95), "unit": "ms"},
        {"case": "tcp_close", "metric": "max_close_to_client_drop", "value": max(close_lat), "unit": "ms"},
        {"case": "direct_drive_watchdog", "metric": "n", "value": len(watchdog_rows), "unit": "trials"},
        {"case": "direct_drive_watchdog", "metric": "events_found", "value": len(watchdog_send_lat), "unit": "count"},
        {"case": "direct_drive_watchdog", "metric": "median_send_to_watchdog", "value": statistics.median(watchdog_send_lat), "unit": "ms"},
        {"case": "direct_drive_watchdog", "metric": "p95_send_to_watchdog", "value": percentile(watchdog_send_lat, 95), "unit": "ms"},
        {"case": "direct_drive_watchdog", "metric": "median_ack_to_watchdog", "value": statistics.median(watchdog_ack_lat), "unit": "ms"},
        {"case": "direct_drive_watchdog", "metric": "p95_ack_to_watchdog", "value": percentile(watchdog_ack_lat, 95), "unit": "ms"},
        {"case": "direct_drive_watchdog", "metric": "max_send_to_watchdog", "value": max(watchdog_send_lat), "unit": "ms"},
    ]
    return rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="172.20.10.4")
    parser.add_argument("--port", type=int, default=23)
    parser.add_argument("--serial-port", default="/dev/ttyUSB0")
    parser.add_argument("--baud", type=int, default=115200)
    parser.add_argument("--trials", type=int, default=10)
    parser.add_argument("--close-command", default="DRIVE,250,0")
    parser.add_argument("--watchdog-command", default="DRIVE,250,0")
    parser.add_argument("--out-dir", default="Report/appendices/E_data/E6_watchdog_fault_injection")
    args = parser.parse_args()

    os.makedirs(args.out_dir, exist_ok=True)

    q: queue.Queue[SerialEvent] = queue.Queue()
    stop = threading.Event()
    serial_events: list[SerialEvent] = []

    with serial.Serial(args.serial_port, args.baud, timeout=0.1) as ser:
        ser.dtr = False
        ser.rts = False
        ser.reset_input_buffer()
        reader = threading.Thread(target=serial_reader, args=(ser, q, stop), daemon=True)
        reader.start()

        # Opening the serial port can reset some ESP32 boards. Wait and reconnect TCP after.
        time.sleep(2.5)
        close_rows = run_tcp_close_trials(args, q, serial_events)
        watchdog_rows = run_direct_watchdog_trials(args, q, serial_events)

        stop.set()
        reader.join(timeout=1.0)
        drain_serial_events(q, serial_events)

    close_path = os.path.join(args.out_dir, "tcp_close_trials_2026-04-24.csv")
    watchdog_path = os.path.join(args.out_dir, "direct_drive_watchdog_trials_2026-04-24.csv")
    serial_path = os.path.join(args.out_dir, "serial_events_e6_close_watchdog_2026-04-24.csv")
    summary_path = os.path.join(args.out_dir, "watchdog_close_direct_summary_2026-04-24.csv")

    write_dict_csv(close_path, close_rows, "# source=measured_tcp_close_fault_injection, provisional=false")
    write_dict_csv(watchdog_path, watchdog_rows, "# source=measured_direct_drive_watchdog, provisional=false")

    with open(serial_path, "w", newline="") as f:
        f.write("# source=serial_log_for_e6_tcp_close_and_direct_watchdog, provisional=false\n")
        writer = csv.DictWriter(f, fieldnames=["t_ns", "line"])
        writer.writeheader()
        writer.writerows({"t_ns": e.t_ns, "line": e.line} for e in serial_events)

    summary_rows = build_summary(close_rows, watchdog_rows)
    with open(summary_path, "w", newline="") as f:
        f.write("# source=measured_e6_close_direct_summary, provisional=false\n")
        writer = csv.DictWriter(f, fieldnames=["case", "metric", "value", "unit"])
        writer.writeheader()
        writer.writerows(summary_rows)

    for row in summary_rows:
        print(f"{row['case']},{row['metric']},{row['value']},{row['unit']}")
    print(f"wrote {close_path}")
    print(f"wrote {watchdog_path}")
    print(f"wrote {serial_path}")
    print(f"wrote {summary_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
