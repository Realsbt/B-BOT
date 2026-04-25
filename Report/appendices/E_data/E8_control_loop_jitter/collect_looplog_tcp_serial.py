#!/usr/bin/env python3
"""Collect B-BOT CtrlBasic_Task loop-period samples via TCP command + USB serial."""

from __future__ import annotations

import argparse
import csv
import os
import socket
import statistics
import time

import serial


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


def send_tcp_line(sock: socket.socket, line: str) -> str:
    sock.sendall((line + "\n").encode())
    return recv_tcp_line(sock, timeout=5.0)


def read_serial_line(port: serial.Serial, timeout_s: float) -> str | None:
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        raw = port.readline()
        if raw:
            return raw.decode(errors="replace").strip()
    return None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="172.20.10.4")
    parser.add_argument("--tcp-port", type=int, default=23)
    parser.add_argument("--serial-port", default="/dev/ttyUSB0")
    parser.add_argument("--baud", type=int, default=115200)
    parser.add_argument("--samples", type=int, default=15000)
    parser.add_argument("--output", default="Report/appendices/E_data/E8_control_loop_jitter/looplog_2026-04-24.csv")
    parser.add_argument("--summary", default="Report/appendices/E_data/E8_control_loop_jitter/looplog_summary_2026-04-24.csv")
    args = parser.parse_args()

    os.makedirs(os.path.dirname(args.output), exist_ok=True)

    with serial.Serial(args.serial_port, args.baud, timeout=0.2) as ser:
        # Avoid holding common ESP32 auto-reset lines active after opening the port.
        ser.dtr = False
        ser.rts = False
        ser.reset_input_buffer()
        time.sleep(2.0)

        with socket.create_connection((args.host, args.tcp_port), timeout=5.0) as sock:
            hello = recv_tcp_line(sock, timeout=5.0)
            start_ack = send_tcp_line(sock, f"LOOPLOG_START,{args.samples}")

            done_line = None
            start_deadline = time.monotonic() + max(30.0, args.samples * 0.004 + 30.0)
            while time.monotonic() < start_deadline:
                line = read_serial_line(ser, timeout_s=0.5)
                if line and line.startswith("LOOPLOG_DONE"):
                    done_line = line
                    break

            if not done_line:
                raise RuntimeError("Timed out waiting for LOOPLOG_DONE on serial")

            dump_ack_pending = True
            sock.sendall(b"LOOPLOG_DUMP\n")

            rows: list[dict[str, int]] = []
            dump_begin = None
            dump_end = None
            # 115200 baud plus firmware-side yielding can make large dumps slow.
            # Scale the timeout with sample count so 15000+ line captures complete.
            dump_deadline = time.monotonic() + max(120.0, args.samples * 0.02 + 60.0)
            while time.monotonic() < dump_deadline:
                line = read_serial_line(ser, timeout_s=0.5)
                if not line:
                    continue
                if line.startswith("LOOPLOG_DUMP_BEGIN"):
                    dump_begin = line
                elif line.startswith("LOOPDT"):
                    _, idx, dt_us = line.split(",", 2)
                    rows.append({"idx": int(idx), "dt_us": int(dt_us)})
                elif line.startswith("LOOPLOG_DUMP_END"):
                    dump_end = line
                    break

            if not dump_end:
                raise RuntimeError("Timed out waiting for LOOPLOG_DUMP_END on serial")

            try:
                dump_ack = recv_tcp_line(sock, timeout=5.0) if dump_ack_pending else ""
            except Exception as exc:
                dump_ack = f"ACK_READ_ERROR:{exc!r}"

        dt = [float(r["dt_us"]) for r in rows]
        summary_rows = [
            {"metric": "samples", "value": len(dt), "unit": "count"},
            {"metric": "mean", "value": statistics.mean(dt), "unit": "us"},
            {"metric": "std", "value": statistics.pstdev(dt), "unit": "us"},
            {"metric": "min", "value": min(dt), "unit": "us"},
            {"metric": "p50", "value": percentile(dt, 50), "unit": "us"},
            {"metric": "p95", "value": percentile(dt, 95), "unit": "us"},
            {"metric": "p99", "value": percentile(dt, 99), "unit": "us"},
            {"metric": "p99_9", "value": percentile(dt, 99.9), "unit": "us"},
            {"metric": "max", "value": max(dt), "unit": "us"},
        ]

        with open(args.output, "w", newline="") as f:
            f.write("# source=measured_ctrl_looplog, planning_data=false\n")
            f.write(f"# hello={hello}\n")
            f.write(f"# start_ack={start_ack}\n")
            f.write(f"# done_line={done_line}\n")
            f.write(f"# dump_begin={dump_begin}\n")
            f.write(f"# dump_end={dump_end}\n")
            f.write(f"# dump_ack={dump_ack}\n")
            writer = csv.DictWriter(f, fieldnames=["idx", "dt_us"])
            writer.writeheader()
            writer.writerows(rows)

        with open(args.summary, "w", newline="") as f:
            f.write("# source=measured_ctrl_looplog_summary, planning_data=false\n")
            writer = csv.DictWriter(f, fieldnames=["metric", "value", "unit"])
            writer.writeheader()
            writer.writerows(summary_rows)

        for row in summary_rows:
            print(f"{row['metric']},{row['value']},{row['unit']}")
        print(f"wrote {args.output}")
        print(f"wrote {args.summary}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
