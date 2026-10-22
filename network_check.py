
import argparse
import platform
import re
import statistics
import subprocess


def check_host(host, count=10):
    """Check reachability, packet loss, and latency for one host."""

    is_windows = platform.system().lower() == "windows"

    if is_windows:
        command = ["ping", "-n", str(count), "-w", "2000", host]
    else:
        command = ["ping", "-c", str(count), host]

    print(f"\nChecking {host}...")

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=count * 3 + 10
        )

        output = result.stdout + "\n" + result.stderr

        if is_windows:
            sent_match = re.search(
                r"Sent\s*=\s*(\d+)", output, re.IGNORECASE
            )
            received_match = re.search(
                r"Received\s*=\s*(\d+)", output, re.IGNORECASE
            )
            sent = int(sent_match.group(1)) if sent_match else count
            received = (
                int(received_match.group(1))
                if received_match else 0
            )
        else:
            stats = re.search(
                r"(\d+)\s+packets transmitted,\s*"
                r"(\d+)\s+(?:packets )?received",
                output,
                re.IGNORECASE
            )
            sent = int(stats.group(1)) if stats else count
            received = int(stats.group(2)) if stats else 0

        # Include Windows responses such as time<1ms.
        times = re.findall(
            r"time[=<]\s*(\d+(?:\.\d+)?)\s*ms",
            output,
            re.IGNORECASE
        )
        latencies = [float(value) for value in times]

        loss = max(0, sent - received)
        loss_pct = loss / sent * 100 if sent else 0

        if received > 0:
            status = "UP"
        else:
            status = "NO PING RESPONSE"

        return {
            "host": host,
            "status": status,
            "sent": sent,
            "received": received,
            "loss": loss_pct,
            "min": min(latencies) if latencies else None,
            "avg": statistics.mean(latencies) if latencies else None,
            "max": max(latencies) if latencies else None,
        }

    except subprocess.TimeoutExpired:
        print(f"Ping command timed out for {host}.")
    except FileNotFoundError:
        print("ERROR: Ping utility was not found.")
    except OSError as error:
        print(f"ERROR checking {host}: {error}")

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


def main():
    parser = argparse.ArgumentParser(
        description="Multi-host network monitoring tool"
    )
    parser.add_argument(
        "hosts",
        nargs="+",
        help="One or more IP addresses or hostnames"
    )
    parser.add_argument(
        "-c", "--count",
        type=int,
        default=10,
        help="Ping packets per host (default: 10)"
    )

    args = parser.parse_args()

    if not 1 <= args.count <= 1000:
        parser.error("Count must be between 1 and 1000.")

    results = []

    print("=" * 72)
    print("       MULTI-HOST NETWORK MONITOR")
    print("=" * 72)

    for host in args.hosts:
        results.append(check_host(host, args.count))

    print("\n\nNETWORK MONITORING SUMMARY")
    print("=" * 72)
    print(
        f"{'HOST':<20} {'STATUS':<19} {'LOSS':>7} "
        f"{'MIN':>7} {'AVG':>7} {'MAX':>7}"
    )
    print("-" * 72)

    for item in results:
        def fmt(value):
            return f"{value:.1f}" if value is not None else "N/A"

        print(
            f"{item['host']:<20.20} "
            f"{item['status']:<19.19} "
            f"{item['loss']:>6.1f}% "
            f"{fmt(item['min']):>7} "
            f"{fmt(item['avg']):>7} "
            f"{fmt(item['max']):>7}"
        )

    print("=" * 72)
    print(f"Hosts checked: {len(results)}")
    print(f"Hosts responding: {sum(r['status'] == 'UP' for r in results)}")


if __name__ == "__main__":
    main()
