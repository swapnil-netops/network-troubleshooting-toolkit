
import argparse
import platform
import re
import subprocess
import statistics


def check_host(host, count=10):
    """Check reachability, packet loss, and latency."""

    system = platform.system().lower()

    if system == "windows":
        command = ["ping", "-n", str(count), "-w", "2000", host]
    else:
        command = ["ping", "-c", str(count), host]

    print(f"\nNetwork Check: {host}")
    print("-" * 40)
    print(f"Sending {count} ping packets...\n")

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=count * 3 + 10
        )

        output = result.stdout + "\n" + result.stderr

        # Extract packet statistics from Windows ping output.
        if system == "windows":
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
            sent = count
            received_match = re.search(
                r"(\d+)\s+(?:packets )?received", output,
                re.IGNORECASE
            )
            received = (
                int(received_match.group(1))
                if received_match else 0
            )

        # Extract successful ping response times.
        times = re.findall(r"time[=<]\s*(\d+)\s*ms", output,
                           re.IGNORECASE)
        latencies = [float(value) for value in times]

        lost = max(0, sent - received)
        loss_percent = (lost / sent * 100) if sent else 0

        print(f"Host: {host}")
        print(f"Packets sent: {sent}")
        print(f"Packets received: {received}")
        print(f"Packets lost: {lost}")
        print(f"Packet loss: {loss_percent:.1f}%")

        if latencies:
            print(f"Minimum latency: {min(latencies):.0f} ms")
            print(f"Average latency: {statistics.mean(latencies):.2f} ms")
            print(f"Maximum latency: {max(latencies):.0f} ms")
            print("Status: Reachable (ping responses received)")
        else:
            print("Latency: No measurable ping responses")
            print("Status: No ping responses received")

        print("-" * 40)

    except subprocess.TimeoutExpired:
        print("ERROR: Ping command timed out.")
    except FileNotFoundError:
        print("ERROR: Ping utility was not found.")
    except OSError as error:
        print(f"ERROR: {error}")


def main():
    parser = argparse.ArgumentParser(
        description="Network connectivity and latency checker"
    )
    parser.add_argument(
        "host",
        help="Hostname or IP address to test"
    )
    parser.add_argument(
        "-c", "--count",
        type=int,
        default=10,
        help="Number of ping packets (default: 10)"
    )

    args = parser.parse_args()

    if args.count < 1 or args.count > 1000:
        parser.error("Count must be between 1 and 1000.")

    check_host(args.host, args.count)


if __name__ == "__main__":
    main()
