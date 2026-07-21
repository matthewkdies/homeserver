"""This script checks the XposedOrNot free API for breaches for known emails.

Feel free to replace your emails in the `EMAILS` variable below if you want to
run this script yourself. I run this using `uv run --with requests <script>` as
a nightly cron job to confirm I don't have any new breaches I'm unaware of.
"""

import json
import os
import sys
import time
from pathlib import Path

import requests

EMAILS: list[str] = [
    "matthewkdies@gmail.com",
    "matthewkdies.spam@gmail.com",
    "matt.dies@yahoo.com",
]


def get_storage_file() -> Path:
    """Resolves and ensures the existence of the JSON file path."""
    docs_dir = os.environ.get("DOCUMENTS_DIR")
    if docs_dir:
        data_dir = Path(docs_dir) / "data"
    else:
        # Fallback to current working directory if DOCUMENTS_DIR isn't set
        data_dir = Path.cwd() / "data"

    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir / "breach_counts.json"


def load_previous_counts(file_path: Path) -> dict[str, int]:
    """Loads stored breach counts from JSON file."""
    if file_path.exists():
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            print(f"[!] Warning: Could not parse {file_path}. Starting fresh.")
    return {}


def save_counts(file_path: Path, counts: dict[str, int]) -> None:
    """Saves updated breach counts to JSON file."""
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(counts, f, indent=2)


def check_email_xposed(email: str) -> list[str] | None:
    """Queries XposedOrNot API for email breaches."""
    url = f"https://api.xposedornot.com/v1/check-email/{email}"
    try:
        response = requests.get(url, timeout=10)

        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "success" and "breaches" in data:
                return data["breaches"][0]
        elif response.status_code == 404:
            return []  # Clean!
        elif response.status_code == 429:
            print(f"  [!] Rate limited when checking {email}.")
            return None
        else:
            print(f"  [!] HTTP {response.status_code} checking {email}")
            return None
    except requests.RequestException as e:
        print(f"  [!] Connection error checking {email}: {e}")
        return None


def send_ntfy_notification(
    title: str,
    message: str,
    priority: str = "default",
    tags: str = "lock",
) -> bool:
    """Sends a notification to the self-hosted ntfy server."""
    topic = os.environ.get("NTFY_BREACHES_TOPIC")
    token = os.environ.get("NTFY_TOKEN")

    if not topic:
        print("  [!] Skip ntfy: NTFY_BREACHES_TOPIC environment variable is not set.")
        return False

    url = f"https://ntfy.mattdies.com/{topic}"
    headers = {
        "Title": title,
        "Priority": priority,
        "Tags": tags,
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    try:
        response = requests.post(
            url,
            data=message.encode("utf-8"),
            headers=headers,
            timeout=10,
        )
        if response.status_code == 200:
            print(f"  ✓ ntfy notification sent to topic '{topic}'.")
            return True
        else:
            print(
                f"  [!] Failed to send ntfy notification: HTTP {response.status_code}"
            )
            return False
    except requests.RequestException as e:
        print(f"  [!] Connection error sending ntfy notification: {e}")
        return False


def main():
    storage_file = get_storage_file()
    previous_counts = load_previous_counts(storage_file)
    current_counts: dict[str, int] = {}

    print(f"=== Breach Scan Started: {time.strftime('%Y-%m-%d %H:%M:%S')} ===")
    print(f"Data file: {storage_file}")

    new_breaches_detected = False

    for email in EMAILS:
        print(f"\nScanning: {email}...")
        breaches = check_email_xposed(email)

        if breaches is not None:
            count = len(breaches)
            current_counts[email] = count
            prev_count = previous_counts.get(email, 0)

            if count > prev_count:
                new_breaches_detected = True
                new_count = count - prev_count
                print(f"  ❌ ALERT: {new_count} NEW breach(es) found! Total: {count}")
                print(f"     Breaches: {', '.join(breaches)}")
            elif count > 0:
                print(
                    f"  ⚠️  Known issues: Currently in {count} breach(es) (No new ones)."
                )
            else:
                print("  ✓ Clean! No breaches found.")
        else:
            # Preserve previous count if the API request failed
            if email in previous_counts:
                current_counts[email] = previous_counts[email]

        # Respect API rate limits
        time.sleep(3)

    # Save current counts back to JSON file
    save_counts(storage_file, current_counts)

    print(f"\n=== Scan Finished: {time.strftime('%Y-%m-%d %H:%M:%S')} ===")

    # Send ntfy notification based on scan outcomes
    if new_breaches_detected:
        send_ntfy_notification(
            title="Breach Alert: New Leaks Detected!",
            message="One or more tracked email accounts were found in NEW security breaches.",
            priority="high",
            tags="warning,rotating_light",
        )
    else:
        send_ntfy_notification(
            title="Breach Check: All Clean",
            message="Nightly scan finished. No new email breaches detected.",
            priority="low",
            tags="shield",
        )

    # Exit with code 2 ONLY if new vulnerabilities were detected
    if new_breaches_detected:
        sys.exit(2)


if __name__ == "__main__":
    main()
