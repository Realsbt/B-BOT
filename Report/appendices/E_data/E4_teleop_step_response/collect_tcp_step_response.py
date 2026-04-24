#!/usr/bin/env python3
"""Collect E4a TCP teleoperation command-entry step response evidence."""

from __future__ import annotations

import argparse
import csv
import os
import socket
import statistics
import time


STEP_CASES = [
    ("speed_150", "DRIVE,150,0", "DRIVE,0,0"),
    ("speed_250", "DRIVE,250,0", "DRIVE,0,0"),
    ("yaw_left_600", "DRIVE,0,600", "DRIVE,0,0"),
    ("yaw_right_600", "DRIVE,0,-600", "DRIVE,0,0"),
]


def percentile(values: list[float], p: float) -> float:
    ordered = sorted(values)
    if not ordered:
        return float("nan")
    k = (len(ordered) - 1) * p / 100.0
    lo = int(k)
    hi = min(lo + 1, len(ordered) - 1)
    frac = k - lo
    return ordered[lo] * (1.0 - frac) + ordered[hi] * frac


def recv_line(sock: socket.socket, timeout: float = 3.0) -> str:
    sock.settimeout(timeout)
    data = bytearray()
    while True:
        b = sock.recv(1)
        if not b:
            raise RuntimeError("TCP connection closed before newline")
        data.extend(b)
        if b == b"\n":
            return data.decode("ascii", errors="replace").strip()


def send_command(sock: socket.socket, command: str) -> tuple[int, int, str]:
    payload = command.rstrip("\r\n")
    t_send = time.monotonic_ns()
    sock.sendall((payload + "\n").encode("ascii"))
    ack = recv_line(sock, timeout=3.0)
    t_ack = time.monotonic_ns()
    return t_send, t_ack, ack


def parse_ack(ack: str) -> dict[str, str]:
    parts = ack.split(",", 3)
    return {
        "ack_kind": parts[0] if len(parts) > 0 else "",
        "esp_ms": parts[1] if len(parts) > 1 else "",
        "rc": parts[2] if len(parts) > 2 else "",
        "ack_command": parts[3] if len(parts) > 3 else "",
        "raw_ack": ack,
    }


def connect(host: str, port: int) -> tuple[socket.socket, str]:
    sock = socket.create_connection((host, port), timeout=3.0)
    sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    hello = recv_line(sock, timeout=3.0)
    return sock, hello


def run(args) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    sock, hello = connect(args.host, args.port)
    try:
        for case_name, step_command, stop_command in STEP_CASES:
            for trial in range(1, args.trials + 1):
                t0_send, t0_ack, ack0 = send_command(sock, stop_command)
                time.sleep(args.settle_s)
                ts_send, ts_ack, ack_step = send_command(sock, step_command)
                time.sleep(args.hold_s)
                te_send, te_ack, ack_stop = send_command(sock, stop_command)
                # Send explicit safe tails for all cases.
                send_command(sock, "YAWRATE,0")
                send_command(sock, "QUEUE_STOP")

                parsed_step = parse_ack(ack_step)
                parsed_stop = parse_ack(ack_stop)
                rows.append({
                    "trial_id": f"{case_name}_{trial:02d}",
                    "case": case_name,
                    "step_command": step_command,
                    "stop_command": stop_command,
                    "hello": hello,
                    "baseline_send_ns": t0_send,
                    "baseline_ack_ns": t0_ack,
                    "step_send_ns": ts_send,
                    "step_ack_ns": ts_ack,
                    "step_ack_latency_ms": (ts_ack - ts_send) / 1e6,
                    "step_ack_kind": parsed_step["ack_kind"],
                    "step_ack_rc": parsed_step["rc"],
                    "step_ack_command": parsed_step["ack_command"],
                    "stop_send_ns": te_send,
                    "stop_ack_ns": te_ack,
                    "stop_ack_latency_ms": (te_ack - te_send) / 1e6,
                    "stop_ack_kind": parsed_stop["ack_kind"],
                    "stop_ack_rc": parsed_stop["rc"],
                    "stop_ack_command": parsed_stop["ack_command"],
                    "hold_s": args.hold_s,
                    "provisional": False,
                    "notes": "E4a_command_entry_only_no_physical_speed_or_pitch_response",
                })
                time.sleep(args.inter_trial_s)
    finally:
        try:
            send_command(sock, "DRIVE,0,0")
            send_command(sock, "YAWRATE,0")
            send_command(sock, "QUEUE_STOP")
        except Exception:
            pass
        sock.close()
    return rows


def write_csv(path: str, rows: list[dict[str, object]]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_summary(path: str, rows: list[dict[str, object]]) -> None:
    case_names = sorted({str(r["case"]) for r in rows})
    summary_rows: list[dict[str, object]] = []
    for case_name in case_names:
        case_rows = [r for r in rows if r["case"] == case_name]
        step_lat = [float(r["step_ack_latency_ms"]) for r in case_rows]
        stop_lat = [float(r["stop_ack_latency_ms"]) for r in case_rows]
        summary_rows.append({
            "case": case_name,
            "n": len(case_rows),
            "step_command": case_rows[0]["step_command"],
            "step_ack_median_ms": statistics.median(step_lat),
            "step_ack_p95_ms": percentile(step_lat, 95),
            "step_ack_max_ms": max(step_lat),
            "stop_ack_median_ms": statistics.median(stop_lat),
            "stop_ack_p95_ms": percentile(stop_lat, 95),
            "stop_ack_max_ms": max(stop_lat),
            "non_ack_count": sum(1 for r in case_rows if r["step_ack_kind"] != "ACK" or r["stop_ack_kind"] != "ACK"),
            "scope": "command_entry_only",
        })
    write_csv(path, summary_rows)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="172.20.10.4")
    parser.add_argument("--port", type=int, default=23)
    parser.add_argument("--trials", type=int, default=5)
    parser.add_argument("--settle-s", type=float, default=0.2)
    parser.add_argument("--hold-s", type=float, default=0.5)
    parser.add_argument("--inter-trial-s", type=float, default=0.2)
    parser.add_argument("--out-dir", default="Report/appendices/E_data/E4_teleop_step_response")
    args = parser.parse_args()

    rows = run(args)
    raw_path = os.path.join(args.out_dir, "tcp_step_response_2026-04-24.csv")
    summary_path = os.path.join(args.out_dir, "tcp_step_response_summary_2026-04-24.csv")
    write_csv(raw_path, rows)
    write_summary(summary_path, rows)
    print(f"wrote {raw_path}")
    print(f"wrote {summary_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
