#!/usr/bin/env python3
"""Collect supplementary O3 command-arbitration evidence on the ESP32 board.

The test validates firmware command-source arbitration at controller-board level.
It does not require the drivetrain to be powered, and it should be run with the
robot physically supported if motors are connected.
"""

from __future__ import annotations

import argparse
import csv
import glob
import queue
import socket
import sys
import threading
import time
from dataclasses import dataclass
from pathlib import Path

try:
    import serial
except ImportError:  # pragma: no cover - environment dependency
    serial = None


DEFAULT_HOST = "wheeleg.local"
DEFAULT_PORT = 23
DEFAULT_BAUD = 115200
SERIAL_GLOBS = ("/dev/ttyUSB*", "/dev/ttyACM*")


@dataclass
class SerialEvent:
    t_s: float
    line: str


def now_stamp() -> str:
    return time.strftime("%Y-%m-%d_%H%M%S")


def recv_tcp_line(sock: socket.socket, timeout_s: float = 3.0) -> str:
    sock.settimeout(timeout_s)
    buf = bytearray()
    while True:
        chunk = sock.recv(1)
        if not chunk:
            break
        if chunk in (b"\n", b"\r"):
            if buf:
                break
            continue
        buf.extend(chunk)
    return buf.decode("utf-8", errors="replace").strip()


def connect_tcp(host: str, port: int, timeout_s: float) -> socket.socket:
    sock = socket.create_connection((host, port), timeout=timeout_s)
    sock.settimeout(timeout_s)
    return sock


def send_command(sock: socket.socket, command: str, timeout_s: float) -> tuple[str, float, float]:
    sent_s = time.time()
    sock.sendall((command.strip() + "\n").encode("utf-8"))
    ack = recv_tcp_line(sock, timeout_s)
    ack_s = time.time()
    return ack, sent_s, ack_s


def discover_serial_port() -> str | None:
    ports: list[str] = []
    for pattern in SERIAL_GLOBS:
        ports.extend(sorted(glob.glob(pattern)))
    return ports[0] if ports else None


def open_serial_port(port: str | None, baud: int):
    if serial is None:
        raise RuntimeError("pyserial is not installed; install it or run from the existing report environment")
    resolved = port or discover_serial_port()
    if not resolved:
        raise RuntimeError("no serial port found under /dev/ttyUSB* or /dev/ttyACM*")
    ser = serial.Serial(resolved, baudrate=baud, timeout=0.1)
    ser.dtr = False
    ser.rts = False
    ser.reset_input_buffer()
    return ser, resolved


def serial_reader(stop: threading.Event, ser, event_q: queue.Queue[SerialEvent], all_events: list[SerialEvent]) -> None:
    while not stop.is_set():
        try:
            raw = ser.readline()
        except Exception as exc:  # pragma: no cover - hardware edge case
            event = SerialEvent(time.time(), f"SERIAL_READ_ERROR: {exc}")
            event_q.put(event)
            all_events.append(event)
            return
        if not raw:
            continue
        line = raw.decode("utf-8", errors="replace").strip()
        if not line:
            continue
        event = SerialEvent(time.time(), line)
        event_q.put(event)
        all_events.append(event)


def wait_for_line(
    event_q: queue.Queue[SerialEvent],
    patterns: tuple[str, ...],
    timeout_s: float,
) -> str:
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        try:
            event = event_q.get(timeout=max(0.05, min(0.25, deadline - time.time())))
        except queue.Empty:
            continue
        if any(pattern in event.line for pattern in patterns):
            return event.line
    return ""


def tcp_session(args: argparse.Namespace) -> tuple[socket.socket, str]:
    sock = connect_tcp(args.host, args.port, args.timeout)
    hello = recv_tcp_line(sock, args.timeout)
    return sock, hello


def ack_ok(ack: str) -> bool:
    return ack.startswith("ACK,")


def run_ble_pc_trial(
    args: argparse.Namespace,
    event_q: queue.Queue[SerialEvent],
    trial: int,
) -> dict[str, str | int]:
    row: dict[str, str | int] = {"trial": trial}
    sock, hello = tcp_session(args)
    try:
        row["hello"] = hello

        ack, _, _ = send_command(sock, "BLE_STATUS", args.timeout)
        row["initial_status_ack"] = ack
        row["initial_status_serial"] = wait_for_line(event_q, ("BLE connected:",), args.serial_timeout)

        ack, _, _ = send_command(sock, "BLE_DISABLE", args.timeout)
        row["disable_ack"] = ack
        row["disable_serial"] = wait_for_line(event_q, ("BLE input disabled via serial",), args.serial_timeout)

        ack, _, _ = send_command(sock, "BLE_STATUS", args.timeout)
        row["disabled_status_ack"] = ack
        row["disabled_status_serial"] = wait_for_line(event_q, ("BLE connected:",), args.serial_timeout)

        ack, _, _ = send_command(sock, "DRIVE,0,0", args.timeout)
        row["neutral_drive_ack"] = ack
        row["neutral_drive_serial"] = wait_for_line(event_q, ("DRIVE set: 0 mm/s, 0 mrad/s",), args.serial_timeout)

        ack, _, _ = send_command(sock, "BLE_ENABLE", args.timeout)
        row["enable_ack"] = ack
        row["enable_serial"] = wait_for_line(event_q, ("BLE input enabled via serial",), args.serial_timeout)

        ack, _, _ = send_command(sock, "BLE_STATUS", args.timeout)
        row["enabled_status_ack"] = ack
        row["enabled_status_serial"] = wait_for_line(event_q, ("BLE connected:",), args.serial_timeout)
    finally:
        sock.close()

    controller_connected = all(
        "BLE connected: yes" in str(row[key])
        for key in ("initial_status_serial", "disabled_status_serial", "enabled_status_serial")
    )
    row["ble_connected"] = "yes" if controller_connected else "no"

    checks = [
        controller_connected,
        ack_ok(str(row["initial_status_ack"])),
        ack_ok(str(row["disable_ack"])),
        ack_ok(str(row["disabled_status_ack"])),
        ack_ok(str(row["neutral_drive_ack"])),
        ack_ok(str(row["enable_ack"])),
        ack_ok(str(row["enabled_status_ack"])),
        "BLE input disabled via serial" in str(row["disable_serial"]),
        "input enabled: no" in str(row["disabled_status_serial"]),
        "DRIVE set: 0 mm/s, 0 mrad/s" in str(row["neutral_drive_serial"]),
        "BLE input enabled via serial" in str(row["enable_serial"]),
        "input enabled: yes" in str(row["enabled_status_serial"]),
    ]
    row["pass"] = "yes" if all(checks) else "no"
    return row


def run_queue_drive_trial(
    args: argparse.Namespace,
    event_q: queue.Queue[SerialEvent],
    trial: int,
) -> dict[str, str | int]:
    row: dict[str, str | int] = {"trial": trial}
    sock, hello = tcp_session(args)
    try:
        row["hello"] = hello

        cleanup_commands = ("BALANCE_OFF", "QUEUE_STOP", "DRIVE,0,0", "YAWRATE,0")
        for command in cleanup_commands:
            ack, _, _ = send_command(sock, command, args.timeout)
            row[f"pre_{command.split(',')[0].lower()}_ack"] = ack
            time.sleep(0.05)

        ack, _, _ = send_command(sock, args.queue_command, args.timeout)
        row["queue_command"] = args.queue_command
        row["queue_command_ack"] = ack
        time.sleep(args.queue_settle)

        ack, _, _ = send_command(sock, "DRIVE,250,0", args.timeout)
        row["blocked_drive_ack"] = ack
        row["blocked_drive_serial"] = wait_for_line(event_q, ("DRIVE ignored: command queue busy",), args.serial_timeout)

        ack, _, _ = send_command(sock, "QUEUE_STOP", args.timeout)
        row["post_queue_stop_ack"] = ack
        time.sleep(0.05)
        ack, _, _ = send_command(sock, "DRIVE,0,0", args.timeout)
        row["post_neutral_drive_ack"] = ack
    finally:
        sock.close()

    checks = [
        ack_ok(str(row["queue_command_ack"])),
        ack_ok(str(row["blocked_drive_ack"])),
        "DRIVE ignored: command queue busy" in str(row["blocked_drive_serial"]),
        ack_ok(str(row["post_queue_stop_ack"])),
        ack_ok(str(row["post_neutral_drive_ack"])),
    ]
    row["pass"] = "yes" if all(checks) else "no"
    return row


def write_csv(path: Path, rows: list[dict[str, str | int]]) -> None:
    if not rows:
        return
    fields: list[str] = []
    for row in rows:
        for key in row:
            if key not in fields:
                fields.append(key)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def write_serial_events(path: Path, events: list[SerialEvent]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=("t_s", "line"))
        writer.writeheader()
        for event in events:
            writer.writerow({"t_s": f"{event.t_s:.6f}", "line": event.line})


def pass_count(rows: list[dict[str, str | int]]) -> int:
    return sum(1 for row in rows if row.get("pass") == "yes")


def write_summary(
    path: Path,
    args: argparse.Namespace,
    serial_port: str,
    ble_rows: list[dict[str, str | int]],
    queue_rows: list[dict[str, str | int]],
) -> None:
    lines = [
        "# O3 Arbitration Supplement Summary",
        "",
        f"- Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}",
        f"- TCP target: {args.host}:{args.port}",
        f"- Serial port: {serial_port} at {args.baud} baud",
        f"- BLE/PC gate trials: {pass_count(ble_rows)}/{len(ble_rows)} pass",
        f"- Queue/DRIVE arbitration trials: {pass_count(queue_rows)}/{len(queue_rows)} pass",
        "",
        "Interpretation:",
        "- BLE/PC gate evidence is based on BLE_DISABLE, BLE_STATUS, neutral DRIVE, BLE_ENABLE, and BLE_STATUS serial traces.",
        "- Queue/DRIVE evidence requires the serial line `DRIVE ignored: command queue busy`; TCP ACK alone is not sufficient because ignored commands still return ACK at transport level.",
        "- This is controller-board arbitration evidence. It does not replace full robot motion-safety validation.",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default=DEFAULT_HOST, help="ESP32 TCP host or IP address")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="ESP32 TCP command port")
    parser.add_argument("--serial-port", default=None, help="ESP32 USB serial port; auto-detected if omitted")
    parser.add_argument("--baud", type=int, default=DEFAULT_BAUD, help="serial baud rate")
    parser.add_argument("--trials", type=int, default=5, help="trials per arbitration case")
    parser.add_argument("--timeout", type=float, default=3.0, help="TCP command timeout in seconds")
    parser.add_argument("--serial-timeout", type=float, default=3.0, help="serial evidence timeout in seconds")
    parser.add_argument(
        "--startup-delay",
        type=float,
        default=2.5,
        help="delay after opening serial because ESP32 boards can reset on USB serial open",
    )
    parser.add_argument("--queue-settle", type=float, default=0.20, help="settle time after queue command")
    parser.add_argument("--queue-command", default="FORWARD,1,2", help="low-duty queue command used in O3-B")
    parser.add_argument("--out-dir", type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument("--only", choices=("all", "ble", "queue"), default="all")
    parser.add_argument(
        "--confirm-board-only",
        action="store_true",
        help="confirm the robot is supported or drivetrain power is removed",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.confirm_board_only:
        print(
            "Refusing to run until --confirm-board-only is supplied. "
            "Support the robot or remove drivetrain power before running this bench test.",
            file=sys.stderr,
        )
        return 2

    args.out_dir.mkdir(parents=True, exist_ok=True)
    ser, serial_port = open_serial_port(args.serial_port, args.baud)
    stop = threading.Event()
    event_q: queue.Queue[SerialEvent] = queue.Queue()
    events: list[SerialEvent] = []
    reader = threading.Thread(target=serial_reader, args=(stop, ser, event_q, events), daemon=True)
    reader.start()
    time.sleep(args.startup_delay)

    stamp = now_stamp()
    ble_rows: list[dict[str, str | int]] = []
    queue_rows: list[dict[str, str | int]] = []
    try:
        if args.only in ("all", "ble"):
            for trial in range(1, args.trials + 1):
                print(f"[BLE/PC] trial {trial}/{args.trials}")
                ble_rows.append(run_ble_pc_trial(args, event_q, trial))
        if args.only in ("all", "queue"):
            for trial in range(1, args.trials + 1):
                print(f"[QUEUE/DRIVE] trial {trial}/{args.trials}")
                queue_rows.append(run_queue_drive_trial(args, event_q, trial))
    finally:
        stop.set()
        reader.join(timeout=1.0)
        ser.close()

    if ble_rows:
        write_csv(args.out_dir / f"o3_ble_pc_arbitration_{stamp}.csv", ble_rows)
    if queue_rows:
        write_csv(args.out_dir / f"o3_queue_drive_arbitration_{stamp}.csv", queue_rows)
    write_serial_events(args.out_dir / f"o3_serial_events_{stamp}.csv", events)
    write_summary(args.out_dir / f"o3_arbitration_summary_{stamp}.md", args, serial_port, ble_rows, queue_rows)

    print(f"Wrote O3 arbitration evidence to {args.out_dir}")
    if ble_rows:
        print(f"BLE/PC pass: {pass_count(ble_rows)}/{len(ble_rows)}")
    if queue_rows:
        print(f"QUEUE/DRIVE pass: {pass_count(queue_rows)}/{len(queue_rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
