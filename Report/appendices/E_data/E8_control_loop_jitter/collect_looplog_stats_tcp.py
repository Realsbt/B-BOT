#!/usr/bin/env python3
"""Collect E8 loop timing summary and histogram from ESP32 over TCP."""

from __future__ import annotations

import argparse
import csv
import os
import socket
import time


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
    parser.add_argument("--bin-width-us", type=int, default=100)
    parser.add_argument("--summary", default="Report/appendices/E_data/E8_control_loop_jitter/looplog_stats_15000_summary_2026-04-24.csv")
    parser.add_argument("--histogram", default="Report/appendices/E_data/E8_control_loop_jitter/looplog_stats_15000_histogram_2026-04-24.csv")
    args = parser.parse_args()

    os.makedirs(os.path.dirname(args.summary), exist_ok=True)

    with connect_with_retry(args.host, args.port) as sock:
        hello_start = recv_line(sock)
        send_line(sock, f"LOOPLOG_START,{args.samples}")
        start_ack = recv_line(sock)

    wait_s = max(5.0, args.samples * 0.004 + 5.0)
    time.sleep(wait_s)

    stats: list[dict[str, str]] = []
    hist: list[dict[str, str]] = []
    with connect_with_retry(args.host, args.port) as sock:
        hello_stats = recv_line(sock)
        send_line(sock, f"LOOPLOG_STATS_TCP,{args.bin_width_us}")
        stats_begin = ""
        stats_end = ""
        ack_line = ""
        while True:
            line = recv_line(sock, timeout=10.0)
            if line.startswith("LOOPLOG_STATS_BEGIN"):
                stats_begin = line
            elif line.startswith("LOOPSTAT"):
                _, metric, value, unit = line.split(",", 3)
                stats.append({"metric": metric, "value": value, "unit": unit})
            elif line.startswith("LOOPHIST"):
                _, start_us, end_us, count = line.split(",", 3)
                hist.append({"bin_start_us": start_us, "bin_end_us": end_us, "count": count})
            elif line.startswith("LOOPLOG_STATS_END"):
                stats_end = line
            elif line.startswith("ACK") or line.startswith("NACK"):
                ack_line = line
                break

    sample_values = [row for row in stats if row["metric"] == "samples"]
    measured_samples = int(sample_values[0]["value"]) if sample_values else 0
    if measured_samples != args.samples:
        raise RuntimeError(f"Expected {args.samples} samples, got {measured_samples}")

    with open(args.summary, "w", newline="") as f:
        f.write("# source=measured_ctrl_looplog_tcp_stats, provisional=false\n")
        f.write(f"# hello_start={hello_start}\n")
        f.write(f"# start_ack={start_ack}\n")
        f.write(f"# wait_s={wait_s}\n")
        f.write(f"# hello_stats={hello_stats}\n")
        f.write(f"# stats_begin={stats_begin}\n")
        f.write(f"# stats_end={stats_end}\n")
        f.write(f"# stats_ack={ack_line}\n")
        writer = csv.DictWriter(f, fieldnames=["metric", "value", "unit"])
        writer.writeheader()
        writer.writerows(stats)

    with open(args.histogram, "w", newline="") as f:
        f.write("# source=measured_ctrl_looplog_tcp_histogram, provisional=false\n")
        f.write(f"# bin_width_us={args.bin_width_us}\n")
        writer = csv.DictWriter(f, fieldnames=["bin_start_us", "bin_end_us", "count"])
        writer.writeheader()
        writer.writerows(hist)

    for row in stats:
        print(f"{row['metric']},{row['value']},{row['unit']}")
    print(f"histogram_bins,{len(hist)},count")
    print(f"wrote {args.summary}")
    print(f"wrote {args.histogram}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
