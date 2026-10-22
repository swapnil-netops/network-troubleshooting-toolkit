
import time
import argparse
import csv
import platform
import re
import subprocess
from datetime import datetime


def check_host(host, count):
    """Ping a host and calculate packet loss and latency statistics."""

    print(f"\nChecking {host}...")

    system = platform.system().lower()

    if system == "windows":
        command = ["ping", "-n", str(count), "-w", "2000", host]
    else:
        command = ["ping", "-c", str(count), "-W", "2", host]

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            errors="replace",
            timeout=count * 3 + 5
        )

        output = result.stdout + result.stderr

    except subprocess.TimeoutExpired:
        print(f"ERROR: Ping timed out for {host}")
        return {
            "host": host,
            "status": "DOWN",
            "sent": count,
            "received": 0,
            "loss": 100.0,
            "min": None,
            "avg": None,
            "max": None,
        }

    except OSError as error:
        print(f"ERROR: Unable to run ping for {host}: {error}")
        return {
            "host": host,
            "status": "ERROR",
            "sent": count,
            "received": 0,
            "loss": 100.0,
            "min": None,
            "avg": None,
            "max": None,
        }

    # Extract packet statistics.
    if system == "windows":
        sent_match = re.search(r"Sent\s*=\s*(\d+)", output, re.I)
        received_match = re.search(r"Received\s*=\s*(\d+)", output, re.I)
        loss_match = re.search(r"\((\d+(?:\.\d+)?)%\s*loss\)", output, re.I)
    else:
        sent_match = re.search(r"(\d+)\s+packets transmitted", output, re.I)
        received_match = re.search(r"(\d+)\s+(?:packets )?received", output, re.I)
        loss_match = re.search(r"([\d.]+)%\s*packet loss", output, re.I)

    sent = int(sent_match.group(1)) if sent_match else count
    received = int(received_match.group(1)) if received_match else 0

    if loss_match:
        loss = float(loss_match.group(1))
    else:
        loss = ((sent - received) / sent * 100) if sent else 100.0

    # Extract individual reply times.
    if system == "windows":
        times = re.findall(r"time[=<]\s*(\d+)\s*ms", output, re.I)
    else:
        times = re.findall(r"time[=<]\s*([\d.]+)\s*ms", output, re.I)

    latencies = [float(value) for value in times]

    if latencies:
        min_latency = min(latencies)
        avg_latency = sum(latencies) / len(latencies)
        max_latency = max(latencies)
    else:
        min_latency = None
        avg_latency = None
        max_latency = None

    status = "UP" if received > 0 else "DOWN"

    return {
        "host": host,
        "status": status,
        "sent": sent,
        "received": received,
        "loss": round(loss, 2),
        "min": round(min_latency, 2) if min_latency is not None else None,
        "avg": round(avg_latency, 2) if avg_latency is not None else None,
        "max": round(max_latency, 2) if max_latency is not None else None,
    }


def export_to_csv(results):
    """Export monitoring results to a timestamped CSV report."""

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_time = datetime.now().isoformat(timespec="seconds")
    filename = f"network_report_{timestamp}.csv"

    columns = [
        "timestamp",
        "host",
        "status",
        "packets_sent",
        "packets_received",
        "packet_loss_percent",
        "min_latency_ms",
        "avg_latency_ms",
        "max_latency_ms",
    ]

    try:
        with open(filename, "w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=columns)
            writer.writeheader()

            for item in results:
                writer.writerow({
                    "timestamp": report_time,
                    "host": item["host"],
                    "status": item["status"],
                    "packets_sent": item["sent"],
                    "packets_received": item["received"],
                    "packet_loss_percent": item["loss"],
                    "min_latency_ms": item["min"] if item["min"] is not None else "",
                    "avg_latency_ms": item["avg"] if item["avg"] is not None else "",
                    "max_latency_ms": item["max"] if item["max"] is not None else "",
                })

        print(f"\nReport exported successfully: {filename}")

    except OSError as error:
        print(f"\nERROR exporting report: {error}")



def main():
    parser = argparse.ArgumentParser(
        description="Network Troubleshooting Toolkit - Continuous Monitor"
    )

    parser.add_argument(
        "hosts",
        nargs="+",
        help="IP addresses or hostnames to monitor"
    )

    parser.add_argument(
        "-c",
        "--count",
        type=int,
        default=5,
        help="Number of ping requests per host (default: 5)"
    )

    parser.add_argument(
        "--interval",
        type=int,
        default=10,
        help="Seconds to wait between monitoring cycles (default: 10)"
    )

    args = parser.parse_args()

    if args.count < 1:
        parser.error("Ping count must be at least 1.")

    if args.interval < 1:
        parser.error("Monitoring interval must be at least 1 second.")

    print("=" * 72)
    print("NETWORK TROUBLESHOOTING TOOLKIT - VERSION 5")
    print("=" * 72)
    print(f"Hosts: {', '.join(args.hosts)}")
    print(f"Ping requests per host: {args.count}")
    print(f"Monitoring interval: {args.interval} seconds")
    print("Press Ctrl+C to stop monitoring.")

    cycle = 0

    try:
        while True:
            cycle += 1
            results = []

            print(f"\n{'=' * 72}")
            print(
                f"MONITORING CYCLE {cycle} | "
                f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
            print("=" * 72)

            for host in args.hosts:
                results.append(check_host(host, args.count))

            print("\nNETWORK MONITORING SUMMARY")
            print("-" * 80)
            print(
                f"{'HOST':<22}"
                f"{'STATUS':<10}"
                f"{'LOSS %':<12}"
                f"{'MIN MS':<12}"
                f"{'AVG MS':<12}"
                f"{'MAX MS':<12}"
            )
            print("-" * 80)

            for item in results:
                min_value = (
                    f"{item['min']:.2f}"
                    if item["min"] is not None else "N/A"
                )
                avg_value = (
                    f"{item['avg']:.2f}"
                    if item["avg"] is not None else "N/A"
                )
                max_value = (
                    f"{item['max']:.2f}"
                    if item["max"] is not None else "N/A"
                )

                print(
                    f"{item['host']:<22}"
                    f"{item['status']:<10}"
                    f"{item['loss']:<12.2f}"
                    f"{min_value:<12}"
                    f"{avg_value:<12}"
                    f"{max_value:<12}"
                )

            responding = sum(
                item["status"] == "UP" for item in results
            )

            print("-" * 80)
            print(f"Hosts checked: {len(results)}")
            print(f"Hosts responding: {responding}")
            print(f"Hosts not responding: {len(results) - responding}")

            export_to_csv(results)

            print(
                f"\nNext cycle in {args.interval} seconds..."
            )
            time.sleep(args.interval)

    except KeyboardInterrupt:
        print(f"\nMonitoring stopped. Total cycles completed: {cycle}")


if __name__ == "__main__":
    main()
