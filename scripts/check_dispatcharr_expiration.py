#!/usr/bin/env python3
"""
check_dispatcharr_expiration.py

Monitors Dispatcharr M3U accounts and profiles for upcoming subscription expirations.
Sends daily push notifications via Ntfy when an active subscription has <= 5 days remaining
or has expired.

Usage:
    uv run --with requests check_dispatcharr_expiration.py [options]

Options:
    --days <int>       Override expiration threshold in days (default: 5)
    --test             Send a test notification to verify Ntfy delivery
    --dry-run          Check and display expirations without sending notifications
    --log-file <path>  Append logs to specified file
"""

import argparse
import os
import sys
from datetime import datetime, timezone
from typing import Any

import requests


def parse_iso_datetime(dt_str: str) -> datetime | None:
    """Parses an ISO 8601 datetime string into a timezone-aware UTC datetime."""
    if not dt_str:
        return None
    try:
        # Standardize 'Z' to '+00:00' for datetime.fromisoformat
        clean_str = dt_str.replace("Z", "+00:00")
        dt = datetime.fromisoformat(clean_str)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception as exc:
        print(f"[!] Warning: Unable to parse date '{dt_str}': {exc}", file=sys.stderr)
        return None


def fetch_accounts(
    base_url: str,
    api_key: str,
    session: requests.Session | None = None,
    timeout: int = 15,
) -> list[dict[str, Any]]:
    """Fetches M3U accounts from Dispatcharr REST API."""
    url = f"{base_url.rstrip('/')}/api/m3u/accounts/"
    headers = {"X-API-Key": api_key}
    client = session or requests

    response = client.get(url, headers=headers, timeout=timeout)
    response.raise_for_status()
    data = response.json()

    if isinstance(data, list):
        return data
    if isinstance(data, dict) and "results" in data:
        return data["results"]
    return []


def parse_expirations(accounts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Extracts all active accounts and profiles that have expiration dates.
    Returns a list of dicts with keys: account_name, profile_name, exp_date.
    """
    results: list[dict[str, Any]] = []

    for acc in accounts:
        if not acc.get("is_active", True):
            continue

        acc_name = acc.get("name", "Unknown Account")
        all_expirations = acc.get("all_expirations", [])

        if all_expirations:
            for exp_info in all_expirations:
                if not exp_info.get("is_active", True):
                    continue
                exp_date_str = exp_info.get("exp_date")
                parsed_dt = parse_iso_datetime(exp_date_str)
                if parsed_dt:
                    results.append(
                        {
                            "account_name": acc_name,
                            "profile_name": exp_info.get("profile_name", "Default Profile"),
                            "exp_date": parsed_dt,
                        }
                    )
        else:
            # Fallback to top-level exp_date if all_expirations is missing
            top_exp = acc.get("exp_date") or acc.get("earliest_expiration")
            parsed_dt = parse_iso_datetime(top_exp)
            if parsed_dt:
                results.append(
                    {
                        "account_name": acc_name,
                        "profile_name": "Default",
                        "exp_date": parsed_dt,
                    }
                )

    return results


def check_expirations(
    expirations: list[dict[str, Any]],
    threshold_days: int = 5,
    now: datetime | None = None,
) -> list[dict[str, Any]]:
    """
    Identifies subscriptions that are expired or expiring within threshold_days.
    Adds 'days_remaining' and 'status' ('expired' or 'expiring_soon') to matching items.
    """
    current_time = now or datetime.now(timezone.utc)
    alerting: list[dict[str, Any]] = []

    for item in expirations:
        exp_date: datetime = item["exp_date"]
        diff = exp_date - current_time
        days_remaining = diff.total_seconds() / 86400.0

        item_copy = dict(item)
        item_copy["days_remaining"] = days_remaining

        if days_remaining < 0:
            item_copy["status"] = "expired"
            alerting.append(item_copy)
        elif days_remaining <= threshold_days:
            item_copy["status"] = "expiring_soon"
            alerting.append(item_copy)

    return alerting


def send_ntfy_notification(
    items: list[dict[str, Any]],
    ntfy_url: str,
    topic: str,
    token: str | None = None,
    is_test: bool = False,
    session: requests.Session | None = None,
    timeout: int = 15,
) -> bool:
    """Sends a notification to the configured Ntfy server and topic."""
    target_url = f"{ntfy_url.rstrip('/')}/{topic}"
    client = session or requests

    if is_test:
        title = "Dispatcharr: Expiration Checker Test"
        priority = "default"
        tags = "white_check_mark,test_tube"
        body_lines = [
            "Test notification from Dispatcharr expiration monitor.",
            "Connection to Ntfy verified successfully.",
        ]
        if items:
            body_lines.append("\nCurrent Monitored Subscriptions:")
            for it in items:
                exp_str = it["exp_date"].strftime("%b %d, %Y %H:%M UTC")
                days = it.get("days_remaining")
                days_str = f" ({days:.1f} days left)" if days is not None else ""
                body_lines.append(f"• {it['account_name']} ({it['profile_name']}): {exp_str}{days_str}")
    else:
        has_expired = any(i["status"] == "expired" for i in items)
        if has_expired:
            title = "Dispatcharr Alert: Subscription Expired!"
            priority = "urgent"
            tags = "rotating_light,x"
        else:
            title = "Dispatcharr Alert: Subscription Expiring Soon"
            priority = "high"
            tags = "warning,hourglass_flowing_sand"

        body_lines = ["The following Dispatcharr IPTV subscription(s) require attention:"]
        for it in items:
            exp_str = it["exp_date"].strftime("%b %d, %Y %H:%M UTC")
            days = it["days_remaining"]
            if it["status"] == "expired":
                desc = f"EXPIRED ({abs(days):.1f} days ago on {exp_str})"
            else:
                desc = f"{days:.1f} days remaining (Expires: {exp_str})"
            body_lines.append(f"• {it['account_name']} - {it['profile_name']}: {desc}")

        body_lines.append("\nPlease renew your subscription to maintain stream access.")

    message_body = "\n".join(body_lines)
    headers = {
        "Title": title,
        "Priority": priority,
        "Tags": tags,
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    try:
        response = client.post(
            target_url,
            data=message_body.encode("utf-8"),
            headers=headers,
            timeout=timeout,
        )
        response.raise_for_status()
        return True
    except Exception as exc:
        print(f"[!] Failed to send Ntfy notification: {exc}", file=sys.stderr)
        return False


def log_message(msg: str, log_file: str | None = None):
    """Outputs a timestamped message to stdout and optionally appends to a log file."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    formatted = f"[{timestamp}] {msg}"
    print(formatted)

    if log_file:
        try:
            os.makedirs(os.path.dirname(os.path.abspath(log_file)), exist_ok=True)
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(formatted + "\n")
        except Exception as exc:
            print(f"[!] Warning: Could not write to log file: {exc}", file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(description="Check Dispatcharr subscriptions for expiration and notify via Ntfy.")
    parser.add_argument(
        "--days",
        type=int,
        default=5,
        help="Expiration threshold in days (default: 5)",
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Send a test notification regardless of expiration date",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print status without sending any notifications",
    )
    parser.add_argument(
        "--log-file",
        type=str,
        default=None,
        help="Path to log file (default: None)",
    )

    args = parser.parse_args()

    # Load configuration from environment
    api_key = os.environ.get("DISPATCHARR_API_KEY")
    if not api_key:
        log_message("ERROR: DISPATCHARR_API_KEY environment variable is not set.", args.log_file)
        sys.exit(1)

    dispatcharr_url = os.environ.get("DISPATCHARR_URL", "http://172.19.0.15:9191")
    ntfy_url = os.environ.get("NTFY_URL", "https://ntfy.mattdies.com")
    ntfy_topic = os.environ.get("NTFY_DISPATCHARR_TOPIC", "dispatcharr-IqCDjkHMeeaNqc0v")
    ntfy_token = os.environ.get("NTFY_TOKEN")

    log_message(
        f"Checking Dispatcharr subscriptions at {dispatcharr_url} (Threshold: {args.days} days)...",
        args.log_file,
    )

    try:
        accounts = fetch_accounts(dispatcharr_url, api_key)
    except Exception as exc:
        log_message(f"ERROR: Failed to connect to Dispatcharr API: {exc}", args.log_file)
        sys.exit(1)

    expirations = parse_expirations(accounts)
    if not expirations:
        log_message("No active accounts or profiles with expiration dates found.", args.log_file)
        if args.test and not args.dry_run:
            send_ntfy_notification(
                items=[],
                ntfy_url=ntfy_url,
                topic=ntfy_topic,
                token=ntfy_token,
                is_test=True,
            )
            log_message("Sent test notification to Ntfy.", args.log_file)
        sys.exit(0)

    now = datetime.now(timezone.utc)
    alerting_items = check_expirations(expirations, threshold_days=args.days, now=now)

    for item in expirations:
        diff_days = (item["exp_date"] - now).total_seconds() / 86400.0
        exp_formatted = item["exp_date"].strftime("%Y-%m-%d %H:%M UTC")
        log_message(
            f"Account: '{item['account_name']}' ({item['profile_name']}) - Expires: {exp_formatted} ({diff_days:.1f} days left)",
            args.log_file,
        )

    if args.test:
        if args.dry_run:
            log_message("[Dry-Run] Test mode requested. Notification skipped.", args.log_file)
        else:
            log_message(f"Sending test notification to {ntfy_url}/{ntfy_topic}...", args.log_file)
            sent = send_ntfy_notification(
                items=expirations,
                ntfy_url=ntfy_url,
                topic=ntfy_topic,
                token=ntfy_token,
                is_test=True,
            )
            if sent:
                log_message("Test notification successfully sent.", args.log_file)
            else:
                log_message("Failed to send test notification.", args.log_file)
                sys.exit(1)
        sys.exit(0)

    if not alerting_items:
        log_message(
            f"All subscriptions healthy (none expiring within {args.days} days). No notification needed.",
            args.log_file,
        )
        sys.exit(0)

    log_message(f"Found {len(alerting_items)} subscription(s) needing attention.", args.log_file)

    if args.dry_run:
        log_message("[Dry-Run] Notification skipped.", args.log_file)
        sys.exit(0)

    sent = send_ntfy_notification(
        items=alerting_items,
        ntfy_url=ntfy_url,
        topic=ntfy_topic,
        token=ntfy_token,
    )
    if sent:
        log_message(f"Alert notification sent to Ntfy topic '{ntfy_topic}'.", args.log_file)
    else:
        log_message("Failed to send alert notification to Ntfy.", args.log_file)
        sys.exit(1)


if __name__ == "__main__":
    main()
