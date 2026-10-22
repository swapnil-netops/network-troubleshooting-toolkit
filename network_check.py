
import platform
import subprocess
import argparse


def check_host(host):
    """Check whether a host responds to a single ping."""
    system = platform.system().lower()

    if system == "windows":
        command = ["ping", "-n", "1", "-w", "3000", host]
    else:
        command = ["ping", "-c", "1", host]

    print(f"\nChecking connectivity to {host}...")

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=5
        )

        if result.returncode == 0:
            print(f"STATUS: Reachable - {host}")
        else:
            print(f"STATUS: No ping response from {host}")

        output = result.stdout or result.stderr
        if output:
            print("\nPing details:")
            print(output.strip())

    except subprocess.TimeoutExpired:
        print(f"STATUS: Timed out - {host}")
    except FileNotFoundError:
        print("ERROR: Ping utility was not found.")
    except OSError as error:
        print(f"ERROR: {error}")


def main():
    parser = argparse.ArgumentParser(
        description="Simple network connectivity checker"
    )
    parser.add_argument(
        "host",
        help="Hostname or IP address to test"
    )
    args = parser.parse_args()

    check_host(args.host)


if __name__ == "__main__":
    main()
