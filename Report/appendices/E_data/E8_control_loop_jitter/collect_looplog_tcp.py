#!/usr/bin/env python3
"""Collect B-BOT CtrlBasic_Task loop-period samples through the TCP logger."""

from __future__ import annotations

import argparse
import csv
import os
import socket
import statistics
import time


def percentile(values: list[float], p: float) -> float:
    ordered = sorted(values)
    if not ordered:
        return float("nan")
    k = (len(ordered) - 1) * p / 100.0
    lo = int(k)
    hi = min(lo + 1, len(ordered) - 1)
    frac = k - lo
    return ordered[lo] * (1.0 - frac) + ordered[hi] * frac


def recv_line(sock: socket.socket, timeout: float = 5.0) -> str:
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
            return socket.create_connection((host, port), timeout=5.0)
        except Exception as exc:
            last_exc = exc
            time.sleep(1.0)
    raise RuntimeError(f"Could not connect to {host}:{port}") from last_exc


def send_line(sock: socket.socket, line: str) -> None:
    sock.sendall((line + "\n").encode())


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="172.20.10.4")
    parser.add_argument("--port", type=int, default=23)
    parser.add_argument("--samples", type=int, default=15000)
    parser.add_argument("--keepalive-interval", type=float, default=0.75)
    parser.add_argument("--chunk-size", type=int, default=500)
    parser.add_argument("--output", default="Report/appendices/E_data/E8_control_loop_jitter/looplog_tcp_2026-04-24.csv")
    parser.add_argument("--summary", default="Report/appendices/E_data/E8_control_loop_jitter/looplog_tcp_summary_2026-04-24.csv")
    args = parser.parse_args()

    os.makedirs(os.path.dirname(args.output), exist_ok=True)

    keepalive_acks: list[str] = []
    with connect_with_retry(args.host, args.port) as sock:
        hello_start = recv_line(sock)
        send_line(sock, f"LOOPLOG_START,{args.samples}")
        start_ack = recv_line(sock)

        # Keep the TCP client alive while the loop logger samples in the control task.
        wait_s = max(5.0, args.samples * 0.004 + 5.0)
        end_time = time.monotonic() + wait_s
        while time.monotonic() < end_time:
            time.sleep(min(args.keepalive_interval, max(0.0, end_time - time.monotonic())))
            send_line(sock, "DRIVE,0,0")
            keepalive_acks.append(recv_line(sock))

        # Close the sampling client before dumping. The log buffer is kept in RAM,
        # and reopening per chunk avoids long-lived TCP sessions being dropped.
        sock.close()
        time.sleep(0.5)

        rows: list[dict[str, int]] = []
        hello_dump = ""
        dump_begin = ""
        dump_end = ""
        ack_line = ""
        chunk_headers: list[str] = []
        chunk_ends: list[str] = []
        chunk_acks: list[str] = []
        total_count: int | None = None
        start = 0
        while total_count is None or start < total_count:
            chunk_rows = 0
            for attempt in range(1, 4):
                chunk_temp: list[dict[str, int]] = []
                chunk_rows = 0
                try:
                    with connect_with_retry(args.host, args.port, attempts=5) as dump_sock:
                        current_hello = recv_line(dump_sock)
                        if not hello_dump:
                            hello_dump = current_hello
                        send_line(dump_sock, f"LOOPLOG_DUMP_TCP,{start},{args.chunk_size}")
                        while True:
                            line = recv_line(dump_sock, timeout=10.0)
                            if line.startswith("LOOPLOG_DUMP_BEGIN"):
                                if not dump_begin:
                                    dump_begin = line
                                chunk_headers.append(line)
                                parts = line.split(",")
                                if len(parts) >= 2:
                                    current_total = int(parts[1])
                                    if total_count is None:
                                        total_count = current_total
                                    elif current_total != total_count:
                                        raise RuntimeError(
                                            f"Looplog total changed from {total_count} to {current_total}; "
                                            "ESP32 likely rebooted during dump"
                                        )
                            elif line.startswith("LOOPDT"):
                                _, idx, dt_us = line.split(",", 2)
                                chunk_temp.append({"idx": int(idx), "dt_us": int(dt_us)})
                                chunk_rows += 1
                            elif line.startswith("LOOPLOG_DUMP_END"):
                                dump_end = line
                                chunk_ends.append(line)
                            elif line.startswith("ACK") or line.startswith("NACK"):
                                ack_line = line
                                chunk_acks.append(line)
                                break
                    rows.extend(chunk_temp)
                    break
                except Exception:
                    if attempt == 3:
                        raise
                    time.sleep(0.5)
            if chunk_rows == 0:
                break
            start += chunk_rows

    if not dump_begin or not dump_end:
        raise RuntimeError(f"Incomplete dump: begin={dump_begin!r} end={dump_end!r} rows={len(rows)}")
    if total_count is not None and len(rows) != total_count:
        raise RuntimeError(f"Incomplete looplog rows: expected {total_count}, got {len(rows)}")

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
        f.write("# source=measured_ctrl_looplog_tcp, planning_data=false\n")
        f.write(f"# hello_start={hello_start}\n")
        f.write(f"# start_ack={start_ack}\n")
        f.write(f"# wait_s={wait_s}\n")
        f.write(f"# hello_dump={hello_dump}\n")
        f.write(f"# keepalive_interval={args.keepalive_interval}\n")
        f.write(f"# keepalive_acks={len(keepalive_acks)}\n")
        f.write(f"# chunk_size={args.chunk_size}\n")
        f.write(f"# chunks={len(chunk_headers)}\n")
        f.write(f"# dump_begin={dump_begin}\n")
        f.write(f"# dump_end={dump_end}\n")
        f.write(f"# dump_ack={ack_line}\n")
        writer = csv.DictWriter(f, fieldnames=["idx", "dt_us"])
        writer.writeheader()
        writer.writerows(rows)

    with open(args.summary, "w", newline="") as f:
        f.write("# source=measured_ctrl_looplog_tcp_summary, planning_data=false\n")
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
